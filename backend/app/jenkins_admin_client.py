"""Read-only client for the llm-jenkins-mcp /admin/* endpoints (loopback only)."""

from __future__ import annotations

import json
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .models import ServiceDefinition

ADMIN_KEY_ENV = "JENKINS_MCP_ADMIN_KEY"
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


class JenkinsAdminError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class JenkinsAdminClient:
    """The dashboard has no Jenkins credentials: it asks the MCP, which does.

    The key is generated once per dashboard process and passed to the MCP at start
    (env ``JENKINS_MCP_ADMIN_KEY``); it is never persisted or returned by the API.
    """

    def __init__(self, *, key: str | None = None, timeout_seconds: float = 40.0):
        self.key = key or secrets.token_urlsafe(32)
        self.timeout_seconds = timeout_seconds

    def runtime_env(self) -> dict[str, str]:
        return {ADMIN_KEY_ENV: self.key}

    def _base_url(self, service: ServiceDefinition) -> str:
        control = service.control
        if control is None or not control.health_url:
            raise JenkinsAdminError("Il servizio Jenkins non ha un health_url configurato.", status_code=400)
        base_url = control.health_url.rstrip("/")
        if base_url.endswith("/health"):
            base_url = base_url[: -len("/health")]
        host = urllib.parse.urlsplit(base_url).hostname or ""
        if host not in _LOOPBACK_HOSTS:
            raise JenkinsAdminError("L'endpoint admin di Jenkins MCP deve essere su loopback.", status_code=400)
        return base_url

    def _get(self, service: ServiceDefinition, path: str) -> dict[str, Any]:
        url = f"{self._base_url(service)}/{path.lstrip('/')}"
        request = urllib.request.Request(url, method="GET", headers={"X-Admin-Key": self.key})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                body = json.loads(exc.read().decode("utf-8") or "{}")
                detail = str(body.get("error") or "") if isinstance(body, dict) else ""
            except (UnicodeDecodeError, json.JSONDecodeError, OSError):
                detail = ""
            if exc.code in (401, 404):
                raise JenkinsAdminError(
                    "Il servizio Jenkins in esecuzione non accetta la chiave della dashboard: "
                    "riavvialo dalla dashboard.",
                    status_code=409,
                ) from exc
            raise JenkinsAdminError(detail or f"Jenkins MCP ha risposto HTTP {exc.code}.", status_code=502) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise JenkinsAdminError("Jenkins MCP non raggiungibile: avvia il servizio.", status_code=409) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise JenkinsAdminError("Risposta non valida da Jenkins MCP.", status_code=502) from exc
        if not isinstance(payload, dict):
            raise JenkinsAdminError("Risposta non valida da Jenkins MCP.", status_code=502)
        return payload

    def destinations(self, service: ServiceDefinition) -> list[str]:
        payload = self._get(service, "/admin/destinations")
        choices = payload.get("choices")
        if not isinstance(choices, list) or not all(isinstance(item, str) for item in choices):
            raise JenkinsAdminError("Risposta non valida da Jenkins MCP.", status_code=502)
        return choices

    def active_policies(self, service: ServiceDefinition) -> dict[str, Any]:
        payload = self._get(service, "/admin/policies")
        demos = payload.get("demos")
        if not isinstance(payload.get("default"), str) or not isinstance(demos, dict):
            raise JenkinsAdminError("Risposta non valida da Jenkins MCP.", status_code=502)
        return {"default": payload["default"], "demos": dict(demos)}

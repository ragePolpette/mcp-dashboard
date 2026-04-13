"""Local HTTP proxy client for llm-memory admin endpoints."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .models import ServiceDefinition


class MemoryAdminProxyError(RuntimeError):
    """Raised when the llm-memory admin surface cannot be reached cleanly."""

    def __init__(self, message: str, *, status_code: int = 502):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class MemoryAdminClient:
    """Thin read-only client for llm-memory /admin/* endpoints."""

    def __init__(self, *, timeout_seconds: float = 2.0):
        self.timeout_seconds = timeout_seconds

    def _base_url(self, service: ServiceDefinition) -> str:
        control = service.control
        if control is None or not control.health_url:
            raise MemoryAdminProxyError(
                f"Service {service.service_id} does not expose a health_url for admin proxying.",
                status_code=400,
            )
        if "memory_admin" not in service.capabilities:
            raise MemoryAdminProxyError(
                f"Service {service.service_id} does not expose the memory admin surface.",
                status_code=400,
            )
        base_url = control.health_url.rstrip("/")
        if base_url.endswith("/health"):
            base_url = base_url[: -len("/health")]
        return base_url.rstrip("/")

    def _build_url(self, service: ServiceDefinition, path: str, query: dict[str, Any] | None = None) -> str:
        base_url = self._base_url(service)
        endpoint = f"{base_url}/{path.lstrip('/')}"
        params = {
            key: value
            for key, value in (query or {}).items()
            if value is not None and str(value).strip() != ""
        }
        if params:
            endpoint = f"{endpoint}?{urllib.parse.urlencode(params, doseq=True)}"
        return endpoint

    def _get_json(self, url: str) -> dict[str, Any]:
        request = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode("utf-8"))
                message = payload.get("detail") or payload.get("message") or str(exc)
            except (UnicodeDecodeError, json.JSONDecodeError):
                message = str(exc)
            raise MemoryAdminProxyError(message, status_code=exc.code) from exc
        except (urllib.error.URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MemoryAdminProxyError(f"Unable to reach llm-memory admin surface: {exc}") from exc

        if not isinstance(payload, dict):
            raise MemoryAdminProxyError("Invalid llm-memory admin response shape.")
        return payload

    def get_summary(self, service: ServiceDefinition) -> dict[str, Any]:
        return self._get_json(self._build_url(service, "/admin/summary"))

    def get_audit(self, service: ServiceDefinition, **filters: Any) -> dict[str, Any]:
        return self._get_json(self._build_url(service, "/admin/audit", filters))

    def get_projects(self, service: ServiceDefinition, **filters: Any) -> dict[str, Any]:
        return self._get_json(self._build_url(service, "/admin/projects", filters))

    def get_candidates(self, service: ServiceDefinition, **filters: Any) -> dict[str, Any]:
        return self._get_json(self._build_url(service, "/admin/fast-memory/candidates", filters))

"""Request guards for the dashboard: trusted hosts, same-origin checks and a local session token."""

from __future__ import annotations

import hmac
import json
import os
import secrets
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urlsplit

from .fs_utils import atomic_write_text

REQUESTED_WITH_HEADER = "x-requested-with"
REQUESTED_WITH_VALUE = "mcp-dashboard"
TOKEN_HEADER = "x-dashboard-token"
ALLOWED_HOSTS_ENV = "MCP_DASHBOARD_ALLOWED_HOSTS"
DEFAULT_ALLOWED_HOSTS = ("localhost", "127.0.0.1", "::1")
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})


def _strip_brackets(host: str) -> str:
    if host.startswith("[") and host.endswith("]"):
        return host[1:-1]
    return host


def split_host_port(value: str) -> tuple[str, int | None]:
    """Split a Host header value into a lowercase host name and an optional port."""
    text = (value or "").strip().lower()
    if not text:
        return "", None
    if text.startswith("["):
        end = text.find("]")
        if end < 0:
            return "", None
        host = text[1:end]
        rest = text[end + 1 :]
        if not rest:
            return host, None
        if not rest.startswith(":"):
            return "", None
        port_text = rest[1:]
    elif text.count(":") == 1:
        host, port_text = text.split(":", 1)
    elif ":" in text:
        return text, None
    else:
        return text, None
    if not port_text.isdigit():
        return "", None
    return host, int(port_text)


def allowed_hosts_from_env(raw: str | None = None) -> tuple[str, ...]:
    text = os.environ.get(ALLOWED_HOSTS_ENV, "") if raw is None else raw
    hosts = [_strip_brackets(item.strip().lower()) for item in text.split(",") if item.strip()]
    return tuple(hosts) if hosts else DEFAULT_ALLOWED_HOSTS


def _default_port(scheme: str) -> int | None:
    return {"http": 80, "https": 443, "ws": 80, "wss": 443}.get(scheme)


class SessionToken:
    """Random token generated per dashboard process and required on state-changing requests."""

    def __init__(self, value: str | None = None):
        self.value = value or secrets.token_urlsafe(32)

    def matches(self, candidate: str | None) -> bool:
        if not candidate:
            return False
        return hmac.compare_digest(candidate.encode("utf-8"), self.value.encode("utf-8"))

    def write(self, path: Path) -> None:
        atomic_write_text(Path(path), self.value, mode=0o600)

    @staticmethod
    def remove(path: Path) -> None:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass


class DashboardSecurityMiddleware:
    """ASGI middleware enforcing host allow-listing and CSRF protection for the dashboard API.

    Every HTTP request must carry a Host header from the allow-list, which also defeats
    DNS rebinding. Unsafe methods additionally need the X-Requested-With marker, the
    session token, and an Origin or Referer (when sent) matching the dashboard itself.
    """

    def __init__(self, app, *, token: SessionToken, allowed_hosts: Iterable[str] | None = None):
        self.app = app
        self.token = token
        hosts = tuple(allowed_hosts) if allowed_hosts is not None else allowed_hosts_from_env()
        self.allow_any_host = "*" in hosts
        self.allowed_hosts = frozenset(_strip_brackets(host.lower()) for host in hosts if host != "*")

    async def __call__(self, scope, receive, send):
        if scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return

        headers = {key.decode("latin-1").lower(): value.decode("latin-1") for key, value in scope.get("headers", [])}
        host_header = headers.get("host", "")
        host, _ = split_host_port(host_header)
        if not self.allow_any_host and host not in self.allowed_hosts:
            await self._reject(scope, send, 400, "invalid_host", "Invalid host header.")
            return

        method = scope.get("method", "GET").upper() if scope["type"] == "http" else "GET"
        if method not in SAFE_METHODS:
            error = self._check_unsafe_request(headers, host_header, scope.get("scheme", "http"))
            if error is not None:
                await self._reject(scope, send, 403, error[0], error[1])
                return

        await self.app(scope, receive, send)

    def _check_unsafe_request(self, headers: dict[str, str], host_header: str, scheme: str) -> tuple[str, str] | None:
        if headers.get(REQUESTED_WITH_HEADER, "").strip().lower() != REQUESTED_WITH_VALUE:
            return "csrf_header_missing", f"Missing X-Requested-With: {REQUESTED_WITH_VALUE} header."
        origin = headers.get("origin")
        if origin is not None:
            if not self._same_origin(origin, host_header, scheme):
                return "csrf_origin_rejected", "Cross-origin request rejected."
        else:
            referer = headers.get("referer")
            if referer and not self._same_origin(referer, host_header, scheme):
                return "csrf_origin_rejected", "Cross-origin request rejected."
        if not self.token.matches(headers.get(TOKEN_HEADER)):
            return "csrf_token_invalid", "Missing or invalid X-Dashboard-Token header."
        return None

    @staticmethod
    def _same_origin(url: str, host_header: str, scheme: str) -> bool:
        text = url.strip()
        if not text or text == "null":
            return False
        try:
            parts = urlsplit(text)
            origin_port = parts.port
        except ValueError:
            return False
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            return False
        if parts.scheme != {"ws": "http", "wss": "https"}.get(scheme, scheme):
            return False
        request_host, request_port = split_host_port(host_header)
        if parts.hostname.lower() != request_host:
            return False
        expected_port = request_port if request_port is not None else _default_port(scheme)
        actual_port = origin_port if origin_port is not None else _default_port(parts.scheme)
        return expected_port == actual_port

    @staticmethod
    async def _reject(scope, send, status: int, code: str, message: str) -> None:
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        body = json.dumps({"detail": message, "code": code}).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                    (b"cache-control", b"no-store"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


def client_headers(token: SessionToken) -> dict[str, str]:
    return {"X-Requested-With": REQUESTED_WITH_VALUE, "X-Dashboard-Token": token.value}


__all__ = [
    "DashboardSecurityMiddleware",
    "SessionToken",
    "allowed_hosts_from_env",
    "client_headers",
    "split_host_port",
]

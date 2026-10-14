"""Test client factory that talks to the dashboard like the bundled frontend does."""

from __future__ import annotations

from fastapi.testclient import TestClient

DASHBOARD_BASE_URL = "http://127.0.0.1:8790"


def dashboard_client(app, *, authenticated: bool = True, **kwargs) -> TestClient:
    from app import main
    from app.security import client_headers

    headers = dict(kwargs.pop("headers", {}) or {})
    if authenticated:
        headers = {**client_headers(main.session_token), **headers}
    return TestClient(app, base_url=kwargs.pop("base_url", DASHBOARD_BASE_URL), headers=headers, **kwargs)

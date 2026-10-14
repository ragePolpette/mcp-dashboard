"""Tests for host allow-listing, CSRF protection and the local session token."""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import main  # noqa: E402
from app.main import app  # noqa: E402
from app.secret_vault import DashboardSecretVault  # noqa: E402
from app.security import DashboardSecurityMiddleware, SessionToken, allowed_hosts_from_env, split_host_port  # noqa: E402
from dashboard_client import DASHBOARD_BASE_URL, dashboard_client  # noqa: E402

PASSPHRASE = "Passphrase-2026!"


@pytest.fixture
def unlocked_vault(monkeypatch, tmp_path):
    vault = DashboardSecretVault(tmp_path / "vault")
    vault.initialize(PASSPHRASE)
    monkeypatch.setattr("app.main.vault_manager", vault)
    return vault


def _raw_client(**kwargs) -> TestClient:
    return TestClient(app, base_url=kwargs.pop("base_url", DASHBOARD_BASE_URL), **kwargs)


def test_unsafe_request_without_headers_is_rejected(unlocked_vault):
    response = _raw_client().post("/api/vault/lock")

    assert response.status_code == 403
    assert response.json()["code"] == "csrf_header_missing"
    assert unlocked_vault.status()["unlocked"] is True


def test_unsafe_request_without_token_is_rejected(unlocked_vault):
    response = _raw_client(headers={"X-Requested-With": "mcp-dashboard"}).post("/api/vault/lock")

    assert response.status_code == 403
    assert response.json()["code"] == "csrf_token_invalid"
    assert unlocked_vault.status()["unlocked"] is True


def test_unsafe_request_with_wrong_token_is_rejected(unlocked_vault):
    client = _raw_client(headers={"X-Requested-With": "mcp-dashboard", "X-Dashboard-Token": "not-the-token"})

    response = client.post("/api/vault/lock")

    assert response.status_code == 403
    assert unlocked_vault.status()["unlocked"] is True


def test_unsafe_request_with_headers_and_token_is_accepted(unlocked_vault):
    response = dashboard_client(app).post("/api/vault/lock")

    assert response.status_code == 200
    assert response.json()["unlocked"] is False


@pytest.mark.parametrize(
    "header,value",
    [
        ("Origin", "http://evil.example"),
        ("Origin", "http://127.0.0.1:9999"),
        ("Origin", "https://127.0.0.1:8790"),
        ("Origin", "null"),
        ("Referer", "http://evil.example/form.html"),
    ],
)
def test_foreign_origin_is_rejected(unlocked_vault, header, value):
    response = dashboard_client(app, headers={header: value}).post("/api/vault/lock")

    assert response.status_code == 403
    assert response.json()["code"] == "csrf_origin_rejected"
    assert unlocked_vault.status()["unlocked"] is True


@pytest.mark.parametrize(
    "header,value",
    [("Origin", "http://127.0.0.1:8790"), ("Referer", "http://127.0.0.1:8790/")],
)
def test_same_origin_is_accepted(unlocked_vault, header, value):
    response = dashboard_client(app, headers={header: value}).post("/api/vault/lock")

    assert response.status_code == 200


def test_kill_all_and_vault_delete_require_the_session_token(monkeypatch, unlocked_vault):
    unlocked_vault.upsert_secret("db.dev.main", "Server=.;Database=Dev;")
    scheduled: list[float] = []
    monkeypatch.setattr("app.main._schedule_dashboard_shutdown", lambda delay_seconds=0.35: scheduled.append(delay_seconds))
    monkeypatch.setattr("app.main.registry.list_services", lambda: [])
    client = _raw_client(headers={"X-Requested-With": "mcp-dashboard"})

    assert client.post("/api/control/kill-all").status_code == 403
    assert client.delete("/api/vault/entries", params={"ref": "db.dev.main"}).status_code == 403
    assert scheduled == []
    assert unlocked_vault.status()["entry_count"] == 1


def test_simple_form_post_from_another_site_is_rejected(unlocked_vault):
    response = _raw_client().post(
        "/api/vault/lock",
        data={"x": "1"},
        headers={"Origin": "http://evil.example", "Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 403
    assert unlocked_vault.status()["unlocked"] is True


def test_untrusted_host_is_rejected_even_for_reads():
    response = _raw_client(base_url="http://evil.example").get("/health")

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_host"


@pytest.mark.parametrize("base_url", ["http://localhost:8790", "http://127.0.0.1", "http://[::1]:8790"])
def test_loopback_hosts_are_trusted(base_url):
    assert _raw_client(base_url=base_url).get("/health").status_code == 200


def test_safe_methods_do_not_need_the_token():
    assert _raw_client().get("/api/dashboard/status").status_code == 200


def test_allowed_hosts_can_be_extended_through_the_environment(monkeypatch):
    monkeypatch.setenv("MCP_DASHBOARD_ALLOWED_HOSTS", "dashboard.lan, 192.168.1.20 ,[fe80::1]")

    assert allowed_hosts_from_env() == ("dashboard.lan", "192.168.1.20", "fe80::1")


def test_allowed_hosts_default_to_loopback(monkeypatch):
    monkeypatch.delenv("MCP_DASHBOARD_ALLOWED_HOSTS", raising=False)

    assert set(allowed_hosts_from_env()) == {"localhost", "127.0.0.1", "::1"}


def test_custom_allowed_host_is_accepted_by_the_middleware():
    from fastapi import FastAPI

    token = SessionToken("fixed-token")
    lan_app = FastAPI()
    lan_app.add_middleware(DashboardSecurityMiddleware, token=token, allowed_hosts=["dashboard.lan"])

    @lan_app.post("/ping")
    def ping() -> dict[str, bool]:
        return {"ok": True}

    headers = {"X-Requested-With": "mcp-dashboard", "X-Dashboard-Token": "fixed-token"}
    assert TestClient(lan_app, base_url="http://dashboard.lan:8790", headers=headers).post("/ping").status_code == 200
    assert TestClient(lan_app, base_url="http://127.0.0.1:8790", headers=headers).post("/ping").status_code == 400


@pytest.mark.parametrize(
    "value,expected",
    [
        ("127.0.0.1:8790", ("127.0.0.1", 8790)),
        ("LOCALHOST", ("localhost", None)),
        ("[::1]:8790", ("::1", 8790)),
        ("[::1]", ("::1", None)),
        ("[::1", ("", None)),
        ("host:abc", ("", None)),
        ("", ("", None)),
    ],
)
def test_split_host_port(value, expected):
    assert split_host_port(value) == expected


def test_session_endpoint_returns_the_token_only_with_the_marker_header():
    assert _raw_client().get("/api/session").status_code == 403

    response = _raw_client(headers={"X-Requested-With": "mcp-dashboard"}).get("/api/session")

    assert response.status_code == 200
    assert response.json()["token"] == main.session_token.value
    assert response.headers["cache-control"] == "no-store"


def test_session_token_file_is_private_and_removed_on_shutdown(monkeypatch, tmp_path):
    token_file = tmp_path / "runtime" / "dashboard_session.token"
    monkeypatch.setattr("app.main.SESSION_TOKEN_FILE", token_file)
    monkeypatch.setattr("app.main.status_monitor.start", lambda: None)
    monkeypatch.setattr("app.main.pipeline.prune_old_logs", lambda *_args, **_kwargs: [])

    with _raw_client():
        assert token_file.read_text(encoding="utf-8") == main.session_token.value
        if os.name != "nt":
            assert stat.S_IMODE(token_file.stat().st_mode) == 0o600

    assert not token_file.exists()


def test_session_tokens_are_random_and_compared_safely():
    first, second = SessionToken(), SessionToken()

    assert first.value != second.value
    assert len(first.value) >= 32
    assert first.matches(first.value)
    assert not first.matches(second.value)
    assert not first.matches("")
    assert not first.matches(None)


def test_locked_vault_lists_names_without_metadata_or_usage(monkeypatch, unlocked_vault):
    unlocked_vault.upsert_secret("db.dev.main", "Server=.;Database=Dev;")
    monkeypatch.setattr(
        "app.main.options_manager.secret_ref_usage",
        lambda: {"vault://db.dev.main": [{"service_id": "llm-sql-db-mcp", "option_id": "conn"}]},
    )
    client = dashboard_client(app)

    unlocked = client.get("/api/vault").json()
    assert "updated_at" in unlocked["entries"][0]
    assert unlocked["ref_usage"]["vault://db.dev.main"]

    client.post("/api/vault/lock")
    locked = client.get("/api/vault").json()

    assert locked["entries"] == [{"ref": "vault://db.dev.main", "name": "db.dev.main"}]
    assert locked["ref_usage"] == {}


def test_vault_delete_requires_an_unlocked_vault(unlocked_vault):
    unlocked_vault.upsert_secret("db.dev.main", "Server=.;Database=Dev;")
    unlocked_vault.lock()

    response = dashboard_client(app).delete("/api/vault/entries", params={"ref": "db.dev.main"})

    assert response.status_code == 423
    assert unlocked_vault.list_entries()[0]["ref"] == "vault://db.dev.main"


def test_settings_update_applies_the_vault_auto_lock_timeout(monkeypatch, tmp_path, unlocked_vault):
    from app.dashboard_settings import DashboardSettingsManager

    monkeypatch.setattr("app.main.settings_manager", DashboardSettingsManager(tmp_path / "settings.json"))
    monkeypatch.setattr("app.main.pipeline.prune_old_logs", lambda *_args, **_kwargs: [])

    response = dashboard_client(app).post("/api/settings", json={"preferences": {"vault_auto_lock_minutes": 5}})

    assert response.status_code == 200
    assert response.json()["preferences"]["vault_auto_lock_minutes"] == 5
    assert unlocked_vault.status()["auto_lock_seconds"] == 300

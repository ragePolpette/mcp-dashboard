"""Tests for dashboard vault APIs."""

from __future__ import annotations

from pathlib import Path
import tempfile
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app  # noqa: E402
from app.secret_vault import DashboardSecretVault  # noqa: E402


def test_vault_initialize_store_lock_and_unlock(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        vault = DashboardSecretVault(Path(tmp) / "vault")
        monkeypatch.setattr("app.main.vault_manager", vault)

        client = TestClient(app)

        status_before = client.get("/api/vault")
        assert status_before.status_code == 200
        assert status_before.json()["initialized"] is False

        initialized = client.post("/api/vault/init", json={"passphrase": "Passphrase-2026!"})
        assert initialized.status_code == 200
        assert initialized.json()["initialized"] is True
        assert initialized.json()["unlocked"] is True

        saved = client.post("/api/vault/entries", json={"ref": "bitbucket.api_token", "value": "secret-value"})
        assert saved.status_code == 200
        assert saved.json()["entry"]["ref"] == "vault://bitbucket.api_token"

        locked = client.post("/api/vault/lock")
        assert locked.status_code == 200
        assert locked.json()["unlocked"] is False

        unlocked = client.post("/api/vault/unlock", json={"passphrase": "Passphrase-2026!"})
        assert unlocked.status_code == 200
        assert unlocked.json()["unlocked"] is True
        assert unlocked.json()["entry_count"] == 1


def test_vault_delete_entry(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        vault = DashboardSecretVault(Path(tmp) / "vault")
        vault.initialize("Passphrase-2026!")
        vault.upsert_secret("db.prod.connection", "Server=.;Database=Prod;")
        monkeypatch.setattr("app.main.vault_manager", vault)

        client = TestClient(app)
        response = client.delete("/api/vault/entries", params={"ref": "db.prod.connection"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["vault"]["entry_count"] == 0

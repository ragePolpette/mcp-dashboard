"""Tests for the reusable local secret vault module."""

from __future__ import annotations

import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "modules" / "local_secret_vault" / "src"))

from local_secret_vault import LocalSecretVault, LocalSecretVaultError, normalize_ref  # noqa: E402


def test_vault_initialize_unlock_store_and_resolve():
    with tempfile.TemporaryDirectory() as tmp:
        vault = LocalSecretVault(Path(tmp) / "vault")

        status = vault.initialize("Passphrase-2026!")
        assert status["initialized"] is True
        assert status["unlocked"] is True
        assert status["entry_count"] == 0

        entry = vault.upsert_secret("db.prod.connection", "Server=.;Database=Prod;")
        assert entry["ref"] == "vault://db.prod.connection"

        listed = vault.list_entries()
        assert len(listed) == 1
        assert listed[0]["name"] == "db.prod.connection"

        secret = vault.resolve_secret("vault://db.prod.connection")
        assert secret == "Server=.;Database=Prod;"


def test_vault_lock_requires_unlock_before_resolve():
    with tempfile.TemporaryDirectory() as tmp:
        vault = LocalSecretVault(Path(tmp) / "vault")
        vault.initialize("Passphrase-2026!")
        vault.upsert_secret("bitbucket.token", "secret-token")
        vault.lock()

        try:
            vault.resolve_secret("bitbucket.token")
        except LocalSecretVaultError as exc:
            assert exc.code == "E_VAULT_LOCKED"
        else:  # pragma: no cover - defensive
            raise AssertionError("Expected vault locked error.")

        status = vault.unlock("Passphrase-2026!")
        assert status["unlocked"] is True
        assert vault.resolve_secret("bitbucket.token") == "secret-token"


def test_vault_delete_removes_entry():
    with tempfile.TemporaryDirectory() as tmp:
        vault = LocalSecretVault(Path(tmp) / "vault")
        vault.initialize("Passphrase-2026!")
        vault.upsert_secret("db.dev.connection", "Server=.;Database=Dev;")
        after = vault.delete_secret("db.dev.connection")

        assert after["entry_count"] == 0
        assert vault.list_entries() == []


def test_normalize_ref_applies_scheme_and_rejects_bad_values():
    assert normalize_ref("db.prod.connection") == "vault://db.prod.connection"

    try:
        normalize_ref("bad ref with spaces")
    except LocalSecretVaultError as exc:
        assert exc.code == "E_REF_INVALID"
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected invalid ref error.")

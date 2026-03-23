"""Dashboard adapter for the reusable local secret vault module."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VAULT_MODULE_SRC = PROJECT_ROOT / "modules" / "local_secret_vault" / "src"
if str(VAULT_MODULE_SRC) not in sys.path:
    sys.path.insert(0, str(VAULT_MODULE_SRC))

from local_secret_vault import LocalSecretVault, LocalSecretVaultError, normalize_ref  # noqa: E402


class DashboardSecretVault:
    """Thin adapter that keeps dashboard imports stable."""

    def __init__(self, root_dir: Path):
        self.root_dir = Path(root_dir)
        self._vault = LocalSecretVault(self.root_dir)

    def status(self) -> dict[str, Any]:
        payload = self._vault.status()
        payload["entries"] = self._vault.list_entries() if payload["initialized"] else []
        return payload

    def initialize(self, passphrase: str) -> dict[str, Any]:
        self._vault.initialize(passphrase)
        return self.status()

    def unlock(self, passphrase: str) -> dict[str, Any]:
        self._vault.unlock(passphrase)
        return self.status()

    def lock(self) -> dict[str, Any]:
        self._vault.lock()
        return self.status()

    def list_entries(self) -> list[dict[str, Any]]:
        return self._vault.list_entries()

    def upsert_secret(self, ref: str, plaintext: str) -> dict[str, Any]:
        return self._vault.upsert_secret(ref, plaintext)

    def delete_secret(self, ref: str) -> dict[str, Any]:
        return self._vault.delete_secret(ref)

    def resolve_secret(self, ref: str) -> str:
        return self._vault.resolve_secret(ref)

    def normalize_ref(self, ref: str) -> str:
        return normalize_ref(ref)


__all__ = ["DashboardSecretVault", "LocalSecretVaultError"]

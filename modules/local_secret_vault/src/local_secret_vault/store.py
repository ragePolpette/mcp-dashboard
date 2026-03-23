"""Encrypted local secret vault store."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .crypto import create_key_envelope, decrypt_secret, encrypt_secret, unwrap_dek
from .errors import LocalSecretVaultError
from .refs import normalize_ref, ref_name


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class VaultEntry:
    ref: str
    name: str
    created_at: str
    updated_at: str


class LocalSecretVault:
    """Minimal encrypted local vault for runtime secrets."""

    def __init__(self, root_dir: Path):
        self.root_dir = Path(root_dir)
        self.store_dir = self.root_dir / "store"
        self.metadata_path = self.store_dir / "metadata.json"
        self.ciphertexts_dir = self.store_dir / "ciphertexts"
        self._dek: bytes | None = None

    def status(self) -> dict[str, Any]:
        initialized = self.metadata_path.exists()
        entries = self.list_entries() if initialized else []
        return {
            "initialized": initialized,
            "unlocked": self._dek is not None,
            "entry_count": len(entries),
        }

    def initialize(self, passphrase: str) -> dict[str, Any]:
        if self.metadata_path.exists():
            raise LocalSecretVaultError("E_ALREADY_INITIALIZED", "Secret vault is already initialized.")
        envelope, dek = create_key_envelope(passphrase)
        timestamp = _now_iso()
        metadata = {
            "version": 1,
            "key_envelope": envelope,
            "entries": [],
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        self.ciphertexts_dir.mkdir(parents=True, exist_ok=True)
        self._write_metadata(metadata)
        self._dek = dek
        return self.status()

    def lock(self) -> dict[str, Any]:
        self._dek = None
        return self.status()

    def unlock(self, passphrase: str) -> dict[str, Any]:
        metadata = self._load_metadata()
        self._dek = unwrap_dek(passphrase, metadata["key_envelope"])
        return self.status()

    def list_entries(self) -> list[dict[str, Any]]:
        metadata = self._load_metadata(optional=True)
        if metadata is None:
            return []
        entries = metadata.get("entries") or []
        return [
            {
                "ref": entry["ref"],
                "name": entry["name"],
                "created_at": entry["created_at"],
                "updated_at": entry["updated_at"],
            }
            for entry in entries
        ]

    def upsert_secret(self, ref: str, plaintext: str) -> dict[str, Any]:
        if not isinstance(plaintext, str) or not plaintext:
            raise LocalSecretVaultError("E_SECRET_INVALID", "Secret value must be provided.")
        dek = self._require_unlocked()
        metadata = self._load_metadata()
        normalized_ref = normalize_ref(ref)
        name = ref_name(normalized_ref)
        ciphertext_path = self.ciphertexts_dir / f"{name}.bin"
        ciphertext_path.parent.mkdir(parents=True, exist_ok=True)
        ciphertext_path.write_bytes(encrypt_secret(dek, plaintext, normalized_ref))

        existing = None
        entries = metadata["entries"]
        for entry in entries:
            if entry["ref"] == normalized_ref:
                existing = entry
                break
        timestamp = _now_iso()
        if existing is None:
            entries.append(
                {
                    "ref": normalized_ref,
                    "name": name,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                }
            )
        else:
            existing["updated_at"] = timestamp

        metadata["entries"] = sorted(entries, key=lambda entry: entry["ref"])
        metadata["updated_at"] = timestamp
        self._write_metadata(metadata)
        return self._entry_by_ref(metadata, normalized_ref)

    def delete_secret(self, ref: str) -> dict[str, Any]:
        metadata = self._load_metadata()
        normalized_ref = normalize_ref(ref)
        name = ref_name(normalized_ref)
        before = len(metadata["entries"])
        metadata["entries"] = [entry for entry in metadata["entries"] if entry["ref"] != normalized_ref]
        if len(metadata["entries"]) == before:
            raise LocalSecretVaultError("E_REF_UNKNOWN", "Vault reference was not found.")
        ciphertext_path = self.ciphertexts_dir / f"{name}.bin"
        if ciphertext_path.exists():
            ciphertext_path.unlink()
        metadata["updated_at"] = _now_iso()
        self._write_metadata(metadata)
        return self.status()

    def resolve_secret(self, ref: str) -> str:
        dek = self._require_unlocked()
        metadata = self._load_metadata()
        normalized_ref = normalize_ref(ref)
        self._entry_by_ref(metadata, normalized_ref)
        payload_path = self.ciphertexts_dir / f"{ref_name(normalized_ref)}.bin"
        if not payload_path.exists():
            raise LocalSecretVaultError("E_STORE_CORRUPT", "Secret ciphertext is missing.")
        return decrypt_secret(dek, payload_path.read_bytes(), normalized_ref)

    def _require_unlocked(self) -> bytes:
        if self._dek is None:
            raise LocalSecretVaultError("E_VAULT_LOCKED", "Secret vault is locked.")
        return self._dek

    def _entry_by_ref(self, metadata: dict[str, Any], normalized_ref: str) -> dict[str, Any]:
        for entry in metadata["entries"]:
            if entry["ref"] == normalized_ref:
                return {
                    "ref": entry["ref"],
                    "name": entry["name"],
                    "created_at": entry["created_at"],
                    "updated_at": entry["updated_at"],
                }
        raise LocalSecretVaultError("E_REF_UNKNOWN", "Vault reference was not found.")

    def _load_metadata(self, optional: bool = False) -> dict[str, Any] | None:
        if not self.metadata_path.exists():
            if optional:
                return None
            raise LocalSecretVaultError("E_STORE_UNINITIALIZED", "Secret vault is not initialized.")
        try:
            payload = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise LocalSecretVaultError("E_STORE_CORRUPT", "Secret vault metadata is corrupted.") from exc
        if (
            not isinstance(payload, dict)
            or payload.get("version") != 1
            or not isinstance(payload.get("key_envelope"), dict)
            or not isinstance(payload.get("entries"), list)
        ):
            raise LocalSecretVaultError("E_STORE_CORRUPT", "Secret vault metadata is invalid.")
        return payload

    def _write_metadata(self, metadata: dict[str, Any]) -> None:
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.write_text(json.dumps(metadata, ensure_ascii=True, indent=2), encoding="utf-8")


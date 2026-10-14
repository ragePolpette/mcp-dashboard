"""Encrypted local secret vault store."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .crypto import create_key_envelope, decrypt_secret, encrypt_secret, unwrap_dek
from .errors import LocalSecretVaultError
from .refs import VAULT_SCHEME, normalize_legacy_ref, normalize_ref

PRIVATE_FILE_MODE = 0o600


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_name, PRIVATE_FILE_MODE)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


@dataclass(slots=True)
class VaultEntry:
    ref: str
    name: str
    created_at: str
    updated_at: str


class LocalSecretVault:
    """Minimal encrypted local vault for runtime secrets.

    ``auto_lock_seconds`` locks the vault after that many seconds without an
    explicit vault operation (unlock, upsert, delete). Zero or None disables it.
    Resolving secrets does not count as activity, so background consumers cannot
    keep the vault unlocked forever.
    """

    def __init__(
        self,
        root_dir: Path,
        *,
        auto_lock_seconds: float | None = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.root_dir = Path(root_dir)
        self.store_dir = self.root_dir / "store"
        self.metadata_path = self.store_dir / "metadata.json"
        self.ciphertexts_dir = self.store_dir / "ciphertexts"
        self._dek: bytes | None = None
        self._lock = threading.RLock()
        self._clock = clock
        self._auto_lock_seconds = float(auto_lock_seconds or 0)
        self._last_activity = clock()

    @property
    def auto_lock_seconds(self) -> float:
        return self._auto_lock_seconds

    def set_auto_lock_seconds(self, seconds: float | None) -> None:
        with self._lock:
            self._auto_lock_seconds = max(0.0, float(seconds or 0))
            self._enforce_auto_lock_unlocked()

    def enforce_auto_lock(self) -> bool:
        """Lock the vault if the idle timeout elapsed. Returns True when it locked."""
        with self._lock:
            return self._enforce_auto_lock_unlocked()

    def status(self) -> dict[str, Any]:
        with self._lock:
            self._enforce_auto_lock_unlocked()
            initialized = self.metadata_path.exists()
            entries = self.list_entries() if initialized else []
            payload: dict[str, Any] = {
                "initialized": initialized,
                "unlocked": self._dek is not None,
                "entry_count": len(entries),
                "auto_lock_seconds": int(self._auto_lock_seconds),
                "auto_lock_in_seconds": None,
            }
            if self._dek is not None and self._auto_lock_seconds > 0:
                remaining = self._auto_lock_seconds - (self._clock() - self._last_activity)
                payload["auto_lock_in_seconds"] = max(0, int(remaining))
            return payload

    def initialize(self, passphrase: str) -> dict[str, Any]:
        with self._lock:
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
            self._touch()
            return self.status()

    def lock(self) -> dict[str, Any]:
        with self._lock:
            self._dek = None
            return self.status()

    def unlock(self, passphrase: str) -> dict[str, Any]:
        with self._lock:
            metadata = self._load_metadata()
            self._dek = unwrap_dek(passphrase, metadata["key_envelope"])
            self._touch()
            return self.status()

    def is_unlocked(self) -> bool:
        with self._lock:
            self._enforce_auto_lock_unlocked()
            return self._dek is not None

    def list_entries(self) -> list[dict[str, Any]]:
        with self._lock:
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

    def normalize_ref(self, ref: str) -> str:
        """Normalize a reference, also accepting legacy names already stored in the vault."""
        with self._lock:
            metadata = self._load_metadata(optional=True)
        return self._validated_ref(metadata, ref)

    def upsert_secret(self, ref: str, plaintext: str) -> dict[str, Any]:
        if not isinstance(plaintext, str) or not plaintext:
            raise LocalSecretVaultError("E_SECRET_INVALID", "Secret value must be provided.")
        with self._lock:
            dek = self._require_unlocked()
            metadata = self._load_metadata()
            normalized_ref = self._validated_ref(metadata, ref)
            name = normalized_ref[len(VAULT_SCHEME) :]
            ciphertext_path = self._ciphertext_path(name)
            _atomic_write_bytes(ciphertext_path, encrypt_secret(dek, plaintext, normalized_ref))

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
            self._touch()
            return self._entry_by_ref(metadata, normalized_ref)

    def delete_secret(self, ref: str) -> dict[str, Any]:
        with self._lock:
            self._require_unlocked()
            metadata = self._load_metadata()
            normalized_ref = self._validated_ref(metadata, ref)
            name = normalized_ref[len(VAULT_SCHEME) :]
            ciphertext_path = self._ciphertext_path(name)
            before = len(metadata["entries"])
            metadata["entries"] = [entry for entry in metadata["entries"] if entry["ref"] != normalized_ref]
            if len(metadata["entries"]) == before:
                raise LocalSecretVaultError("E_REF_UNKNOWN", "Vault reference was not found.")
            metadata["updated_at"] = _now_iso()
            self._write_metadata(metadata)
            ciphertext_path.unlink(missing_ok=True)
            self._touch()
            return self.status()

    def resolve_secret(self, ref: str) -> str:
        with self._lock:
            dek = self._require_unlocked()
            metadata = self._load_metadata()
            normalized_ref = self._validated_ref(metadata, ref)
            self._entry_by_ref(metadata, normalized_ref)
            payload_path = self._ciphertext_path(normalized_ref[len(VAULT_SCHEME) :])
            if not payload_path.exists():
                raise LocalSecretVaultError("E_STORE_CORRUPT", "Secret ciphertext is missing.")
            payload = payload_path.read_bytes()
        return decrypt_secret(dek, payload, normalized_ref)

    def _touch(self) -> None:
        self._last_activity = self._clock()

    def _enforce_auto_lock_unlocked(self) -> bool:
        if self._dek is None or self._auto_lock_seconds <= 0:
            return False
        if self._clock() - self._last_activity < self._auto_lock_seconds:
            return False
        self._dek = None
        return True

    def _require_unlocked(self) -> bytes:
        self._enforce_auto_lock_unlocked()
        if self._dek is None:
            raise LocalSecretVaultError("E_VAULT_LOCKED", "Secret vault is locked.")
        return self._dek

    def _validated_ref(self, metadata: dict[str, Any] | None, ref: str) -> str:
        try:
            return normalize_ref(ref)
        except LocalSecretVaultError:
            legacy_ref = normalize_legacy_ref(ref)
            known = {entry.get("ref") for entry in (metadata or {}).get("entries") or [] if isinstance(entry, dict)}
            if legacy_ref not in known:
                raise
            return legacy_ref

    def _ciphertext_path(self, name: str) -> Path:
        base = self.ciphertexts_dir.resolve()
        candidate = (self.ciphertexts_dir / f"{name}.bin").resolve()
        if candidate == base or not candidate.is_relative_to(base):
            raise LocalSecretVaultError("E_REF_INVALID", "Vault reference resolves outside the vault store.")
        return candidate

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
        _atomic_write_bytes(self.metadata_path, json.dumps(metadata, ensure_ascii=True, indent=2).encode("utf-8"))

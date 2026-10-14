"""Tests for the reusable local secret vault module."""

from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
import threading
from pathlib import Path

import pytest

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


PASSPHRASE = "Passphrase-2026!"

MALICIOUS_REFS = [
    "../outside",
    "vault://../outside",
    "a/../../outside",
    "..",
    "db..main",
    "db.main.",
    ".hidden",
    "nested/name",
    "drive:stream",
    "C:\\windows\\x",
    "/etc/passwd",
    "a\\..\\b",
    "x" * 129,
]


def _unlocked_vault(root: Path) -> LocalSecretVault:
    vault = LocalSecretVault(root / "vault")
    vault.initialize(PASSPHRASE)
    return vault


def _files_outside_store(root: Path, vault: LocalSecretVault) -> list[Path]:
    return [path for path in root.rglob("*") if path.is_file() and vault.store_dir not in path.parents]


@pytest.mark.parametrize("ref", MALICIOUS_REFS)
def test_normalize_ref_rejects_traversal_and_separators(ref):
    with pytest.raises(LocalSecretVaultError) as excinfo:
        normalize_ref(ref)
    assert excinfo.value.code == "E_REF_INVALID"


@pytest.mark.parametrize("ref", ["conn_dev", "vault://conn_dev", "db.dev.main", "vault://db.dev.main", "db-prod.main_1", "x" * 128])
def test_normalize_ref_keeps_existing_ref_styles(ref):
    name = ref.removeprefix("vault://")
    assert normalize_ref(ref) == f"vault://{name}"


@pytest.mark.parametrize("ref", MALICIOUS_REFS)
def test_malicious_refs_never_touch_files_outside_the_store(tmp_path, ref):
    vault = _unlocked_vault(tmp_path)
    (tmp_path / "outside.bin").write_bytes(b"keep")

    for operation in (
        lambda: vault.upsert_secret(ref, "value"),
        lambda: vault.resolve_secret(ref),
        lambda: vault.delete_secret(ref),
    ):
        with pytest.raises(LocalSecretVaultError):
            operation()

    assert (tmp_path / "outside.bin").read_bytes() == b"keep"
    assert _files_outside_store(tmp_path, vault) == [tmp_path / "outside.bin"]


def _inject_legacy_entry(vault: LocalSecretVault, ref: str, payload: bytes | None = None) -> None:
    metadata = json.loads(vault.metadata_path.read_text(encoding="utf-8"))
    name = ref.removeprefix("vault://")
    metadata["entries"].append({"ref": ref, "name": name, "created_at": "2026-01-01", "updated_at": "2026-01-01"})
    vault.metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    if payload is not None:
        target = vault.ciphertexts_dir / f"{name}.bin"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)


def test_legacy_refs_already_in_the_store_stay_usable(tmp_path):
    from local_secret_vault.crypto import encrypt_secret

    vault = _unlocked_vault(tmp_path)
    legacy_ref = "vault://team/bitbucket:token"
    _inject_legacy_entry(vault, legacy_ref, encrypt_secret(vault._dek, "legacy-secret", legacy_ref))

    assert vault.normalize_ref("team/bitbucket:token") == legacy_ref
    assert vault.resolve_secret(legacy_ref) == "legacy-secret"
    vault.upsert_secret(legacy_ref, "rotated")
    assert vault.resolve_secret(legacy_ref) == "rotated"
    vault.delete_secret(legacy_ref)
    assert vault.list_entries() == []

    with pytest.raises(LocalSecretVaultError):
        vault.upsert_secret("team/new:token", "value")


def test_legacy_metadata_cannot_escape_the_ciphertext_directory(tmp_path):
    vault = _unlocked_vault(tmp_path)
    victim = tmp_path / "victim.bin"
    victim.write_bytes(b"keep")
    _inject_legacy_entry(vault, "vault://x/../../../victim")
    _inject_legacy_entry(vault, "vault://ok/../../../../victim")

    for ref in ("vault://x/../../../victim", "vault://ok/../../../../victim"):
        with pytest.raises(LocalSecretVaultError):
            vault.delete_secret(ref)
        with pytest.raises(LocalSecretVaultError):
            vault.upsert_secret(ref, "overwrite")
    assert victim.read_bytes() == b"keep"


def test_delete_requires_an_unlocked_vault(tmp_path):
    vault = _unlocked_vault(tmp_path)
    vault.upsert_secret("db.dev.main", "value")
    vault.lock()

    with pytest.raises(LocalSecretVaultError) as excinfo:
        vault.delete_secret("db.dev.main")

    assert excinfo.value.code == "E_VAULT_LOCKED"
    assert [entry["ref"] for entry in vault.list_entries()] == ["vault://db.dev.main"]
    assert (vault.ciphertexts_dir / "db.dev.main.bin").exists()


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_vault_auto_locks_after_idle_timeout(tmp_path):
    clock = FakeClock()
    vault = LocalSecretVault(tmp_path / "vault", auto_lock_seconds=60, clock=clock)
    vault.initialize(PASSPHRASE)
    vault.upsert_secret("db.dev.main", "value")

    clock.now += 59
    assert vault.resolve_secret("db.dev.main") == "value"
    assert vault.status()["auto_lock_in_seconds"] == 1

    clock.now += 1
    with pytest.raises(LocalSecretVaultError) as excinfo:
        vault.resolve_secret("db.dev.main")
    assert excinfo.value.code == "E_VAULT_LOCKED"
    assert vault.status()["unlocked"] is False


def test_vault_activity_resets_the_idle_timer_and_enforce_locks(tmp_path):
    clock = FakeClock()
    vault = LocalSecretVault(tmp_path / "vault", auto_lock_seconds=60, clock=clock)
    vault.initialize(PASSPHRASE)

    clock.now += 50
    vault.upsert_secret("db.dev.main", "value")
    clock.now += 50
    assert vault.enforce_auto_lock() is False
    clock.now += 10
    assert vault.enforce_auto_lock() is True
    assert vault.is_unlocked() is False


def test_vault_auto_lock_can_be_disabled(tmp_path):
    clock = FakeClock()
    vault = LocalSecretVault(tmp_path / "vault", auto_lock_seconds=0, clock=clock)
    vault.initialize(PASSPHRASE)

    clock.now += 10 * 24 * 3600
    assert vault.enforce_auto_lock() is False
    assert vault.status()["unlocked"] is True
    assert vault.status()["auto_lock_in_seconds"] is None

    vault.set_auto_lock_seconds(30)
    assert vault.status()["unlocked"] is False


def test_failed_metadata_write_keeps_previous_metadata(tmp_path, monkeypatch):
    vault = _unlocked_vault(tmp_path)
    vault.upsert_secret("db.dev.main", "value")
    before = vault.metadata_path.read_text(encoding="utf-8")

    def broken_replace(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr("local_secret_vault.store.os.replace", broken_replace)
    with pytest.raises(OSError):
        vault.upsert_secret("db.dev.other", "value")

    assert vault.metadata_path.read_text(encoding="utf-8") == before
    assert [path.name for path in vault.store_dir.rglob("*.tmp")] == []


def test_vault_files_are_private(tmp_path):
    vault = _unlocked_vault(tmp_path)
    vault.upsert_secret("db.dev.main", "value")

    if os.name != "nt":
        assert stat.S_IMODE(vault.metadata_path.stat().st_mode) == 0o600
        assert stat.S_IMODE((vault.ciphertexts_dir / "db.dev.main.bin").stat().st_mode) == 0o600


def test_concurrent_upserts_do_not_lose_entries(tmp_path):
    vault = _unlocked_vault(tmp_path)
    errors: list[BaseException] = []

    def worker(index: int) -> None:
        try:
            vault.upsert_secret(f"svc.secret_{index}", f"value-{index}")
        except Exception as exc:  # noqa: BLE001  # pragma: no cover - surfaced through the assertion below
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(index,)) for index in range(24)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert len(vault.list_entries()) == 24
    assert vault.resolve_secret("svc.secret_7") == "value-7"

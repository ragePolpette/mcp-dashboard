"""Persisted dashboard state must be replaced atomically, never truncated in place."""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.bitbucket_repository_registry import BitbucketRepositoryRegistry  # noqa: E402
from app.dashboard_settings import DashboardSettingsManager  # noqa: E402
from app.db_target_registry import DbTargetRegistry  # noqa: E402
from app.fs_utils import atomic_write_json, atomic_write_text  # noqa: E402
from app.service_options import ServiceOptionsManager  # noqa: E402
from test_service_options import _memory_service  # noqa: E402


@pytest.fixture
def failing_replace(monkeypatch):
    def broken_replace(_src, _dst):
        raise OSError("simulated crash before rename")

    def install() -> None:
        monkeypatch.setattr("app.fs_utils.os.replace", broken_replace)

    return install


def _tmp_leftovers(directory: Path) -> list[str]:
    return sorted(path.name for path in directory.iterdir() if path.name.endswith(".tmp"))


def test_atomic_write_replaces_content_and_cleans_up(tmp_path):
    target = tmp_path / "nested" / "state.json"

    atomic_write_json(target, {"a": 1})
    atomic_write_json(target, {"a": 2})

    assert target.read_text(encoding="utf-8") == '{\n  "a": 2\n}'
    assert _tmp_leftovers(target.parent) == []


def test_atomic_write_keeps_existing_permissions_and_defaults_to_0644(tmp_path):
    if os.name == "nt":
        pytest.skip("POSIX permissions only")
    fresh = tmp_path / "fresh.json"
    atomic_write_text(fresh, "x")
    assert stat.S_IMODE(fresh.stat().st_mode) == 0o644

    private = tmp_path / "private.json"
    private.write_text("x", encoding="utf-8")
    private.chmod(0o600)
    atomic_write_text(private, "y")
    assert stat.S_IMODE(private.stat().st_mode) == 0o600


def test_dashboard_settings_survive_a_failed_write(tmp_path, failing_replace):
    path = tmp_path / "dashboard_settings.json"
    manager = DashboardSettingsManager(path)
    manager.update(services=[], preferences={"log_retention_days": 7})
    before = path.read_text(encoding="utf-8")

    failing_replace()
    with pytest.raises(OSError):
        manager.update(services=[], preferences={"log_retention_days": 9})

    assert path.read_text(encoding="utf-8") == before
    assert _tmp_leftovers(tmp_path) == []


def test_bitbucket_registry_survives_a_failed_write(tmp_path, failing_replace):
    path = tmp_path / "bitbucket_repositories.json"
    registry = BitbucketRepositoryRegistry(path)
    registry.create_repository({"id": "main", "workspace": "acme", "repo_slug": "app"})
    before = path.read_text(encoding="utf-8")

    failing_replace()
    with pytest.raises(OSError):
        registry.create_repository({"id": "other", "workspace": "acme", "repo_slug": "lib"})

    assert path.read_text(encoding="utf-8") == before
    assert _tmp_leftovers(tmp_path) == []


def test_service_options_survive_a_failed_write(tmp_path, failing_replace):
    path = tmp_path / "service_options.json"
    manager = ServiceOptionsManager(path)
    service = _memory_service()
    manager.update_options(service, {"memory_importance_strict": True})
    before = path.read_text(encoding="utf-8")

    failing_replace()
    with pytest.raises(OSError):
        manager.update_options(service, {"memory_importance_strict": False})

    assert path.read_text(encoding="utf-8") == before
    assert _tmp_leftovers(tmp_path) == []


def test_db_target_registry_survives_a_failed_write(tmp_path, failing_replace):
    state = tmp_path / "db_targets.json"
    registry = DbTargetRegistry(state, tmp_path / "runtime.json", tmp_path / "missing-bootstrap.json")
    registry.create_target({"target_id": "first"})
    before = state.read_text(encoding="utf-8")

    failing_replace()
    with pytest.raises(OSError):
        registry.create_target({"target_id": "second"})

    assert state.read_text(encoding="utf-8") == before
    assert _tmp_leftovers(tmp_path) == []

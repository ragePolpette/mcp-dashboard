"""Synthetic tests for the per-target DDL (schema change) switch; no real vault or database."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db_target_registry import DbTargetRegistry  # noqa: E402


def _registry(tmp_path: Path) -> DbTargetRegistry:
    runtime = Path(tmp_path) / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    return DbTargetRegistry(
        runtime / "db_targets.json",
        runtime / "llm_sql_db_targets.runtime.json",
        ROOT / "backend" / "config" / "db_targets.bootstrap.json",
        vault=None,
    )


def _create(registry: DbTargetRegistry, target_id: str = "alpha", **values):
    payload = {
        "target_id": target_id,
        "display_name": target_id,
        "environment": "dev",
        "status": "active",
        "connection_vault_ref": f"vault://synthetic.{target_id}",
        **values,
    }
    return registry.create_target(payload)


def _runtime_target(registry: DbTargetRegistry, target_id: str) -> dict:
    return next(t for t in registry.runtime_snapshot()["targets"] if t["target_id"] == target_id)


def test_ddl_is_off_by_default_and_db_ddl_is_not_exposed(tmp_path):
    registry = _registry(tmp_path)
    created = _create(registry)

    assert created["policy"]["ddl_enabled"] is False
    assert created["policy"]["effective_ddl_enabled"] is False
    runtime = _runtime_target(registry, "alpha")
    assert runtime["ddl_enabled"] is False
    assert "db_ddl" not in runtime["allowed_tools"]


def test_enabling_ddl_adds_db_ddl_and_exports_it_to_the_runtime_file(tmp_path):
    registry = _registry(tmp_path)
    created = _create(registry, ddl_enabled=True)

    assert created["policy"]["ddl_enabled"] is True
    assert created["policy"]["effective_ddl_enabled"] is True
    assert created["runtime"]["ddl_enabled"] is True
    assert "db_ddl" in created["allowed_tools"]
    assert "db_ddl" in created["runtime"]["allowed_tools"]
    runtime = _runtime_target(registry, "alpha")
    assert runtime["ddl_enabled"] is True
    assert "db_ddl" in runtime["allowed_tools"]


def test_turning_ddl_off_stops_exposing_db_ddl(tmp_path):
    registry = _registry(tmp_path)
    _create(registry, ddl_enabled=True)

    updated = registry.update_target("alpha", {"ddl_enabled": False})

    assert updated["policy"]["ddl_enabled"] is False
    assert updated["runtime"]["ddl_enabled"] is False
    assert "db_ddl" not in updated["runtime"]["allowed_tools"]
    runtime = _runtime_target(registry, "alpha")
    assert runtime["ddl_enabled"] is False
    assert "db_ddl" not in runtime["allowed_tools"]


def test_ddl_setting_is_per_target(tmp_path):
    registry = _registry(tmp_path)
    _create(registry, "alpha", ddl_enabled=True)
    _create(registry, "beta")

    assert _runtime_target(registry, "alpha")["ddl_enabled"] is True
    assert _runtime_target(registry, "beta")["ddl_enabled"] is False
    registry.update_target("beta", {"display_name": "Beta bis"})
    assert registry.get_target("alpha")["policy"]["ddl_enabled"] is True


def test_ddl_is_forced_off_on_prod(tmp_path):
    registry = _registry(tmp_path)
    created = _create(registry, "prodlike", environment="prod", ddl_enabled=True)

    assert created["policy"]["ddl_enabled"] is False
    runtime = _runtime_target(registry, "prodlike")
    assert runtime["ddl_enabled"] is False
    assert "db_ddl" not in runtime["allowed_tools"]


def test_ddl_is_forced_off_on_anonymized_targets(tmp_path):
    registry = _registry(tmp_path)
    created = _create(registry, ddl_enabled=True, anonymization_enabled=True, anonymization_mode="deterministic")

    assert created["policy"]["ddl_enabled"] is False
    assert _runtime_target(registry, "alpha")["ddl_enabled"] is False

    registry.update_target("alpha", {"anonymization_enabled": False, "ddl_enabled": True})
    assert _runtime_target(registry, "alpha")["ddl_enabled"] is True


def test_turning_on_anonymization_switches_ddl_off(tmp_path):
    registry = _registry(tmp_path)
    _create(registry, ddl_enabled=True)

    updated = registry.update_target("alpha", {"anonymization_enabled": True, "anonymization_mode": "deterministic"})

    assert updated["policy"]["ddl_enabled"] is False
    assert "db_ddl" not in _runtime_target(registry, "alpha")["allowed_tools"]


def test_disabled_target_never_exposes_db_ddl_or_db_write(tmp_path):
    registry = _registry(tmp_path)
    _create(registry, status="disabled", ddl_enabled=True, write_policy="allow")

    runtime = _runtime_target(registry, "alpha")
    assert runtime["ddl_enabled"] is False
    assert "db_ddl" not in runtime["allowed_tools"]
    assert "db_write" not in runtime["allowed_tools"]


def test_enabling_write_and_ddl_together_keeps_both_tools(tmp_path):
    registry = _registry(tmp_path)
    created = _create(registry, write_policy="allow", ddl_enabled=True)

    assert "db_write" in created["allowed_tools"]
    assert "db_ddl" in created["allowed_tools"]


def test_explicit_allowed_tools_are_respected_when_enabling_ddl(tmp_path):
    registry = _registry(tmp_path)
    _create(registry)

    updated = registry.update_target("alpha", {"ddl_enabled": True, "allowed_tools": ["db_read"]})

    assert updated["allowed_tools"] == ["db_read"]
    assert "db_ddl" not in updated["runtime"]["allowed_tools"]

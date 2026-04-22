"""Tests for DB target registry APIs and runtime env integration."""

from __future__ import annotations

from pathlib import Path
import tempfile
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app  # noqa: E402
from app.db_target_registry import DbTargetRegistry  # noqa: E402
from app.models import ServiceControlDefinition, ServiceDefinition, ServiceLogSource  # noqa: E402
from app.secret_vault import DashboardSecretVault  # noqa: E402


def _make_registry(tmp: str, *, with_vault: bool = False):
    runtime = Path(tmp) / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    vault = DashboardSecretVault(runtime / "vault") if with_vault else None
    if vault is not None:
        vault.initialize("Passphrase-2026!")
    registry = DbTargetRegistry(
        runtime / "db_targets.json",
        runtime / "llm_sql_db_targets.runtime.json",
        ROOT / "backend" / "config" / "db_targets.bootstrap.json",
        vault=vault,
    )
    return registry, vault


def test_db_targets_api_supports_create_update_and_disable(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        registry, _vault = _make_registry(tmp)
        monkeypatch.setattr("app.main.db_target_registry", registry)

        client = TestClient(app)

        listed = client.get("/api/db-targets")
        assert listed.status_code == 200
        assert listed.json()["count"] >= 2

        created = client.post(
            "/api/db-targets",
            json={
                "values": {
                    "target_id": "qa-reporting",
                    "display_name": "QA Reporting",
                    "environment": "qa",
                    "status": "active",
                    "connection_vault_ref": "vault://db.qa.reporting",
                    "policy": {"read_enabled": True, "write_policy": "approval_required"},
                    "anonymization": {"enabled": False, "mode": "off", "provider": "none", "model": ""},
                    "limits": {"max_rows": 150, "max_result_bytes": 90000},
                }
            },
        )
        assert created.status_code == 200
        payload = created.json()["target"]
        assert payload["target_id"] == "qa-reporting"
        assert payload["environment"] == "qa"
        assert payload["policy"]["write_policy"] == "approval_required"

        updated = client.put(
            "/api/db-targets/qa-reporting",
            json={"values": {"display_name": "QA Reporting Updated", "limits": {"max_rows": 175}}},
        )
        assert updated.status_code == 200
        updated_payload = updated.json()["target"]
        assert updated_payload["display_name"] == "QA Reporting Updated"
        assert updated_payload["limits"]["max_rows"] == 175

        disabled = client.post("/api/db-targets/qa-reporting/disable")
        assert disabled.status_code == 200
        disabled_payload = disabled.json()["target"]
        assert disabled_payload["status"] == "disabled"


def test_sql_service_start_uses_runtime_registry_env_and_vault_ref(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        registry, vault = _make_registry(tmp, with_vault=True)
        assert vault is not None
        vault.upsert_secret("db.prod.main", "Server=.;Database=Prod;")
        registry.update_target("prod-main", {"connection": {"vault_ref": "db.prod.main"}})

        service = ServiceDefinition(
            service_id="llm-sql-db-mcp",
            name="SQL Gateway",
            log_sources=[ServiceLogSource(path=Path("dummy.log"), channel="stderr")],
            control=ServiceControlDefinition(workdir=Path("."), start_command=["node", "src/server.js"]),
        )
        captured: dict[str, str] = {}

        monkeypatch.setattr("app.main.db_target_registry", registry)
        monkeypatch.setattr("app.main._service_or_404", lambda _service_id: service)
        monkeypatch.setattr("app.main.options_manager.options_env", lambda _service: {"ANON_FAIL_OPEN": "false"})
        monkeypatch.setattr("app.main.options_manager.missing_required_options", lambda _service, env_overrides=None: [])
        monkeypatch.setattr(
            "app.main.process_manager.start",
            lambda _service, env_overrides=None: captured.update(env_overrides or {}) or {"ok": True},
        )

        client = TestClient(app)
        response = client.post("/api/services/llm-sql-db-mcp/start")

        assert response.status_code == 200
        assert captured["TARGETS_FILE"].endswith("llm_sql_db_targets.runtime.json")
        assert captured["DB_PROD_MAIN_CONNECTION_STRING"] == "Server=.;Database=Prod;"
        assert captured["ANON_FAIL_OPEN"] == "false"


def test_db_target_runtime_contract_is_compatible_with_sql_mcp(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        registry, vault = _make_registry(tmp, with_vault=True)
        assert vault is not None
        vault.upsert_secret("db.prod.main", "Server=.;Database=Prod;")
        registry.update_target("prod-main", {"connection": {"vault_ref": "db.prod.main"}})

        monkeypatch.setattr("app.main.db_target_registry", registry)
        monkeypatch.setattr("app.main.process_manager.status", lambda _service: {"running": True, "pid": 4242})

        client = TestClient(app)

        runtime_response = client.get("/api/db-targets/runtime")
        assert runtime_response.status_code == 200
        runtime_payload = runtime_response.json()
        assert runtime_payload["service_id"] == "llm-sql-db-mcp"
        assert runtime_payload["apply_status"] == "restart_required"
        assert runtime_payload["snapshot"]["publisher"] == "mcp-dashboard"
        assert runtime_payload["snapshot"]["apply_strategy"] == "restart_or_start"

        prod_target = next(
            target for target in runtime_payload["snapshot"]["targets"] if target["target_id"] == "prod-main"
        )
        assert prod_target["llm_provider"] == "lmstudio"
        assert prod_target["llm_model"] == "google/gemma-3-4b"
        assert prod_target["connection_vault_ref"] == "vault://db.prod.main"
        assert prod_target["state"]["last_synced_at"]
        assert prod_target["state"]["runtime_status"] == "ready"

        sync_response = client.post("/api/db-targets/runtime/sync")
        assert sync_response.status_code == 200
        sync_payload = sync_response.json()
        assert sync_payload["ok"] is True
        assert sync_payload["apply_status"] == "restart_required"


def test_sql_mcp_service_options_expose_only_global_runtime_settings():
    client = TestClient(app)

    response = client.get("/api/services/llm-sql-db-mcp/options")

    assert response.status_code == 200
    option_ids = {item["id"] for item in response.json()["options"]}
    assert "db_dev_main_connection_string" not in option_ids
    assert "db_prod_main_connection_string" not in option_ids
    assert {"anon_hash_salt", "anon_field_identification", "anon_fail_open"} <= option_ids


def test_vault_status_includes_db_target_registry_ref_usage(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        registry, vault = _make_registry(tmp, with_vault=True)
        assert vault is not None
        vault.upsert_secret("db.prod.main", "Server=.;Database=Prod;")
        registry.update_target("prod-main", {"connection": {"vault_ref": "db.prod.main"}})

        monkeypatch.setattr("app.main.db_target_registry", registry)
        monkeypatch.setattr(
            "app.main.options_manager.secret_ref_usage",
            lambda: {"vault://service.secret": [{"service_id": "llm-memory", "option_id": "memory_secret"}]},
        )

        client = TestClient(app)
        response = client.get("/api/vault")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ref_usage"]["vault://service.secret"][0]["service_id"] == "llm-memory"
        assert payload["ref_usage"]["vault://db.prod.main"][0]["target_id"] == "prod-main"

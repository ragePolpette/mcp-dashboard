"""Tests for service options manager."""

from __future__ import annotations

from pathlib import Path
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models import (  # noqa: E402
    ServiceControlDefinition,
    ServiceDefinition,
    ServiceLogSource,
    ServiceOptionDefinition,
)
from app.secret_vault import DashboardSecretVault  # noqa: E402
from app.service_options import ServiceOptionsManager  # noqa: E402


def _memory_service() -> ServiceDefinition:
    return ServiceDefinition(
        service_id="llm-memory",
        name="LLM Memory",
        log_sources=[ServiceLogSource(path=Path("dummy.log"), channel="stderr")],
        control=ServiceControlDefinition(
            workdir=Path("."),
            start_command=["python", "-m", "src.mcp_server.http_server"],
            options=[
                ServiceOptionDefinition(
                    option_id="memory_importance_strict",
                    label="Strict",
                    kind="boolean",
                    env_var="MEMORY_IMPORTANCE_STRICT",
                    default=False,
                )
            ],
        ),
    )


def _context_service() -> ServiceDefinition:
    return ServiceDefinition(
        service_id="llm-context",
        name="LLM Context",
        log_sources=[ServiceLogSource(path=Path("dummy.log"), channel="stderr")],
        control=ServiceControlDefinition(
            workdir=Path("."),
            start_command=["python", "-u", "mcp_server_http.py"],
            options=[
                ServiceOptionDefinition(
                    option_id="llm_context_write_enabled",
                    label="Enable Context Write / Ingest",
                    kind="boolean",
                    env_var="LLM_CONTEXT_WRITE_ENABLED",
                    default=False,
                )
            ],
        ),
    )


def _db_prod_service() -> ServiceDefinition:
    return ServiceDefinition(
        service_id="llm-db-prod-mcp",
        name="DB PROD",
        log_sources=[ServiceLogSource(path=Path("dummy.log"), channel="stderr")],
        control=ServiceControlDefinition(
            workdir=Path("."),
            start_command=["node", "src/server.js"],
            options=[
                ServiceOptionDefinition(
                    option_id="db_prod_connection_string",
                    label="DB PROD Connection String",
                    kind="string",
                    env_var="DB_PROD_CONNECTION_STRING",
                    default="",
                    required=True,
                    secret=True,
                ),
                ServiceOptionDefinition(
                    option_id="anon_hash_salt",
                    label="ANON HASH SALT",
                    kind="string",
                    env_var="ANON_HASH_SALT",
                    default="",
                    secret=True,
                )
            ],
        ),
    )


def test_options_update_and_env_mapping():
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "runtime" / "service_options.json"
        manager = ServiceOptionsManager(state)
        service = _memory_service()

        opts_before = manager.list_options(service)
        assert opts_before[0]["value"] is False

        manager.update_options(service, {"memory_importance_strict": True})
        opts_after = manager.list_options(service)
        assert opts_after[0]["value"] is True

        env = manager.options_env(service)
        assert env["MEMORY_IMPORTANCE_STRICT"] == "true"


def test_context_write_toggle_maps_to_env():
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "runtime" / "service_options.json"
        manager = ServiceOptionsManager(state)
        service = _context_service()

        manager.update_options(service, {"llm_context_write_enabled": True})

        env = manager.options_env(service)
        assert env["LLM_CONTEXT_WRITE_ENABLED"] == "true"


def test_options_invalid_boolean_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "runtime" / "service_options.json"
        manager = ServiceOptionsManager(state)
        service = _memory_service()

        failed = False
        try:
            manager.update_options(service, {"memory_importance_strict": "not-a-bool"})
        except ValueError:
            failed = True

        assert failed is True


def test_secret_option_not_exposed_and_applied_to_env():
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "runtime" / "service_options.json"
        manager = ServiceOptionsManager(state)
        service = _db_prod_service()

        manager.update_options(
            service,
            {
                "db_prod_connection_string": "Server=.;Database=Prod;",
                "anon_hash_salt": "Orsa-Pietra-Faro-2026!",
            },
        )
        listed = manager.list_options(service)
        assert len(listed) == 2
        assert all(item["secret"] is True for item in listed)
        assert all(item["value"] is None for item in listed)
        assert all(item["is_set"] is True for item in listed)

        env = manager.options_env(service)
        assert env["DB_PROD_CONNECTION_STRING"] == "Server=.;Database=Prod;"
        assert env["ANON_HASH_SALT"] == "Orsa-Pietra-Faro-2026!"
        payload = state.read_text(encoding="utf-8")
        assert "db_prod_connection_string" not in payload
        assert "Server=.;Database=Prod;" not in payload
        assert "anon_hash_salt" not in payload
        assert "Orsa-Pietra-Faro-2026!" not in payload

        # empty secret update does not wipe value
        manager.update_options(service, {"db_prod_connection_string": "", "anon_hash_salt": ""})
        env_after = manager.options_env(service)
        assert env_after["DB_PROD_CONNECTION_STRING"] == "Server=.;Database=Prod;"
        assert env_after["ANON_HASH_SALT"] == "Orsa-Pietra-Faro-2026!"


def test_secret_option_is_ephemeral_across_manager_restart():
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "runtime" / "service_options.json"
        service = _db_prod_service()

        manager = ServiceOptionsManager(state)
        manager.update_options(
            service,
            {
                "db_prod_connection_string": "Server=.;Database=Prod;",
                "anon_hash_salt": "Orsa-Pietra-Faro-2026!",
            },
        )
        assert all(item["is_set"] is True for item in manager.list_options(service))

        manager_restarted = ServiceOptionsManager(state)
        listed = manager_restarted.list_options(service)
        assert all(item["is_set"] is False for item in listed)
        assert "DB_PROD_CONNECTION_STRING" not in manager_restarted.options_env(service)
        assert "ANON_HASH_SALT" not in manager_restarted.options_env(service)


def test_secret_option_can_resolve_from_vault_reference():
    with tempfile.TemporaryDirectory() as tmp:
        runtime = Path(tmp) / "runtime"
        state = runtime / "service_options.json"
        vault = DashboardSecretVault(runtime / "vault")
        vault.initialize("Passphrase-2026!")
        vault.upsert_secret("db.prod.connection", "Server=.;Database=Prod;")
        manager = ServiceOptionsManager(state, vault=vault)
        service = _db_prod_service()

        manager.update_options(
            service,
            {
                "db_prod_connection_string": {"source": "vault", "ref": "db.prod.connection"},
                "anon_hash_salt": {"source": "session", "value": "Orsa-Pietra-Faro-2026!"},
            },
        )
        listed = manager.list_options(service)
        connection = next(item for item in listed if item["id"] == "db_prod_connection_string")
        assert connection["secret_source"] == "vault"
        assert connection["vault_ref"] == "vault://db.prod.connection"
        assert connection["is_ready"] is True

        env = manager.options_env(service)
        assert env["DB_PROD_CONNECTION_STRING"] == "Server=.;Database=Prod;"
        assert env["ANON_HASH_SALT"] == "Orsa-Pietra-Faro-2026!"


def test_secret_vault_reference_survives_manager_restart_but_requires_unlock():
    with tempfile.TemporaryDirectory() as tmp:
        runtime = Path(tmp) / "runtime"
        state = runtime / "service_options.json"
        vault = DashboardSecretVault(runtime / "vault")
        vault.initialize("Passphrase-2026!")
        vault.upsert_secret("db.prod.connection", "Server=.;Database=Prod;")
        service = _db_prod_service()

        manager = ServiceOptionsManager(state, vault=vault)
        manager.update_options(service, {"db_prod_connection_string": {"source": "vault", "ref": "db.prod.connection"}})
        vault.lock()

        manager_restarted = ServiceOptionsManager(state, vault=vault)
        listed = manager_restarted.list_options(service)
        connection = next(item for item in listed if item["id"] == "db_prod_connection_string")
        assert connection["is_set"] is True
        assert connection["is_ready"] is False
        assert connection["secret_source"] == "vault"

        failed = False
        try:
            manager_restarted.options_env(service)
        except ValueError:
            failed = True
        assert failed is True


def test_missing_required_options_reports_absent_secret():
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "runtime" / "service_options.json"
        manager = ServiceOptionsManager(state)
        service = _db_prod_service()

        missing_before = manager.missing_required_options(service)
        assert missing_before == ["DB PROD Connection String"]

        manager.update_options(service, {"db_prod_connection_string": "Server=.;Database=Prod;"})
        missing_after = manager.missing_required_options(service)
        assert missing_after == []


def test_scrub_persisted_secrets_removes_existing_disk_values():
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "runtime" / "service_options.json"
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(
            '{"services":{"llm-db-prod-mcp":{"db_prod_connection_string":"Server=.;Database=Prod;","anon_hash_salt":"Orsa-Pietra-Faro-2026!"}}}',
            encoding="utf-8",
        )

        manager = ServiceOptionsManager(state)
        service = _db_prod_service()

        changed = manager.scrub_persisted_secrets([service])

        assert changed is True
        payload = state.read_text(encoding="utf-8")
        assert "db_prod_connection_string" not in payload
        assert "Server=.;Database=Prod;" not in payload
        assert "anon_hash_salt" not in payload
        assert "Orsa-Pietra-Faro-2026!" not in payload


def test_secret_ref_usage_lists_persisted_vault_bindings():
    with tempfile.TemporaryDirectory() as tmp:
        runtime = Path(tmp) / "runtime"
        state = runtime / "service_options.json"
        vault = DashboardSecretVault(runtime / "vault")
        vault.initialize("Passphrase-2026!")
        vault.upsert_secret("db.prod.connection", "Server=.;Database=Prod;")
        manager = ServiceOptionsManager(state, vault=vault)
        service = _db_prod_service()

        manager.update_options(service, {"db_prod_connection_string": {"source": "vault", "ref": "db.prod.connection"}})

        usage = manager.secret_ref_usage()
        assert usage["vault://db.prod.connection"][0] == {
            "service_id": "llm-db-prod-mcp",
            "option_id": "db_prod_connection_string",
        }

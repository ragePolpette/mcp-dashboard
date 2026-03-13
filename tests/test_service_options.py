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

        manager.update_options(service, {"db_prod_connection_string": "Server=.;Database=Prod;"})
        listed = manager.list_options(service)
        assert listed[0]["secret"] is True
        assert listed[0]["value"] is None
        assert listed[0]["is_set"] is True

        env = manager.options_env(service)
        assert env["DB_PROD_CONNECTION_STRING"] == "Server=.;Database=Prod;"
        payload = state.read_text(encoding="utf-8")
        assert "db_prod_connection_string" not in payload
        assert "Server=.;Database=Prod;" not in payload

        # empty secret update does not wipe value
        manager.update_options(service, {"db_prod_connection_string": ""})
        env_after = manager.options_env(service)
        assert env_after["DB_PROD_CONNECTION_STRING"] == "Server=.;Database=Prod;"


def test_secret_option_is_ephemeral_across_manager_restart():
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "runtime" / "service_options.json"
        service = _db_prod_service()

        manager = ServiceOptionsManager(state)
        manager.update_options(service, {"db_prod_connection_string": "Server=.;Database=Prod;"})
        assert manager.list_options(service)[0]["is_set"] is True

        manager_restarted = ServiceOptionsManager(state)
        listed = manager_restarted.list_options(service)
        assert listed[0]["is_set"] is False
        assert "DB_PROD_CONNECTION_STRING" not in manager_restarted.options_env(service)


def test_scrub_persisted_secrets_removes_existing_disk_values():
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "runtime" / "service_options.json"
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(
            '{"services":{"llm-db-prod-mcp":{"db_prod_connection_string":"Server=.;Database=Prod;"}}}',
            encoding="utf-8",
        )

        manager = ServiceOptionsManager(state)
        service = _db_prod_service()

        changed = manager.scrub_persisted_secrets([service])

        assert changed is True
        payload = state.read_text(encoding="utf-8")
        assert "db_prod_connection_string" not in payload
        assert "Server=.;Database=Prod;" not in payload

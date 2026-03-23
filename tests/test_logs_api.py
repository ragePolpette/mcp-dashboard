"""Tests for dashboard log APIs and DB query extraction."""

from __future__ import annotations

import tempfile
from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app  # noqa: E402
from app.models import ServiceControlDefinition, ServiceDefinition, ServiceLogSource  # noqa: E402
from app.log_pipeline import LogPipeline  # noqa: E402
from app.log_rules import LogRuleEngine  # noqa: E402


def test_logs_endpoint_returns_newest_first(monkeypatch):
    service = ServiceDefinition(
        service_id="svc-logs",
        name="Service Logs",
        log_sources=[ServiceLogSource(path=Path("dummy.log"), channel="stderr")],
    )
    entries = [
        {"timestamp": "2026-03-18T10:00:00+01:00", "event": "old", "message": "old"},
        {"timestamp": "2026-03-18T10:02:00+01:00", "event": "new", "message": "new"},
        {"timestamp": "2026-03-18T10:01:00+01:00", "event": "mid", "message": "mid"},
    ]

    monkeypatch.setattr("app.main._service_or_404", lambda _service_id: service)
    monkeypatch.setattr("app.main.pipeline.read_tail", lambda _service, tail=200: entries)

    client = TestClient(app)
    response = client.get("/api/services/svc-logs/logs")

    assert response.status_code == 200
    payload = response.json()
    assert [entry["event"] for entry in payload["entries"]] == ["new", "mid", "old"]


def test_services_endpoint_includes_kind_group_and_capabilities(monkeypatch):
    services = [
        ServiceDefinition(
            service_id="llm-context",
            name="LLM Context",
            kind="rag",
            group="knowledge",
            capabilities=["logs", "activity", "alerts"],
            log_sources=[ServiceLogSource(path=Path("ctx.log"), channel="stderr", tags=["runtime"])],
        )
    ]

    monkeypatch.setattr("app.main.registry.list_services", lambda: services)

    client = TestClient(app)
    response = client.get("/api/services")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == "llm-context"
    assert payload[0]["kind"] == "rag"
    assert payload[0]["group"] == "knowledge"
    assert payload[0]["capabilities"] == ["logs", "activity", "alerts"]


def test_queries_endpoint_supports_query_in_query_out(monkeypatch):
    service = ServiceDefinition(
        service_id="svc-db",
        name="Service DB",
        log_sources=[ServiceLogSource(path=Path("dummy.log"), channel="stderr")],
    )
    entries = [
        {
            "timestamp": "2026-03-18T10:00:00+01:00",
            "event": "query_in",
            "fields": {
                "tool": "db_dev_read",
                "target_id": "dev-main",
                "sql": "select * from aziende where codice = 14739",
                "parameters": {"codice": 14739},
            },
        },
        {
            "timestamp": "2026-03-18T10:00:01+01:00",
            "event": "query_out",
            "fields": {
                "tool": "db_dev_read",
                "response": {
                    "tool": "db_dev_read",
                    "target_id": "dev-main",
                    "mode": "read",
                    "rowCount": 1,
                    "truncated": False,
                },
            },
        },
    ]

    monkeypatch.setattr("app.main._service_or_404", lambda _service_id: service)
    monkeypatch.setattr("app.main.pipeline.read_tail", lambda _service, tail=2000: entries)

    client = TestClient(app)
    response = client.get("/api/services/svc-db/queries")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    query = payload["queries"][0]
    assert query["tool"] == "db_dev_read"
    assert query["target_id"] == "dev-main"
    assert query["mode"] == "read"
    assert query["row_count"] == 1
    assert query["query_full"] == "select * from aziende where codice = 14739"
    assert query["parameter_keys"] == ["codice"]


def test_activity_endpoint_supports_bitbucket_api_calls(monkeypatch):
    service = ServiceDefinition(
        service_id="llm-bitbucket-mcp",
        name="LLM Bitbucket MCP",
        log_sources=[ServiceLogSource(path=Path("dummy.log"), channel="stdout")],
    )
    entries = [
        {
            "timestamp": "2026-03-20T08:00:00+01:00",
            "event": "query_in",
            "fields": {
                "tool": "bb_api",
                "operation": "GET",
                "query_text": "/2.0/user",
                "agent_id": "codex",
            },
        },
        {
            "timestamp": "2026-03-20T08:00:01+01:00",
            "event": "query_out",
            "fields": {
                "tool": "bb_api",
                "operation": "GET",
                "agent_id": "codex",
                "success": True,
                "result_count": 1,
                "has_results": True,
            },
        },
    ]

    monkeypatch.setattr("app.main._service_or_404", lambda _service_id: service)
    monkeypatch.setattr("app.main.pipeline.read_tail", lambda _service, tail=2000: entries)

    client = TestClient(app)
    response = client.get("/api/services/llm-bitbucket-mcp/activity")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    item = payload["activity"][0]
    assert item["tool"] == "bb_api"
    assert item["kind"] == "read"
    assert item["request_text"] == "/2.0/user"
    assert "success=True" in item["response_text"]


def test_clear_logs_truncates_service_log_files(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        source_log = tmp_dir / "svc.log"
        stdout_log = tmp_dir / "svc.out.log"
        stderr_log = tmp_dir / "svc.err.log"
        for path in (source_log, stdout_log, stderr_log):
            path.write_text("line\n", encoding="utf-8")

        service = ServiceDefinition(
            service_id="svc-clear",
            name="Service Clear",
            log_sources=[ServiceLogSource(path=source_log, channel="stderr")],
            control=ServiceControlDefinition(
                workdir=tmp_dir,
                start_command=["python", "-c", "print('ok')"],
                stdout_log=stdout_log,
                stderr_log=stderr_log,
            ),
        )

        monkeypatch.setattr("app.main._service_or_404", lambda _service_id: service)

        client = TestClient(app)
        response = client.post("/api/services/svc-clear/logs/clear")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["count"] == 3
        assert source_log.read_text(encoding="utf-8") == ""
        assert stdout_log.read_text(encoding="utf-8") == ""
        assert stderr_log.read_text(encoding="utf-8") == ""


def test_db_mcp_parser_uses_embedded_timestamp_for_query_events():
    service = ServiceDefinition(
        service_id="svc-db-prod",
        name="Service DB Prod",
        log_sources=[ServiceLogSource(path=Path("dummy.log"), channel="stderr")],
        parser_chain=["json", "python", "uvicorn_access", "node_deprecation", "db_mcp_event"],
    )
    source = service.log_sources[0]
    line = (
        '[DB_PROD_MCP] 2026-03-18T14:05:56.147Z query_out '
        '{"tool":"db_prod_read_anonymized","response":{"success":true,"rowCount":20}}'
    )
    pipeline = LogPipeline(LogRuleEngine(ROOT / "backend" / "config" / "log_rules.json"))

    parsed = pipeline.parse_line(
        service=service,
        source=source,
        line=line,
        fallback_timestamp="2026-03-19T09:39:12+01:00",
    )

    assert parsed.timestamp == "2026-03-18T14:05:56.147Z"
    assert parsed.event == "query_out"
    assert parsed.logger == "DB_PROD_MCP"
    assert parsed.fields["tool"] == "db_prod_read_anonymized"


def test_db_mcp_parser_accepts_sql_gateway_logger():
    service = ServiceDefinition(
        service_id="svc-sql-gateway",
        name="Service SQL Gateway",
        log_sources=[ServiceLogSource(path=Path("dummy.log"), channel="stdout")],
        parser_chain=["json", "python", "uvicorn_access", "node_deprecation", "db_mcp_event"],
    )
    source = service.log_sources[0]
    line = (
        '[DB_SQL_MCP] 2026-03-20T10:05:56.147Z query_out '
        '{"tool":"db_read","target_id":"prod-main","rowCount":12,"response":{"success":true,"rowCount":12}}'
    )
    pipeline = LogPipeline(LogRuleEngine(ROOT / "backend" / "config" / "log_rules.json"))

    parsed = pipeline.parse_line(
        service=service,
        source=source,
        line=line,
        fallback_timestamp="2026-03-20T11:00:00+01:00",
    )

    assert parsed.timestamp == "2026-03-20T10:05:56.147Z"
    assert parsed.logger == "DB_SQL_MCP"
    assert parsed.event == "query_out"
    assert parsed.fields["target_id"] == "prod-main"
    assert parsed.fields["rowCount"] == 12


def test_mcp_activity_endpoint_builds_read_write_rows(monkeypatch):
    service = ServiceDefinition(
        service_id="llm-memory",
        name="LLM Memory",
        log_sources=[ServiceLogSource(path=Path("dummy.log"), channel="stderr")],
    )
    entries = [
        {
            "timestamp": "2026-03-19T09:57:02.827691+00:00",
            "event": "write_in",
            "fields": {
                "operation": "add",
                "agent_id": "claude-code",
                "content": "Regola bugfix...",
            },
        },
        {
            "timestamp": "2026-03-19T09:57:02.862197+00:00",
            "event": "write_out",
            "fields": {
                "operation": "add",
                "agent_id": "claude-code",
                "success": True,
                "entry_id": "abc",
            },
        },
        {
            "timestamp": "2026-03-18T13:39:23.301617+00:00",
            "event": "query_in",
            "fields": {
                "operation": "search",
                "agent_id": "claude-code",
                "query": "test connessione",
            },
        },
        {
            "timestamp": "2026-03-18T13:39:24.301617+00:00",
            "event": "query_out",
            "fields": {
                "operation": "search",
                "agent_id": "claude-code",
                "result_count": 1,
                "has_results": True,
            },
        },
    ]

    monkeypatch.setattr("app.main._service_or_404", lambda _service_id: service)
    monkeypatch.setattr("app.main.pipeline.read_tail", lambda _service, tail=2000: entries)

    client = TestClient(app)
    response = client.get("/api/services/llm-memory/activity")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert payload["activity"][0]["tool"] == "add"
    assert payload["activity"][0]["kind"] == "write"
    assert "success=True" in payload["activity"][0]["response_text"]
    assert payload["activity"][1]["tool"] == "search"
    assert payload["activity"][1]["kind"] == "read"


def test_mcp_activity_parser_reads_embedded_payload():
    service = ServiceDefinition(
        service_id="llm-context",
        name="LLM Context",
        log_sources=[ServiceLogSource(path=Path("dummy.log"), channel="stderr")],
        parser_chain=["json", "python", "uvicorn_access", "node_deprecation", "mcp_activity"],
    )
    source = service.log_sources[0]
    line = (
        '[MCP_ACTIVITY] {"timestamp":"2026-03-19T09:57:02.862197+00:00","server":"llm-memory",'
        '"event":"write_out","operation":"add","agent_id":"claude-code","success":true}'
    )
    pipeline = LogPipeline(LogRuleEngine(ROOT / "backend" / "config" / "log_rules.json"))

    parsed = pipeline.parse_line(
        service=service,
        source=source,
        line=line,
        fallback_timestamp="2026-03-19T10:00:00+01:00",
    )

    assert parsed.timestamp == "2026-03-19T09:57:02.862197+00:00"
    assert parsed.event == "write_out"
    assert parsed.logger == "MCP_ACTIVITY"
    assert parsed.fields["operation"] == "add"
    assert parsed.fields["success"] is True


def test_dashboard_status_reports_pid(monkeypatch):
    monkeypatch.setattr("app.main.os.getpid", lambda: 4242)

    client = TestClient(app)
    response = client.get("/api/dashboard/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["pid"] == 4242


def test_kill_all_stops_services_and_schedules_dashboard_shutdown(monkeypatch):
    services = [
        ServiceDefinition(
            service_id="llm-context",
            name="LLM Context",
            log_sources=[ServiceLogSource(path=Path("ctx.log"), channel="stderr")],
            control=ServiceControlDefinition(workdir=Path("."), start_command=["python", "-m", "ctx"]),
        ),
        ServiceDefinition(
            service_id="mcp-dashboard",
            name="MCP Dashboard",
            log_sources=[ServiceLogSource(path=Path("dash.log"), channel="stderr")],
            control=ServiceControlDefinition(workdir=Path("."), start_command=["python", "-m", "dash"]),
        ),
    ]
    stopped: list[str] = []
    scheduled: list[float] = []

    monkeypatch.setattr("app.main.registry.list_services", lambda: services)
    monkeypatch.setattr(
        "app.main.process_manager.stop",
        lambda service: stopped.append(service.service_id) or {"ok": True, "result": "stopped"},
    )
    monkeypatch.setattr("app.main._schedule_dashboard_shutdown", lambda delay_seconds=0.35: scheduled.append(delay_seconds))
    monkeypatch.setattr("app.main.os.getpid", lambda: 9001)

    client = TestClient(app)
    response = client.post("/api/control/kill-all")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["dashboard_pid"] == 9001
    assert stopped == ["llm-context"]
    assert scheduled == [0.35]


def test_settings_endpoint_returns_preferences_and_visibility(monkeypatch):
    services = [
        ServiceDefinition(
            service_id="llm-context",
            name="LLM Context",
            kind="rag",
            group="knowledge",
            log_sources=[ServiceLogSource(path=Path("ctx.log"), channel="stderr")],
            control=ServiceControlDefinition(workdir=Path("."), start_command=["python", "-m", "ctx"], port=8765),
        ),
    ]

    monkeypatch.setattr("app.main.registry.list_services", lambda: services)
    monkeypatch.setattr(
        "app.main.settings_manager.snapshot",
        lambda _services: {
            "preferences": {
                "refresh_interval_sec": 10,
                "show_stopped_services": False,
                "default_advanced_tab": "logs",
                "service_order": "group",
                "show_alerts_in_home": False,
                "log_retention_days": 21,
                "recent_rows_limit": 80,
            },
            "service_visibility": {"llm-context": False},
        },
    )

    client = TestClient(app)
    response = client.get("/api/settings")

    assert response.status_code == 200
    payload = response.json()
    assert payload["preferences"]["refresh_interval_sec"] == 10
    assert payload["service_visibility"]["llm-context"] is False
    assert payload["services"][0]["visible"] is False
    assert payload["services"][0]["port"] == 8765


def test_settings_update_stops_newly_hidden_services_and_prunes_logs(monkeypatch):
    services = [
        ServiceDefinition(
            service_id="llm-context",
            name="LLM Context",
            log_sources=[ServiceLogSource(path=Path("ctx.log"), channel="stderr")],
            control=ServiceControlDefinition(workdir=Path("."), start_command=["python", "-m", "ctx"]),
        ),
        ServiceDefinition(
            service_id="llm-memory",
            name="LLM Memory",
            log_sources=[ServiceLogSource(path=Path("mem.log"), channel="stderr")],
            control=ServiceControlDefinition(workdir=Path("."), start_command=["python", "-m", "mem"]),
        ),
    ]
    stopped: list[str] = []

    monkeypatch.setattr("app.main.registry.list_services", lambda: services)
    monkeypatch.setattr(
        "app.main.settings_manager.snapshot",
        lambda _services: {
            "preferences": {
                "refresh_interval_sec": 5,
                "show_stopped_services": True,
                "default_advanced_tab": "automatic",
                "service_order": "manual",
                "show_alerts_in_home": True,
                "log_retention_days": 15,
                "recent_rows_limit": 30,
            },
            "service_visibility": {"llm-context": True, "llm-memory": True},
        },
    )
    monkeypatch.setattr(
        "app.main.settings_manager.update",
        lambda **kwargs: {
            "preferences": {
                "refresh_interval_sec": 10,
                "show_stopped_services": False,
                "default_advanced_tab": "logs",
                "service_order": "status",
                "show_alerts_in_home": False,
                "log_retention_days": 21,
                "recent_rows_limit": 80,
            },
            "service_visibility": {"llm-context": False, "llm-memory": True},
        },
    )
    monkeypatch.setattr(
        "app.main.process_manager.stop",
        lambda service: stopped.append(service.service_id) or {"ok": True, "result": "stopped"},
    )
    monkeypatch.setattr("app.main.pipeline.prune_old_logs", lambda _services, retention_days=15: ["ctx.log"])

    client = TestClient(app)
    response = client.post(
        "/api/settings",
        json={
            "preferences": {"refresh_interval_sec": 10},
            "service_visibility": {"llm-context": False},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert stopped == ["llm-context"]
    assert payload["pruned_logs"] == ["ctx.log"]

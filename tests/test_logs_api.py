"""Tests for dashboard log APIs and DB query extraction."""

from __future__ import annotations

import tempfile
from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app  # noqa: E402
from app.memory_admin_client import MemoryAdminProxyError  # noqa: E402
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


def test_memory_admin_summary_proxy_returns_downstream_payload(monkeypatch):
    service = ServiceDefinition(
        service_id="llm-memory",
        name="LLM Memory",
        kind="memory",
        group="knowledge",
        capabilities=["logs", "activity", "memory_admin"],
        log_sources=[ServiceLogSource(path=Path("mem.log"), channel="stderr")],
        control=ServiceControlDefinition(
            workdir=Path("."),
            start_command=["python", "-m", "mem"],
            health_url="http://127.0.0.1:8767/health",
        ),
    )

    monkeypatch.setattr("app.main._memory_admin_service_or_400", lambda _service_id: service)
    monkeypatch.setattr(
        "app.main.memory_admin_client.get_summary",
        lambda _service: {"status": "ok", "summary": {"counts": {"active_entries": 3}}},
    )

    client = TestClient(app)
    response = client.get("/api/services/llm-memory/memory-admin/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["summary"]["counts"]["active_entries"] == 3


def test_memory_admin_audit_proxy_forwards_filters(monkeypatch):
    service = ServiceDefinition(
        service_id="llm-memory",
        name="LLM Memory",
        capabilities=["memory_admin"],
        log_sources=[ServiceLogSource(path=Path("mem.log"), channel="stderr")],
        control=ServiceControlDefinition(
            workdir=Path("."),
            start_command=["python", "-m", "mem"],
            health_url="http://127.0.0.1:8767/health",
        ),
    )
    captured: dict[str, object] = {}

    def fake_get_audit(_service, **filters):
        captured.update(filters)
        return {"status": "ok", "audit": {"count": 1, "items": [{"action": "export"}]}}

    monkeypatch.setattr("app.main._memory_admin_service_or_400", lambda _service_id: service)
    monkeypatch.setattr("app.main.memory_admin_client.get_audit", fake_get_audit)

    client = TestClient(app)
    response = client.get(
        "/api/services/llm-memory/memory-admin/audit"
        "?limit=25&action=export&actor=agent-a&reason=manual&since=2026-03-26T10:00:00Z"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["audit"]["count"] == 1
    assert captured == {
        "limit": 25,
        "entry_id": None,
        "action": "export",
        "actor": "agent-a",
        "reason": "manual",
        "since": "2026-03-26T10:00:00Z",
    }


def test_memory_admin_projects_proxy_maps_proxy_errors(monkeypatch):
    service = ServiceDefinition(
        service_id="llm-memory",
        name="LLM Memory",
        capabilities=["memory_admin"],
        log_sources=[ServiceLogSource(path=Path("mem.log"), channel="stderr")],
        control=ServiceControlDefinition(
            workdir=Path("."),
            start_command=["python", "-m", "mem"],
            health_url="http://127.0.0.1:8767/health",
        ),
    )

    monkeypatch.setattr("app.main._memory_admin_service_or_400", lambda _service_id: service)
    monkeypatch.setattr(
        "app.main.memory_admin_client.get_projects",
        lambda _service, **_filters: (_ for _ in ()).throw(
            MemoryAdminProxyError("Unable to reach llm-memory admin surface", status_code=502)
        ),
    )

    client = TestClient(app)
    response = client.get("/api/services/llm-memory/memory-admin/projects?limit=20")

    assert response.status_code == 502
    assert response.json()["detail"] == "Unable to reach llm-memory admin surface"


def test_memory_admin_candidates_proxy_forwards_filters(monkeypatch):
    service = ServiceDefinition(
        service_id="llm-memory",
        name="LLM Memory",
        capabilities=["memory_admin"],
        log_sources=[ServiceLogSource(path=Path("mem.log"), channel="stderr")],
        control=ServiceControlDefinition(
            workdir=Path("."),
            start_command=["python", "-m", "mem"],
            health_url="http://127.0.0.1:8767/health",
        ),
    )
    captured: dict[str, object] = {}

    def fake_get_candidates(_service, **filters):
        captured.update(filters)
        return {
            "status": "ok",
            "candidates": {
                "count": 1,
                "items": [{"cluster_id": "cluster-menu", "candidate_score": 0.83}],
            },
        }

    monkeypatch.setattr("app.main._memory_admin_service_or_400", lambda _service_id: service)
    monkeypatch.setattr("app.main.memory_admin_client.get_candidates", fake_get_candidates)

    client = TestClient(app)
    response = client.get(
        "/api/services/llm-memory/memory-admin/candidates"
        "?limit=15&workspace_id=ws-a&project_id=prj-a&include_resolved=true&distillation_status=pending"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["candidates"]["count"] == 1
    assert captured == {
        "limit": 15,
        "workspace_id": "ws-a",
        "project_id": "prj-a",
        "include_resolved": True,
        "distillation_status": "pending",
    }


def test_memory_admin_candidates_proxy_maps_proxy_errors(monkeypatch):
    service = ServiceDefinition(
        service_id="llm-memory",
        name="LLM Memory",
        capabilities=["memory_admin"],
        log_sources=[ServiceLogSource(path=Path("mem.log"), channel="stderr")],
        control=ServiceControlDefinition(
            workdir=Path("."),
            start_command=["python", "-m", "mem"],
            health_url="http://127.0.0.1:8767/health",
        ),
    )

    monkeypatch.setattr("app.main._memory_admin_service_or_400", lambda _service_id: service)
    monkeypatch.setattr(
        "app.main.memory_admin_client.get_candidates",
        lambda _service, **_filters: (_ for _ in ()).throw(
            MemoryAdminProxyError("Candidate queue unavailable", status_code=502)
        ),
    )

    client = TestClient(app)
    response = client.get("/api/services/llm-memory/memory-admin/candidates?limit=10")

    assert response.status_code == 502
    assert response.json()["detail"] == "Candidate queue unavailable"


def test_memory_admin_distillation_runs_proxy_forwards_filters(monkeypatch):
    service = ServiceDefinition(
        service_id="llm-memory",
        name="LLM Memory",
        capabilities=["memory_admin"],
        log_sources=[ServiceLogSource(path=Path("mem.log"), channel="stderr")],
        control=ServiceControlDefinition(
            workdir=Path("."),
            start_command=["python", "-m", "mem"],
            health_url="http://127.0.0.1:8767/health",
        ),
    )
    captured: dict[str, object] = {}

    def fake_get_runs(_service, **filters):
        captured.update(filters)
        return {
            "status": "ok",
            "runs": {
                "count": 1,
                "items": [{"id": "run-1", "status": "prepared"}],
            },
        }

    monkeypatch.setattr("app.main._memory_admin_service_or_400", lambda _service_id: service)
    monkeypatch.setattr("app.main.memory_admin_client.get_distillation_runs", fake_get_runs)

    client = TestClient(app)
    response = client.get(
        "/api/services/llm-memory/memory-admin/distillation/runs"
        "?limit=25&workspace_id=ws-a&project_id=prj-a&agent_id=agent-a&status=reviewed"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["runs"]["count"] == 1
    assert captured == {
        "limit": 25,
        "workspace_id": "ws-a",
        "project_id": "prj-a",
        "agent_id": "agent-a",
        "status": "reviewed",
    }


def test_memory_admin_distillation_run_proxy_returns_detail(monkeypatch):
    service = ServiceDefinition(
        service_id="llm-memory",
        name="LLM Memory",
        capabilities=["memory_admin"],
        log_sources=[ServiceLogSource(path=Path("mem.log"), channel="stderr")],
        control=ServiceControlDefinition(
            workdir=Path("."),
            start_command=["python", "-m", "mem"],
            health_url="http://127.0.0.1:8767/health",
        ),
    )

    monkeypatch.setattr("app.main._memory_admin_service_or_400", lambda _service_id: service)
    monkeypatch.setattr(
        "app.main.memory_admin_client.get_distillation_run",
        lambda _service, run_id: {"status": "ok", "run": {"id": run_id, "status": "applied"}},
    )

    client = TestClient(app)
    response = client.get("/api/services/llm-memory/memory-admin/distillation/runs/run-42")

    assert response.status_code == 200
    payload = response.json()
    assert payload["run"]["id"] == "run-42"
    assert payload["run"]["status"] == "applied"



def test_memory_admin_prepare_distillation_proxy_forwards_payload(monkeypatch):
    service = ServiceDefinition(
        service_id="llm-memory",
        name="LLM Memory",
        capabilities=["memory_admin"],
        log_sources=[ServiceLogSource(path=Path("mem.log"), channel="stderr")],
        control=ServiceControlDefinition(
            workdir=Path("."),
            start_command=["python", "-m", "mem"],
            health_url="http://127.0.0.1:8767/health",
        ),
    )
    captured: dict[str, object] = {}

    def fake_prepare(_service, payload):
        captured.update(payload)
        return {"status": "ok", "distillation_prepare": {"prepared_count": 1}}

    monkeypatch.setattr("app.main._memory_admin_service_or_400", lambda _service_id: service)
    monkeypatch.setattr("app.main.memory_admin_client.prepare_distillation", fake_prepare)

    client = TestClient(app)
    response = client.post(
        "/api/services/llm-memory/memory-admin/distillation/prepare",
        json={
            "agent_id": "dashboard-operator",
            "workspace_id": "ws-a",
            "project_id": "prj-a",
            "reason": "prepare candidate from dashboard",
            "cluster_id": "cluster-menu",
            "top_k": 1,
            "include_resolved": False,
            "distillation_status": "pending",
        },
    )

    assert response.status_code == 200
    assert response.json()["distillation_prepare"]["prepared_count"] == 1
    assert captured["cluster_id"] == "cluster-menu"
    assert captured["agent_id"] == "dashboard-operator"


def test_memory_admin_apply_distillation_proxy_forwards_run_id(monkeypatch):
    service = ServiceDefinition(
        service_id="llm-memory",
        name="LLM Memory",
        capabilities=["memory_admin"],
        log_sources=[ServiceLogSource(path=Path("mem.log"), channel="stderr")],
        control=ServiceControlDefinition(
            workdir=Path("."),
            start_command=["python", "-m", "mem"],
            health_url="http://127.0.0.1:8767/health",
        ),
    )
    captured: dict[str, object] = {}

    def fake_apply(_service, payload):
        captured.update(payload)
        return {"status": "ok", "distillation_apply": {"success": True, "count": 1, "run_id": payload.get("run_id")}}

    monkeypatch.setattr("app.main._memory_admin_service_or_400", lambda _service_id: service)
    monkeypatch.setattr("app.main.memory_admin_client.apply_distillation", fake_apply)

    client = TestClient(app)
    response = client.post(
        "/api/services/llm-memory/memory-admin/distillation/apply",
        json={
            "agent_id": "dashboard-operator",
            "workspace_id": "ws-a",
            "project_id": "prj-a",
            "reason": "preview apply from dashboard",
            "run_id": "run-42",
            "dry_run": True,
            "payload": {"decisions": []},
        },
    )

    assert response.status_code == 200
    assert response.json()["distillation_apply"]["run_id"] == "run-42"
    assert captured["run_id"] == "run-42"



def test_memory_admin_apply_distillation_proxy_maps_proxy_errors(monkeypatch):
    service = ServiceDefinition(
        service_id="llm-memory",
        name="LLM Memory",
        capabilities=["memory_admin"],
        log_sources=[ServiceLogSource(path=Path("mem.log"), channel="stderr")],
        control=ServiceControlDefinition(
            workdir=Path("."),
            start_command=["python", "-m", "mem"],
            health_url="http://127.0.0.1:8767/health",
        ),
    )

    monkeypatch.setattr("app.main._memory_admin_service_or_400", lambda _service_id: service)
    monkeypatch.setattr(
        "app.main.memory_admin_client.apply_distillation",
        lambda _service, _payload: (_ for _ in ()).throw(
            MemoryAdminProxyError("Distillation apply blocked", status_code=403)
        ),
    )

    client = TestClient(app)
    response = client.post(
        "/api/services/llm-memory/memory-admin/distillation/apply",
        json={
            "agent_id": "dashboard-operator",
            "workspace_id": "ws-a",
            "project_id": "prj-a",
            "reason": "preview apply from dashboard",
            "dry_run": True,
            "payload": {"decisions": []},
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Distillation apply blocked"


def test_dashboard_overview_returns_runtime_logs_metrics_and_alerts(monkeypatch):
    services = [
        ServiceDefinition(
            service_id="svc-overview",
            name="Overview Service",
            capabilities=["logs", "alerts"],
            log_sources=[ServiceLogSource(path=Path("overview.log"), channel="stdout")],
        )
    ]
    entries = [
        {
            "timestamp": "2026-03-23T10:00:00+01:00",
            "event": "query_out",
            "level": "INFO",
            "message": "done",
            "fields": {"tool": "db_read", "response": {"rowCount": 1, "truncated": False}},
        }
    ]
    monkeypatch.setattr("app.main.registry.list_services", lambda: services)
    monkeypatch.setattr(
        "app.main.settings_manager.snapshot",
        lambda _services: {"preferences": {}, "service_visibility": {"svc-overview": True}},
    )
    monkeypatch.setattr("app.main.pipeline.read_tail", lambda _service, tail=2000: entries)
    monkeypatch.setattr(
        "app.main.process_manager.status",
        lambda _service: {"running": True, "health_ok": True, "pid": 1234, "port": 9999},
    )
    monkeypatch.setattr(
        "app.main.alert_engine.evaluate",
        lambda **_kwargs: {"status": "ok", "triggered_count": 0, "triggered": []},
    )

    client = TestClient(app)
    response = client.get("/api/dashboard/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["pid"]
    assert payload["service_count"] == 1
    assert payload["service_visibility"]["svc-overview"] is True
    item = payload["services"][0]
    assert item["service_id"] == "svc-overview"
    assert item["runtime"]["running"] is True
    assert item["entries"][0]["event"] == "query_out"
    assert item["metrics"]["db_queries_count"] == 1
    assert item["alerts"]["status"] == "ok"


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

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
    assert query["mode"] == "read"
    assert query["row_count"] == 1
    assert query["query_full"] == "select * from aziende where codice = 14739"
    assert query["parameter_keys"] == ["codice"]


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

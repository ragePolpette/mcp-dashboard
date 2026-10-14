"""Log pruning, clearing, filtering and streaming must cooperate with running services."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import log_pipeline as log_pipeline_module  # noqa: E402
from app.log_pipeline import LogPipeline, compact_log_file, truncate_log_file  # noqa: E402
from app.log_rules import LogRuleEngine  # noqa: E402
from app.main import _apply_log_filters, app  # noqa: E402
from app.models import ServiceControlDefinition, ServiceDefinition, ServiceLogSource  # noqa: E402
from dashboard_client import dashboard_client  # noqa: E402

OLD_LINE = '[DB_DEV_MCP] 2026-02-20T10:00:00.000Z query_in {"tool":"db_dev_read","sql":"select 1"}'
NEW_LINE = '[DB_DEV_MCP] 2026-03-19T09:00:00.000Z query_out {"tool":"db_dev_read","response":{"rowCount":1}}'


def _pipeline(tmp_path: Path) -> LogPipeline:
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(json.dumps({"rule_sets": {"default": []}}), encoding="utf-8")
    return LogPipeline(LogRuleEngine(rules_path))


def _service(log_path: Path) -> ServiceDefinition:
    return ServiceDefinition(
        service_id="llm-db-dev-mcp",
        name="LLM DB DEV MCP",
        log_sources=[ServiceLogSource(path=log_path, channel="stdout")],
        parser_chain=["json", "python", "uvicorn_access", "node_deprecation", "db_mcp_event"],
        rule_sets=[],
    )


def test_prune_rewrites_in_place_while_a_child_keeps_appending(tmp_path):
    log_path = tmp_path / "db.log"
    log_path.write_text(f"{OLD_LINE}\nstack line old\n{NEW_LINE}\nstack line new\n", encoding="utf-8")
    inode_before = log_path.stat().st_ino
    pipeline = _pipeline(tmp_path)

    with log_path.open("a", encoding="utf-8") as child_stdout:
        pruned = pipeline.prune_old_logs(
            [_service(log_path)],
            retention_days=15,
            now=datetime(2026, 3, 25, tzinfo=UTC),
        )
        child_stdout.write("written after prune\n")

    assert pruned == [str(log_path.resolve())]
    assert log_path.stat().st_ino == inode_before
    assert log_path.read_text(encoding="utf-8") == f"{NEW_LINE}\nstack line new\nwritten after prune\n"


def test_prune_streams_the_file_instead_of_loading_it(tmp_path, monkeypatch):
    log_path = tmp_path / "db.log"
    log_path.write_text(f"{OLD_LINE}\n{NEW_LINE}\n", encoding="utf-8")
    pipeline = _pipeline(tmp_path)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("prune must not read the whole log into memory")

    monkeypatch.setattr(Path, "read_text", forbidden)

    pruned = pipeline.prune_old_logs(
        [_service(log_path)],
        retention_days=15,
        now=datetime(2026, 3, 25, tzinfo=UTC),
    )

    assert pruned == [str(log_path.resolve())]
    assert log_path.read_bytes() == f"{NEW_LINE}\n".encode()


def test_compact_log_file_keeps_line_endings_and_reports_changes(tmp_path):
    path = tmp_path / "x.log"
    path.write_bytes(b"keep-1\r\ndrop-1\nkeep-2\ndrop-2\nkeep-3")

    assert compact_log_file(path, lambda line: line.startswith("keep")) is True
    assert path.read_bytes() == b"keep-1\r\nkeep-2\nkeep-3"
    assert compact_log_file(path, lambda line: True) is False
    assert path.read_bytes() == b"keep-1\r\nkeep-2\nkeep-3"


def test_truncate_log_file_keeps_inode_and_creates_missing_files(tmp_path):
    existing = tmp_path / "out.log"
    existing.write_text("old content\n", encoding="utf-8")
    inode_before = existing.stat().st_ino

    with existing.open("a", encoding="utf-8") as child_stdout:
        truncate_log_file(existing)
        child_stdout.write("fresh\n")

    assert existing.stat().st_ino == inode_before
    assert existing.read_text(encoding="utf-8") == "fresh\n"

    missing = tmp_path / "nested" / "err.log"
    truncate_log_file(missing)
    assert missing.read_bytes() == b""


def test_clear_logs_endpoint_truncates_in_place(monkeypatch, tmp_path):
    log_path = tmp_path / "svc.log"
    stdout_log = tmp_path / "svc.out.log"
    log_path.write_text("a\n", encoding="utf-8")
    stdout_log.write_text("b\n", encoding="utf-8")
    service = ServiceDefinition(
        service_id="svc-clear",
        name="svc",
        log_sources=[ServiceLogSource(path=log_path, channel="stderr")],
        control=ServiceControlDefinition(
            workdir=tmp_path,
            start_command=["python"],
            stdout_log=stdout_log,
        ),
    )
    truncated: list[Path] = []
    monkeypatch.setattr("app.main.registry.get", lambda service_id: service if service_id == "svc-clear" else None)
    monkeypatch.setattr("app.main.truncate_log_file", lambda path: truncated.append(path))

    response = dashboard_client(app).post("/api/services/svc-clear/logs/clear")

    assert response.status_code == 200
    assert truncated == [log_path, stdout_log]


def test_text_filter_matches_values_not_json_keys():
    entries = [
        {"level": "INFO", "message": "plain", "fields": {}},
        {"level": "INFO", "message": "perché no", "fields": {}},
        {"level": "INFO", "message": "x", "fields": {"tool": "db_read", "nested": {"target": "Prod-Main"}}},
        {"level": "INFO", "message": "y", "row_count": 42, "fields": None},
    ]

    assert _apply_log_filters(entries, text="level") == []
    assert _apply_log_filters(entries, text="PERCHÉ") == [entries[1]]
    assert _apply_log_filters(entries, text="prod-main") == [entries[2]]
    assert _apply_log_filters(entries, text="42") == [entries[3]]


def test_stream_entries_reads_files_off_the_event_loop(tmp_path, monkeypatch):
    log_path = tmp_path / "stream.log"
    log_path.write_text("before\n", encoding="utf-8")
    pipeline = _pipeline(tmp_path)
    service = _service(log_path)
    offloaded: list[str] = []
    real_to_thread = asyncio.to_thread

    async def recording_to_thread(func, *args, **kwargs):
        offloaded.append(getattr(func, "__name__", repr(func)))
        return await real_to_thread(func, *args, **kwargs)

    monkeypatch.setattr(log_pipeline_module.asyncio, "to_thread", recording_to_thread)

    async def scenario() -> list[str]:
        stream = pipeline.stream_entries(service, poll_seconds=0.01)
        pending = asyncio.ensure_future(stream.__anext__())
        await asyncio.sleep(0.05)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write("first line\npartial")
        first = await asyncio.wait_for(pending, timeout=2)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(" completed\n")
        second = await asyncio.wait_for(stream.__anext__(), timeout=2)
        await stream.aclose()
        return [first["raw"], second["raw"]]

    assert asyncio.run(scenario()) == ["first line", "partial completed"]
    assert offloaded and all(name == "_read_new_lines" for name in offloaded)


@pytest.mark.parametrize("payload", [b"", b"no newline yet"])
def test_stream_waits_for_complete_lines(tmp_path, payload):
    log_path = tmp_path / "s.log"
    log_path.write_bytes(b"")
    pipeline = _pipeline(tmp_path)
    service = _service(log_path)
    offsets = {str(log_path): 0}
    log_path.write_bytes(payload)

    assert pipeline._read_new_lines(service, offsets) == []
    assert offsets[str(log_path)] == 0

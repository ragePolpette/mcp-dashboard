"""Query log and DB metrics for the unified llm-sql-db-mcp log format (db.query_out, db.query_failed, db.query_in)."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import _build_query_records, _compute_metrics  # noqa: E402

HASH_A = "aaaaaaaaaaaaaaaa"
HASH_B = "bbbbbbbbbbbbbbbb"


def _entry(event: str, payload: dict, ts: str, level: str = "INFO") -> dict:
    """An entry as the JSON log parser produces it: the server's `payload` stays nested under fields."""
    return {
        "event": event,
        "level": level,
        "timestamp": ts,
        "source_path": "llm-sql-db-mcp.out.log",
        "fields": {"payload": payload, "request_id": "req-1", "session_id": "sess-1"},
    }


def _out(ts: str, **payload) -> dict:
    base = {"tool": "db_read", "target_id": "dev-main", "row_count": 1, "rows_affected": None, "truncated": False,
            "anonymization_applied": False, "anonymization_provider": "none", "anonymization_mode": "off"}
    return _entry("db.query_out", {**base, **payload}, ts)


def test_info_level_query_out_becomes_a_query_record_without_sql_text():
    records = _build_query_records([_out("2026-11-16T10:00:00.000Z", sql_hash=HASH_A, row_count=3, truncated=True)])

    assert len(records) == 1
    record = records[0]
    assert record["tool"] == "db_read"
    assert record["target_id"] == "dev-main"
    assert record["row_count"] == 3
    assert record["result_truncated"] is True
    assert record["timestamp"] == "2026-11-16T10:00:00.000Z"
    assert record["sql_hash"] == HASH_A
    assert HASH_A in record["query_preview"]
    assert not record.get("query_full")
    assert record["status"] == "ok"


def test_query_out_without_hash_still_shows_a_record():
    records = _build_query_records([_out("2026-11-16T10:00:00.000Z")])

    assert len(records) == 1
    assert records[0]["row_count"] == 1
    assert records[0]["query_preview"]


def test_debug_query_in_is_paired_with_query_out_by_hash_even_when_interleaved():
    entries = [
        _entry("db.query_in", {"tool": "db_read", "target_id": "dev-main", "sql_hash": HASH_A,
                               "sql_preview": "SELECT a FROM dbo.A", "parameter_keys": ["id"]}, "2026-11-16T10:00:00.000Z", "DEBUG"),
        _entry("db.query_in", {"tool": "db_read", "target_id": "dev-main", "sql_hash": HASH_B,
                               "sql_preview": "SELECT b FROM dbo.B", "parameter_keys": []}, "2026-11-16T10:00:00.100Z", "DEBUG"),
        _out("2026-11-16T10:00:00.200Z", sql_hash=HASH_B, row_count=2),
        _out("2026-11-16T10:00:00.300Z", sql_hash=HASH_A, row_count=5),
    ]

    by_hash = {record["sql_hash"]: record for record in _build_query_records(entries)}

    assert by_hash[HASH_A]["query_preview"] == "SELECT a FROM dbo.A"
    assert by_hash[HASH_A]["row_count"] == 5
    assert by_hash[HASH_A]["parameter_keys"] == ["id"]
    assert by_hash[HASH_B]["query_preview"] == "SELECT b FROM dbo.B"
    assert by_hash[HASH_B]["row_count"] == 2


def test_failed_query_is_listed_with_its_error():
    entry = _entry("db.query_failed", {"tool": "db_write", "target_id": "dev-main", "sql_hash": HASH_A,
                                       "error": "Invalid object name 'dbo.Missing'."}, "2026-11-16T10:01:00.000Z")

    records = _build_query_records([entry])

    assert len(records) == 1
    record = records[0]
    assert record["status"] == "failed"
    assert record["tool"] == "db_write"
    assert record["row_count"] is None
    assert record["error"] == "Invalid object name 'dbo.Missing'."
    assert "Invalid object name" in record["query_preview"]


def test_failed_query_keeps_the_preview_of_its_query_in():
    entries = [
        _entry("db.query_in", {"tool": "db_read", "target_id": "dev-main", "sql_hash": HASH_A,
                               "sql_preview": "SELECT x FROM dbo.Nope"}, "2026-11-16T10:00:00.000Z", "DEBUG"),
        _entry("db.query_failed", {"tool": "db_read", "target_id": "dev-main", "sql_hash": HASH_A, "error": "boom"},
               "2026-11-16T10:00:00.050Z"),
    ]

    record = _build_query_records(entries)[0]

    assert "SELECT x FROM dbo.Nope" in record["query_preview"]
    assert "boom" in record["query_preview"]


def test_anonymized_results_are_labelled_in_the_mode_column():
    records = _build_query_records([_out("2026-11-16T10:00:00.000Z", anonymization_applied=True, anonymization_mode="deterministic")])

    assert records[0]["mode"] == "anon:deterministic"


def test_records_are_newest_first_and_other_events_are_ignored():
    entries = [
        _out("2026-11-16T10:00:00.000Z", sql_hash=HASH_A),
        _entry("db.anonymizer_decisions", {"tool": "db_read", "target_id": "prod-main"}, "2026-11-16T10:00:00.500Z"),
        _entry("server.started", {"port": 18784}, "2026-11-16T10:00:01.000Z"),
        _out("2026-11-16T10:00:02.000Z", sql_hash=HASH_B),
    ]

    records = _build_query_records(entries)

    assert [record["sql_hash"] for record in records] == [HASH_B, HASH_A]


def test_legacy_query_in_and_query_out_events_still_work():
    entries = [
        {"event": "query_in", "level": "INFO", "timestamp": "2026-11-16T10:00:00Z", "source_path": "legacy.log",
         "fields": {"tool": "db_dev_read", "target_id": "dev", "sql": "SELECT 1", "parameters": {"id": 1}}},
        {"event": "query_out", "level": "INFO", "timestamp": "2026-11-16T10:00:01Z", "source_path": "legacy.log",
         "fields": {"tool": "db_dev_read", "response": {"rowCount": 7, "truncated": False}}},
    ]

    records = _build_query_records(entries)

    assert len(records) == 1
    assert records[0]["query_full"] == "SELECT 1"
    assert records[0]["row_count"] == 7
    assert records[0]["parameter_keys"] == ["id"]


def test_db_metrics_count_unified_query_out_events():
    now = datetime.now(timezone.utc)
    stamp = lambda seconds: (now - timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")  # noqa: E731
    entries = [
        _out(stamp(30), row_count=2),
        _out(stamp(20), row_count=4),
        _entry("db.query_failed", {"tool": "db_read", "target_id": "dev-main", "error": "boom"}, stamp(10)),
    ]

    metrics = _compute_metrics(entries)

    assert metrics["db_queries_count"] == 2
    assert metrics["db_avg_row_count"] == 3

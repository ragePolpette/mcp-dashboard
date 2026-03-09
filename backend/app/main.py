"""FastAPI app for MCP dashboard logs and control plane."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .alert_engine import AlertEngine
from .log_pipeline import LogPipeline
from .log_rules import LogRuleEngine
from .process_manager import ServiceProcessManager
from .service_options import ServiceOptionsManager
from .services_registry import ServiceRegistry

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "backend" / "config"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
RUNTIME_DIR = PROJECT_ROOT / "runtime"

SERVICES_CONFIG = CONFIG_DIR / "services.json"
RULES_CONFIG = CONFIG_DIR / "log_rules.json"
ALERTS_CONFIG = CONFIG_DIR / "alerts.json"
OPTIONS_STATE = RUNTIME_DIR / "service_options.json"

registry = ServiceRegistry(SERVICES_CONFIG)
rule_engine = LogRuleEngine(RULES_CONFIG)
pipeline = LogPipeline(rule_engine)
alert_engine = AlertEngine(ALERTS_CONFIG)
process_manager = ServiceProcessManager()
options_manager = ServiceOptionsManager(OPTIONS_STATE)

app = FastAPI(title="MCP Dashboard", version="0.3.0")
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")


class OptionUpdatePayload(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)


def _service_or_404(service_id: str):
    service = registry.get(service_id)
    if service is None:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service_id}")
    return service


def _parse_entry_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _apply_log_filters(
    entries: list[dict[str, Any]],
    *,
    level: str | None = None,
    event: str | None = None,
    text: str | None = None,
) -> list[dict[str, Any]]:
    requested_level = (level or "").strip().upper()
    requested_event = (event or "").strip()
    requested_text = (text or "").strip().lower()
    out: list[dict[str, Any]] = []

    for entry in entries:
        entry_level = str(entry.get("level") or "").upper()
        entry_event = str(entry.get("event") or "")
        if requested_level and entry_level != requested_level:
            continue
        if requested_event and entry_event != requested_event:
            continue
        if requested_text:
            haystack = json.dumps(entry, ensure_ascii=True).lower()
            if requested_text not in haystack:
                continue
        out.append(entry)
    return out


def _compute_metrics(entries: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now().astimezone()
    one_minute_ago = now - timedelta(minutes=1)
    today = now.date()

    total = len(entries)
    errors = 0
    requests_per_minute = 0
    db_row_counts: list[float] = []
    db_row_count_series: list[float] = []
    memory_saved_today = 0
    memory_retrieved_today = 0
    context_retrieved_today = 0
    activity_buckets = [0 for _ in range(12)]
    context_retrieval_buckets = [0 for _ in range(12)]
    activity_bucket_labels: list[str] = []
    for i in range(12):
        bucket_time = now - timedelta(minutes=(11 - i))
        activity_bucket_labels.append(bucket_time.strftime("%H:%M"))

    for entry in entries:
        level = str(entry.get("level") or "").upper()
        if level in {"ERROR", "CRITICAL"}:
            errors += 1

        event = str(entry.get("event") or "")
        fields = entry.get("fields") or {}

        parsed_ts = _parse_entry_timestamp(entry.get("timestamp"))
        if parsed_ts is not None:
            if parsed_ts.tzinfo is None:
                parsed_ts = parsed_ts.replace(tzinfo=now.tzinfo)
            parsed_local = parsed_ts.astimezone(now.tzinfo)
            if parsed_local >= one_minute_ago:
                requests_per_minute += 1
            minute_delta = int((now - parsed_local).total_seconds() // 60)
            if 0 <= minute_delta <= 11:
                activity_buckets[11 - minute_delta] += 1
                if event == "context.retrieved":
                    context_retrieval_buckets[11 - minute_delta] += 1
            if parsed_local.date() == today:
                if event == "memory.saved":
                    memory_saved_today += 1
                elif event == "memory.retrieved":
                    memory_retrieved_today += 1
                elif event == "context.retrieved":
                    context_retrieved_today += 1

        if event == "db.query.executed":
            row_count_raw = fields.get("row_count")
            try:
                row_count_value = float(row_count_raw)
                db_row_counts.append(row_count_value)
                db_row_count_series.append(row_count_value)
            except (TypeError, ValueError):
                pass

    avg_row_count = (sum(db_row_counts) / len(db_row_counts)) if db_row_counts else None
    error_rate = (errors / total) if total > 0 else 0.0

    return {
        "window_entries": total,
        "requests_per_minute": requests_per_minute,
        "error_rate": error_rate,
        "errors": errors,
        "db_avg_row_count": avg_row_count,
        "db_queries_count": len(db_row_counts),
        "db_row_count_series": db_row_count_series[-24:],
        "memory_saved_today": memory_saved_today,
        "memory_retrieved_today": memory_retrieved_today,
        "context_retrieved_today": context_retrieved_today,
        "activity_series": activity_buckets,
        "context_retrieval_series": context_retrieval_buckets,
        "activity_labels": activity_bucket_labels,
        "computed_at": datetime.now().isoformat(),
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    html_path = FRONTEND_DIR / "index.html"
    return html_path.read_text(encoding="utf-8")


@app.get("/api/services")
def list_services() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for service in registry.list_services():
        control = None
        if service.control is not None:
            control = {
                "enabled": True,
                "host": service.control.host,
                "port": service.control.port,
                "health_url": service.control.health_url,
                "startup_timeout_sec": service.control.startup_timeout_sec,
                "options_count": len(service.control.options),
            }
        out.append(
            {
                "id": service.service_id,
                "name": service.name,
                "log_sources": [
                    {"path": str(src.path), "channel": src.channel, "tags": src.tags}
                    for src in service.log_sources
                ],
                "parser_chain": service.parser_chain,
                "rule_sets": service.rule_sets,
                "control": control,
            }
        )
    return out


@app.get("/api/services/{service_id}/status")
def service_status(service_id: str) -> dict[str, Any]:
    service = _service_or_404(service_id)
    return process_manager.status(service)


@app.get("/api/services/{service_id}/options")
def service_options(service_id: str) -> dict[str, Any]:
    service = _service_or_404(service_id)
    return {
        "service_id": service_id,
        "options": options_manager.list_options(service),
    }


@app.post("/api/services/{service_id}/options")
def service_options_update(service_id: str, payload: OptionUpdatePayload) -> dict[str, Any]:
    service = _service_or_404(service_id)
    try:
        options = options_manager.update_options(service, payload.values)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "service_id": service_id,
        "options": options,
    }


@app.post("/api/services/{service_id}/start")
def service_start(service_id: str) -> dict[str, Any]:
    service = _service_or_404(service_id)
    try:
        env_overrides = options_manager.options_env(service)
        return process_manager.start(service, env_overrides=env_overrides)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/services/{service_id}/stop")
def service_stop(service_id: str) -> dict[str, Any]:
    service = _service_or_404(service_id)
    try:
        return process_manager.stop(service)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/services/{service_id}/restart")
def service_restart(service_id: str) -> dict[str, Any]:
    service = _service_or_404(service_id)
    try:
        env_overrides = options_manager.options_env(service)
        return process_manager.restart(service, env_overrides=env_overrides)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/services/{service_id}/logs")
def get_logs(
    service_id: str,
    tail: int = Query(default=200, ge=1, le=5000),
    level: str | None = Query(default=None),
    event: str | None = Query(default=None),
    text: str | None = Query(default=None),
) -> dict[str, Any]:
    service = _service_or_404(service_id)
    entries = pipeline.read_tail(service, tail=tail)
    entries = _apply_log_filters(entries, level=level, event=event, text=text)
    return {"service_id": service_id, "count": len(entries), "entries": entries}


@app.get("/api/services/{service_id}/queries")
def get_queries(
    service_id: str,
    tail: int = Query(default=2000, ge=1, le=10000),
    text: str | None = Query(default=None),
) -> dict[str, Any]:
    service = _service_or_404(service_id)
    entries = pipeline.read_tail(service, tail=tail)
    query_entries = [
        entry for entry in entries
        if str(entry.get("event") or "") == "db.query.executed"
    ]
    if text:
        query_entries = _apply_log_filters(query_entries, text=text)

    queries: list[dict[str, Any]] = []
    for entry in query_entries:
        fields = entry.get("fields") or {}
        queries.append(
            {
                "timestamp": entry.get("timestamp"),
                "level": entry.get("level"),
                "tool": fields.get("tool"),
                "mode": fields.get("mode"),
                "row_count": fields.get("row_count"),
                "result_truncated": fields.get("result_truncated"),
                "query_preview": fields.get("query_preview"),
                "query_full": fields.get("query_full"),
                "query_full_truncated": fields.get("query_full_truncated"),
                "parameter_keys": fields.get("parameter_keys"),
                "source_path": entry.get("source_path"),
            }
        )
    return {"service_id": service_id, "count": len(queries), "queries": queries}


@app.get("/api/services/{service_id}/metrics")
def get_metrics(
    service_id: str,
    tail: int = Query(default=2000, ge=1, le=10000),
) -> dict[str, Any]:
    service = _service_or_404(service_id)
    entries = pipeline.read_tail(service, tail=tail)
    metrics = _compute_metrics(entries)
    return {"service_id": service_id, **metrics}


@app.get("/api/services/{service_id}/alerts")
def get_alerts(
    service_id: str,
    tail: int = Query(default=2000, ge=1, le=10000),
) -> dict[str, Any]:
    service = _service_or_404(service_id)
    entries = pipeline.read_tail(service, tail=tail)
    metrics = _compute_metrics(entries)
    return alert_engine.evaluate(service_id=service_id, entries=entries, metrics=metrics)


@app.get("/api/services/{service_id}/logs/stream")
async def stream_logs(service_id: str) -> StreamingResponse:
    service = _service_or_404(service_id)

    async def event_stream():
        async for entry in pipeline.stream_entries(service):
            data = json.dumps(entry, ensure_ascii=True)
            yield f"data: {data}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)

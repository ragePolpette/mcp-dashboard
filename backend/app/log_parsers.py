"""Pluggable parsers for raw log lines."""

from __future__ import annotations

import json
import re
from typing import Any

from .models import ParsedLogEntry

_PY_LOG_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[\sT][0-9:,.\-+:]+)\s+\[(?P<level>[A-Z]+)\]\s+(?P<logger>[^:]+):\s+(?P<message>.*)$"
)
_UVICORN_ACCESS_RE = re.compile(
    r"^(?P<level>INFO|WARNING|ERROR):\s+(?P<client>[\d\.:]+)\s+-\s+\"(?P<method>[A-Z]+)\s+(?P<path>[^ ]+)\s+HTTP/[0-9.]+\"\s+(?P<status>\d+)\s+(?P<status_text>.*)$"
)
_NODE_DEPRECATION_RE = re.compile(
    r"^\(node:(?P<pid>\d+)\)\s+\[(?P<code>[A-Z0-9]+)\]\s+DeprecationWarning:\s+(?P<message>.*)$"
)


def _normalize_level(value: str | None, fallback: str = "INFO") -> str:
    if not value:
        return fallback
    level = value.strip().upper()
    if level in {"DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL"}:
        return "WARN" if level == "WARNING" else level
    return fallback


def _apply_json_parser(line: str, entry: ParsedLogEntry) -> bool:
    text = line.strip()
    if not text.startswith("{") or not text.endswith("}"):
        return False
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return False
    if not isinstance(payload, dict):
        return False

    entry.raw = line
    entry.message = str(payload.get("message") or payload.get("msg") or line).strip()
    entry.level = _normalize_level(str(payload.get("level") or payload.get("severity") or "INFO"))
    entry.timestamp = str(payload.get("timestamp") or payload.get("ts") or "") or None
    entry.logger = str(payload.get("logger") or payload.get("source") or "") or None
    entry.event = str(payload.get("event") or "log.json")
    entry.fields.update({k: v for k, v in payload.items() if k not in {"message", "msg", "level", "severity", "timestamp", "ts", "logger", "source", "event"}})
    entry.tags.append("json")
    return True


def _apply_python_parser(line: str, entry: ParsedLogEntry) -> bool:
    match = _PY_LOG_RE.match(line.strip())
    if not match:
        return False
    entry.raw = line
    entry.message = match.group("message")
    entry.level = _normalize_level(match.group("level"))
    entry.timestamp = match.group("timestamp")
    entry.logger = match.group("logger")
    entry.event = "log.python"
    entry.tags.append("python")
    return True


def _apply_uvicorn_access_parser(line: str, entry: ParsedLogEntry) -> bool:
    match = _UVICORN_ACCESS_RE.match(line.strip())
    if not match:
        return False
    entry.raw = line
    entry.message = f'{match.group("method")} {match.group("path")} -> {match.group("status")}'
    entry.level = _normalize_level(match.group("level"))
    entry.event = "http.request"
    entry.fields.update(
        {
            "client": match.group("client"),
            "method": match.group("method"),
            "path": match.group("path"),
            "status": int(match.group("status")),
            "status_text": match.group("status_text").strip(),
        }
    )
    entry.tags.extend(["http", "access"])
    return True


def _apply_node_deprecation_parser(line: str, entry: ParsedLogEntry) -> bool:
    match = _NODE_DEPRECATION_RE.match(line.strip())
    if not match:
        return False
    entry.raw = line
    entry.message = match.group("message")
    entry.level = "WARN"
    entry.event = "node.deprecation"
    entry.fields.update({"pid": int(match.group("pid")), "deprecation_code": match.group("code")})
    entry.tags.extend(["node", "deprecation"])
    return True


_PARSER_MAP: dict[str, Any] = {
    "json": _apply_json_parser,
    "python": _apply_python_parser,
    "uvicorn_access": _apply_uvicorn_access_parser,
    "node_deprecation": _apply_node_deprecation_parser,
}


def parse_with_chain(line: str, entry: ParsedLogEntry, parser_chain: list[str]) -> ParsedLogEntry:
    """Apply parser chain and fallback to plain text."""

    chain = parser_chain or ["json", "python", "uvicorn_access", "node_deprecation"]
    for parser_name in chain:
        parser = _PARSER_MAP.get(parser_name)
        if parser and parser(line, entry):
            return entry

    entry.raw = line
    entry.message = line.rstrip("\r\n")
    entry.level = _normalize_level(entry.level)
    entry.event = entry.event or "log.line"
    return entry


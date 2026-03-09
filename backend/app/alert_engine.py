"""Alert evaluation engine driven by JSON rules."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def _parse_ts(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _compare(op: str, current: float, threshold: float) -> bool:
    if op == ">":
        return current > threshold
    if op == ">=":
        return current >= threshold
    if op == "<":
        return current < threshold
    if op == "<=":
        return current <= threshold
    if op == "==":
        return current == threshold
    if op == "!=":
        return current != threshold
    return False


@dataclass(slots=True)
class AlertRule:
    rule_id: str
    name: str
    severity: str
    kind: str
    threshold: float
    op: str
    metric: str | None = None
    event: str | None = None
    field: str | None = None
    window_minutes: int = 5
    message: str = ""


class AlertEngine:
    """Evaluates alert rules against parsed log entries and computed metrics."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.default_rules: list[AlertRule] = []
        self.service_rules: dict[str, list[AlertRule]] = {}
        self.reload()

    def reload(self) -> None:
        payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.default_rules = self._parse_rules(payload.get("defaults") or [])
        services_payload = payload.get("services") or {}
        out: dict[str, list[AlertRule]] = {}
        for service_id, raw_rules in services_payload.items():
            out[str(service_id)] = self._parse_rules(raw_rules or [])
        self.service_rules = out

    def _parse_rules(self, raw_rules: list[dict[str, Any]]) -> list[AlertRule]:
        rules: list[AlertRule] = []
        for raw in raw_rules:
            if not isinstance(raw, dict):
                continue
            rule_id = str(raw.get("id") or "").strip()
            kind = str(raw.get("kind") or "").strip()
            severity = str(raw.get("severity") or "warn").strip().lower()
            if not rule_id or not kind:
                continue
            try:
                threshold = float(raw.get("threshold"))
            except (TypeError, ValueError):
                continue
            rules.append(
                AlertRule(
                    rule_id=rule_id,
                    name=str(raw.get("name") or rule_id),
                    severity=severity if severity in {"warn", "alert"} else "warn",
                    kind=kind,
                    threshold=threshold,
                    op=str(raw.get("op") or ">=").strip(),
                    metric=str(raw.get("metric")) if raw.get("metric") is not None else None,
                    event=str(raw.get("event")) if raw.get("event") is not None else None,
                    field=str(raw.get("field")) if raw.get("field") is not None else None,
                    window_minutes=max(1, int(raw.get("window_minutes", 5))),
                    message=str(raw.get("message") or ""),
                )
            )
        return rules

    def _value_for_rule(
        self,
        rule: AlertRule,
        *,
        entries: list[dict[str, Any]],
        metrics: dict[str, Any],
        now: datetime,
    ) -> float:
        if rule.kind == "metric_threshold":
            if not rule.metric:
                return 0.0
            try:
                return float(metrics.get(rule.metric, 0.0) or 0.0)
            except (TypeError, ValueError):
                return 0.0

        window_start = now - timedelta(minutes=rule.window_minutes)
        window_entries: list[dict[str, Any]] = []
        for entry in entries:
            parsed_ts = _parse_ts(entry.get("timestamp"))
            if parsed_ts is None:
                continue
            if parsed_ts.tzinfo is None:
                parsed_ts = parsed_ts.replace(tzinfo=now.tzinfo)
            if parsed_ts.astimezone(now.tzinfo) >= window_start:
                window_entries.append(entry)

        if rule.kind == "event_count_threshold":
            target_event = str(rule.event or "")
            if not target_event:
                return 0.0
            return float(
                sum(1 for entry in window_entries if str(entry.get("event") or "") == target_event)
            )

        if rule.kind == "field_max_threshold":
            target_event = str(rule.event or "")
            field_name = str(rule.field or "")
            if not target_event or not field_name:
                return 0.0
            values: list[float] = []
            for entry in window_entries:
                if str(entry.get("event") or "") != target_event:
                    continue
                fields = entry.get("fields") or {}
                try:
                    values.append(float(fields.get(field_name)))
                except (TypeError, ValueError):
                    continue
            return max(values) if values else 0.0

        return 0.0

    def evaluate(
        self,
        *,
        service_id: str,
        entries: list[dict[str, Any]],
        metrics: dict[str, Any],
    ) -> dict[str, Any]:
        now = datetime.now().astimezone()
        rules = [*self.default_rules, *(self.service_rules.get(service_id) or [])]
        triggered: list[dict[str, Any]] = []

        for rule in rules:
            current = self._value_for_rule(rule, entries=entries, metrics=metrics, now=now)
            is_triggered = _compare(rule.op, current, rule.threshold)
            if not is_triggered:
                continue
            triggered.append(
                {
                    "id": rule.rule_id,
                    "name": rule.name,
                    "severity": rule.severity,
                    "kind": rule.kind,
                    "current_value": current,
                    "threshold": rule.threshold,
                    "op": rule.op,
                    "message": rule.message,
                }
            )

        status = "ok"
        if any(item["severity"] == "alert" for item in triggered):
            status = "alert"
        elif triggered:
            status = "warn"

        return {
            "service_id": service_id,
            "status": status,
            "triggered_count": len(triggered),
            "triggered": triggered,
            "evaluated_at": now.isoformat(),
        }

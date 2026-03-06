"""Rule engine for log enrichment without code changes."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import ParsedLogEntry


@dataclass(slots=True)
class LogRule:
    """Single matching rule."""

    contains: str | None
    regex: re.Pattern[str] | None
    set_fields: dict[str, Any]
    add_tags: list[str]

    def matches(self, line: str) -> bool:
        if self.contains and self.contains not in line:
            return False
        if self.regex and not self.regex.search(line):
            return False
        return True

    def apply(self, entry: ParsedLogEntry, line: str) -> None:
        for key, value in self.set_fields.items():
            if key == "level":
                entry.level = str(value).upper()
            elif key == "event":
                entry.event = str(value)
            elif key == "message":
                entry.message = str(value)
            else:
                entry.fields[key] = value
        entry.tags.extend(self.add_tags)


class LogRuleEngine:
    """Loads rule sets and applies them per service."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._rule_sets: dict[str, list[LogRule]] = {}
        self.reload()

    def reload(self) -> None:
        payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        loaded: dict[str, list[LogRule]] = {}
        for set_name, rules in (payload.get("rule_sets") or {}).items():
            loaded[set_name] = [self._parse_rule(rule) for rule in (rules or [])]
        self._rule_sets = loaded

    def _parse_rule(self, payload: dict[str, Any]) -> LogRule:
        contains = payload.get("contains")
        raw_regex = payload.get("regex")
        regex_obj = re.compile(str(raw_regex)) if raw_regex else None
        set_fields = payload.get("set") or {}
        add_tags = [str(tag) for tag in (payload.get("add_tags") or [])]
        return LogRule(
            contains=str(contains) if contains else None,
            regex=regex_obj,
            set_fields=dict(set_fields),
            add_tags=add_tags,
        )

    def apply(self, entry: ParsedLogEntry, line: str, rule_sets: list[str]) -> ParsedLogEntry:
        to_apply = ["default", *rule_sets]
        for set_name in to_apply:
            for rule in self._rule_sets.get(set_name, []):
                if rule.matches(line):
                    rule.apply(entry, line)
        # deduplicate tags while preserving order
        deduped: list[str] = []
        for tag in entry.tags:
            if tag not in deduped:
                deduped.append(tag)
        entry.tags = deduped
        return entry


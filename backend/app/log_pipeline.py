"""Log ingestion, parsing and streaming pipeline."""

from __future__ import annotations

import asyncio
import os
from dataclasses import asdict
from pathlib import Path
from typing import AsyncIterator

from .log_parsers import parse_with_chain
from .log_rules import LogRuleEngine
from .models import ParsedLogEntry, ServiceDefinition, ServiceLogSource


def _tail_lines(path: Path, tail: int) -> list[str]:
    if tail <= 0:
        return []
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return lines[-tail:]


class LogPipeline:
    """Parses log sources into normalized entries."""

    def __init__(self, rule_engine: LogRuleEngine):
        self.rule_engine = rule_engine

    def parse_line(
        self,
        *,
        service: ServiceDefinition,
        source: ServiceLogSource,
        line: str,
    ) -> ParsedLogEntry:
        entry = ParsedLogEntry(
            service_id=service.service_id,
            channel=source.channel,
            source_path=str(source.path),
            message=line.rstrip("\r\n"),
            raw=line.rstrip("\r\n"),
            tags=list(source.tags),
        )
        parse_with_chain(line, entry, service.parser_chain)
        self.rule_engine.apply(entry, line, service.rule_sets)
        return entry

    def read_tail(self, service: ServiceDefinition, tail: int) -> list[dict]:
        entries: list[dict] = []
        for source in service.log_sources:
            for line in _tail_lines(source.path, tail):
                parsed = self.parse_line(service=service, source=source, line=line)
                entries.append(asdict(parsed))
        return entries

    async def stream_entries(self, service: ServiceDefinition, poll_seconds: float = 0.5) -> AsyncIterator[dict]:
        offsets: dict[str, int] = {}
        for source in service.log_sources:
            try:
                offsets[str(source.path)] = source.path.stat().st_size
            except OSError:
                offsets[str(source.path)] = 0

        while True:
            has_output = False
            for source in service.log_sources:
                source_key = str(source.path)
                current_offset = offsets.get(source_key, 0)
                if not source.path.exists():
                    offsets[source_key] = 0
                    continue
                try:
                    size = source.path.stat().st_size
                except OSError:
                    continue
                if size < current_offset:
                    current_offset = 0

                if size == current_offset:
                    offsets[source_key] = current_offset
                    continue

                try:
                    with source.path.open("r", encoding="utf-8", errors="replace") as handle:
                        handle.seek(current_offset, os.SEEK_SET)
                        chunk = handle.read()
                        offsets[source_key] = handle.tell()
                except OSError:
                    continue

                for line in chunk.splitlines():
                    parsed = self.parse_line(service=service, source=source, line=line)
                    has_output = True
                    yield asdict(parsed)

            if not has_output:
                await asyncio.sleep(poll_seconds)


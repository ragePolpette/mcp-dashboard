"""Log ingestion, parsing and streaming pipeline."""

from __future__ import annotations

import asyncio
import os
import threading
from datetime import datetime
from dataclasses import asdict
from pathlib import Path
from typing import AsyncIterator

from .log_parsers import parse_with_chain
from .log_rules import LogRuleEngine
from .models import ParsedLogEntry, ServiceDefinition, ServiceLogSource

DEFAULT_LOG_RETENTION_DAYS = 15
TAIL_READ_CHUNK_BYTES = 16 * 1024


def _tail_lines(path: Path, tail: int) -> list[str]:
    if tail <= 0:
        return []
    if not path.exists():
        return []
    try:
        size = path.stat().st_size
    except OSError:
        return []
    if size <= 0:
        return []

    buffer = b""
    newline_count = 0
    position = size

    try:
        with path.open("rb") as handle:
            while position > 0 and newline_count <= tail:
                read_size = min(TAIL_READ_CHUNK_BYTES, position)
                position -= read_size
                handle.seek(position, os.SEEK_SET)
                chunk = handle.read(read_size)
                buffer = chunk + buffer
                newline_count = buffer.count(b"\n")
    except OSError:
        return []

    return buffer.decode("utf-8", errors="replace").splitlines()[-tail:]


class LogPipeline:
    """Parses log sources into normalized entries."""

    def __init__(self, rule_engine: LogRuleEngine):
        self.rule_engine = rule_engine
        self._tail_cache: dict[tuple[str, int], dict] = {}
        self._cache_lock = threading.Lock()

    def _sources_signature(self, service: ServiceDefinition) -> tuple:
        signature: list[tuple[str, bool, int | None, int | None]] = []
        for source in service.log_sources:
            try:
                stat = source.path.stat()
                signature.append((str(source.path), True, stat.st_size, stat.st_mtime_ns))
            except OSError:
                signature.append((str(source.path), False, None, None))
        return tuple(signature)

    def prune_old_logs(self, services: list[ServiceDefinition], *, retention_days: int = DEFAULT_LOG_RETENTION_DAYS) -> list[str]:
        if retention_days <= 0:
            return []

        cutoff = datetime.now().astimezone().timestamp() - (retention_days * 86400)
        pruned: list[str] = []
        seen: set[str] = set()

        for service in services:
            for source in service.log_sources:
                resolved = str(source.path.resolve())
                if resolved in seen:
                    continue
                seen.add(resolved)
                if self._prune_log_source(service=service, source=source, cutoff_epoch=cutoff):
                    pruned.append(resolved)

        return pruned

    def _prune_log_source(self, *, service: ServiceDefinition, source: ServiceLogSource, cutoff_epoch: float) -> bool:
        path = source.path
        if not path.exists():
            return False

        try:
            raw_text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return False

        if not raw_text:
            return False

        lines = raw_text.splitlines()
        kept: list[str] = []
        last_keep = True
        changed = False

        for line in lines:
            parsed = self.parse_line(service=service, source=source, line=line, fallback_timestamp=None)
            parsed_epoch = self._timestamp_to_epoch(parsed.timestamp)
            if parsed_epoch is None:
                keep_line = last_keep
            else:
                keep_line = parsed_epoch >= cutoff_epoch
                last_keep = keep_line
            if keep_line:
                kept.append(line)
            else:
                changed = True

        if not changed:
            return False

        out_text = "\n".join(kept)
        if raw_text.endswith(("\n", "\r")) and out_text:
            out_text += "\n"
        try:
            path.write_text(out_text, encoding="utf-8")
        except OSError:
            return False
        return True

    @staticmethod
    def _timestamp_to_epoch(value: str | None) -> float | None:
        if not value:
            return None
        text = str(value).strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.astimezone()
        return parsed.timestamp()

    def parse_line(
        self,
        *,
        service: ServiceDefinition,
        source: ServiceLogSource,
        line: str,
        fallback_timestamp: str | None = None,
    ) -> ParsedLogEntry:
        entry = ParsedLogEntry(
            service_id=service.service_id,
            channel=source.channel,
            source_path=str(source.path),
            message=line.rstrip("\r\n"),
            raw=line.rstrip("\r\n"),
            timestamp=fallback_timestamp,
            tags=list(source.tags),
        )
        parse_with_chain(line, entry, service.parser_chain)
        self.rule_engine.apply(entry, line, service.rule_sets)
        return entry

    def read_tail(self, service: ServiceDefinition, tail: int) -> list[dict]:
        cache_key = (service.service_id, int(tail))
        signature = self._sources_signature(service)
        with self._cache_lock:
            cached = self._tail_cache.get(cache_key)
            if cached and cached.get("signature") == signature:
                return list(cached["entries"])

        entries: list[dict] = []
        for source in service.log_sources:
            fallback_timestamp = None
            try:
                fallback_timestamp = datetime.fromtimestamp(source.path.stat().st_mtime).astimezone().isoformat()
            except OSError:
                fallback_timestamp = None
            for line in _tail_lines(source.path, tail):
                parsed = self.parse_line(
                    service=service,
                    source=source,
                    line=line,
                    fallback_timestamp=fallback_timestamp,
                )
                entries.append(asdict(parsed))

        with self._cache_lock:
            self._tail_cache[cache_key] = {
                "signature": signature,
                "entries": list(entries),
            }
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

                fallback_timestamp = datetime.now().astimezone().isoformat()
                for line in chunk.splitlines():
                    parsed = self.parse_line(
                        service=service,
                        source=source,
                        line=line,
                        fallback_timestamp=fallback_timestamp,
                    )
                    has_output = True
                    yield asdict(parsed)

            if not has_output:
                await asyncio.sleep(poll_seconds)


"""Log ingestion, parsing and streaming pipeline."""

from __future__ import annotations

import asyncio
import os
import threading
from collections.abc import AsyncIterator, Callable
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

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


def compact_log_file(path: Path, keep: Callable[[str], bool]) -> bool:
    """Drop lines rejected by ``keep`` from path, rewriting it in place.

    The file is streamed line by line through a reader and a trailing writer on
    the same inode, then truncated, so memory stays bounded and a child process
    that holds the file open in append mode keeps writing to the same file.
    Returns True when at least one line was removed.
    """
    changed = False
    with path.open("rb") as reader, path.open("r+b") as writer:
        while True:
            raw = reader.readline()
            if not raw:
                break
            line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            if keep(line):
                if changed:
                    writer.write(raw)
                else:
                    writer.seek(reader.tell())
            else:
                changed = True
        if changed:
            writer.flush()
            writer.truncate(writer.tell())
    return changed


def truncate_log_file(path: Path) -> None:
    """Empty a log file in place, creating it when missing, without replacing the inode."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.truncate(0)


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

    def prune_old_logs(
        self,
        services: list[ServiceDefinition],
        *,
        retention_days: int = DEFAULT_LOG_RETENTION_DAYS,
        now: datetime | None = None,
    ) -> list[str]:
        if retention_days <= 0:
            return []

        reference_time = now.astimezone() if now is not None else datetime.now().astimezone()
        cutoff = reference_time.timestamp() - (retention_days * 86400)
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

        last_keep = True

        def keep(line: str) -> bool:
            nonlocal last_keep
            parsed = self.parse_line(service=service, source=source, line=line, fallback_timestamp=None)
            parsed_epoch = self._timestamp_to_epoch(parsed.timestamp)
            if parsed_epoch is None:
                return last_keep
            last_keep = parsed_epoch >= cutoff_epoch
            return last_keep

        try:
            return compact_log_file(path, keep)
        except OSError:
            return False

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

    def _read_new_lines(
        self,
        service: ServiceDefinition,
        offsets: dict[str, int],
    ) -> list[tuple[ServiceLogSource, str]]:
        out: list[tuple[ServiceLogSource, str]] = []
        for source in service.log_sources:
            source_key = str(source.path)
            current_offset = offsets.get(source_key, 0)
            try:
                size = source.path.stat().st_size
            except FileNotFoundError:
                offsets[source_key] = 0
                continue
            except OSError:
                continue
            if size < current_offset:
                current_offset = 0
            if size == current_offset:
                offsets[source_key] = current_offset
                continue
            try:
                with source.path.open("rb") as handle:
                    handle.seek(current_offset, os.SEEK_SET)
                    chunk = handle.read(size - current_offset)
            except OSError:
                continue
            complete = chunk.rfind(b"\n") + 1
            if complete == 0:
                offsets[source_key] = current_offset
                continue
            offsets[source_key] = current_offset + complete
            text = chunk[:complete].decode("utf-8", errors="replace")
            out.extend((source, line) for line in text.splitlines())
        return out

    async def stream_entries(self, service: ServiceDefinition, poll_seconds: float = 0.5) -> AsyncIterator[dict]:
        offsets: dict[str, int] = {}
        for source in service.log_sources:
            try:
                offsets[str(source.path)] = source.path.stat().st_size
            except OSError:
                offsets[str(source.path)] = 0

        while True:
            new_lines = await asyncio.to_thread(self._read_new_lines, service, offsets)
            if not new_lines:
                await asyncio.sleep(poll_seconds)
                continue
            fallback_timestamp = datetime.now().astimezone().isoformat()
            for source, line in new_lines:
                parsed = self.parse_line(
                    service=service,
                    source=source,
                    line=line,
                    fallback_timestamp=fallback_timestamp,
                )
                yield asdict(parsed)

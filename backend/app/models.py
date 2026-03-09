"""Shared models for MCP dashboard backend."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ServiceLogSource:
    """Configured source for a service log stream."""

    path: Path
    channel: str = "stdout"
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ServiceOptionDefinition:
    """Configurable option exposed in dashboard before service start."""

    option_id: str
    label: str
    kind: str
    env_var: str
    default: Any = None
    description: str = ""
    required: bool = False
    secret: bool = False
    allowed_values: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ServiceControlDefinition:
    """Configured control plane settings for start/stop/restart."""

    workdir: Path
    start_command: list[str]
    host: str = "127.0.0.1"
    port: int | None = None
    health_url: str | None = None
    startup_timeout_sec: int = 12
    pid_file: Path | None = None
    stdout_log: Path | None = None
    stderr_log: Path | None = None
    env: dict[str, str] = field(default_factory=dict)
    options: list[ServiceOptionDefinition] = field(default_factory=list)


@dataclass(slots=True)
class ServiceDefinition:
    """Service definition for dashboard monitoring."""

    service_id: str
    name: str
    log_sources: list[ServiceLogSource]
    parser_chain: list[str] = field(default_factory=list)
    rule_sets: list[str] = field(default_factory=list)
    control: ServiceControlDefinition | None = None


@dataclass(slots=True)
class ParsedLogEntry:
    """Normalized log entry sent to UI."""

    service_id: str
    channel: str
    source_path: str
    message: str
    level: str = "INFO"
    event: str = "log.line"
    timestamp: str | None = None
    logger: str | None = None
    raw: str = ""
    tags: list[str] = field(default_factory=list)
    fields: dict[str, Any] = field(default_factory=dict)

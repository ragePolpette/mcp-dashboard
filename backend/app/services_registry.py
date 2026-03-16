"""Service registry loader from JSON config."""

from __future__ import annotations

import json
from pathlib import Path

from .models import (
    ServiceControlDefinition,
    ServiceDefinition,
    ServiceLogSource,
    ServiceOptionDefinition,
)


def _resolve_path(base_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _project_root(base_dir: Path) -> Path:
    return base_dir.resolve().parents[2]


def _is_runtime_project(base_dir: Path) -> bool:
    return _project_root(base_dir).name.lower() == "binah"


def _runtime_log_path(path: Path) -> Path:
    return Path(str(path).replace("_dev_runtime_logs", "_runtime_logs"))


def _is_runtime_log_source(source: ServiceLogSource) -> bool:
    tags = {str(tag).strip().lower() for tag in source.tags}
    if "service-log" in tags:
        return True
    return "runtime" in tags or "binah" in tags


def _is_legacy_runtime_log_source(source: ServiceLogSource) -> bool:
    return "_dev_runtime_logs" in str(source.path)


def _promote_legacy_runtime_source(source: ServiceLogSource) -> ServiceLogSource:
    tags = [str(tag) for tag in source.tags if str(tag).strip().lower() not in {"dev", "yetzirah"}]
    normalized = {tag.strip().lower() for tag in tags}
    if "runtime" not in normalized:
        tags.append("runtime")
    if "binah" not in normalized:
        tags.append("binah")
    if "legacy-runtime" not in normalized:
        tags.append("legacy-runtime")
    return ServiceLogSource(path=source.path, channel=source.channel, tags=tags)


class ServiceRegistry:
    """Loads and serves service definitions."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._services: dict[str, ServiceDefinition] = {}
        self.reload()

    def _parse_options(self, control: dict) -> list[ServiceOptionDefinition]:
        out: list[ServiceOptionDefinition] = []
        for raw in control.get("options") or []:
            if not isinstance(raw, dict):
                continue
            option_id = str(raw.get("id", "")).strip()
            env_var = str(raw.get("env_var", "")).strip()
            if not option_id or not env_var:
                continue
            kind = str(raw.get("type", "string")).strip().lower() or "string"
            if kind not in {"boolean", "string", "integer", "select"}:
                kind = "string"
            allowed_values = [str(v) for v in (raw.get("allowed_values") or [])]
            out.append(
                ServiceOptionDefinition(
                    option_id=option_id,
                    label=str(raw.get("label", option_id)).strip() or option_id,
                    kind=kind,
                    env_var=env_var,
                    default=raw.get("default"),
                    description=str(raw.get("description", "")).strip(),
                    required=bool(raw.get("required", False)),
                    secret=bool(raw.get("secret", False)),
                    allowed_values=allowed_values,
                )
            )
        return out

    def _parse_control(self, base_dir: Path, item: dict) -> ServiceControlDefinition | None:
        control = item.get("control")
        if not isinstance(control, dict):
            return None

        workdir_raw = str(control.get("workdir", "")).strip()
        start_command = [str(arg) for arg in (control.get("start_command") or []) if str(arg).strip()]
        if not workdir_raw or not start_command:
            return None

        port_value = control.get("port")
        port = int(port_value) if isinstance(port_value, int) or (isinstance(port_value, str) and port_value.strip().isdigit()) else None

        startup_timeout_raw = control.get("startup_timeout_sec", 12)
        try:
            startup_timeout_sec = max(1, int(startup_timeout_raw))
        except (TypeError, ValueError):
            startup_timeout_sec = 12

        runtime_project = _is_runtime_project(base_dir)

        def resolve_opt_path(key: str) -> Path | None:
            raw = str(control.get(key, "")).strip()
            if not raw:
                return None
            resolved = _resolve_path(base_dir, raw)
            if runtime_project:
                return _runtime_log_path(resolved)
            return resolved

        env_payload = control.get("env") or {}
        env = {str(k): str(v) for k, v in env_payload.items()} if isinstance(env_payload, dict) else {}

        return ServiceControlDefinition(
            workdir=_resolve_path(base_dir, workdir_raw),
            start_command=start_command,
            host=str(control.get("host", "127.0.0.1")).strip() or "127.0.0.1",
            port=port,
            health_url=str(control.get("health_url", "")).strip() or None,
            startup_timeout_sec=startup_timeout_sec,
            pid_file=resolve_opt_path("pid_file"),
            stdout_log=resolve_opt_path("stdout_log"),
            stderr_log=resolve_opt_path("stderr_log"),
            env=env,
            options=self._parse_options(control),
        )

    def reload(self) -> None:
        base_dir = self.config_path.parent
        runtime_project = _is_runtime_project(base_dir)
        payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        services: dict[str, ServiceDefinition] = {}

        for item in payload.get("services", []):
            service_id = str(item.get("id", "")).strip()
            if not service_id:
                continue
            sources: list[ServiceLogSource] = []
            for src in item.get("log_sources", []):
                raw_path = str(src.get("path", "")).strip()
                if not raw_path:
                    continue
                sources.append(
                    ServiceLogSource(
                        path=_resolve_path(base_dir, raw_path),
                        channel=str(src.get("channel", "stdout")).strip() or "stdout",
                        tags=[str(tag) for tag in (src.get("tags") or [])],
                    )
                )
            if runtime_project:
                runtime_sources = [source for source in sources if _is_runtime_log_source(source)]
                if runtime_sources and any(source.path.exists() for source in runtime_sources):
                    sources = runtime_sources
                else:
                    legacy_runtime_sources = [
                        _promote_legacy_runtime_source(source)
                        for source in sources
                        if _is_legacy_runtime_log_source(source) and source.path.exists()
                    ]
                    if legacy_runtime_sources:
                        sources = legacy_runtime_sources
                    elif runtime_sources:
                        sources = runtime_sources
            services[service_id] = ServiceDefinition(
                service_id=service_id,
                name=str(item.get("name", service_id)),
                log_sources=sources,
                parser_chain=[str(name) for name in (item.get("parser_chain") or [])],
                rule_sets=[str(name) for name in (item.get("rule_sets") or [])],
                control=self._parse_control(base_dir, item),
            )

        self._services = services

    def list_services(self) -> list[ServiceDefinition]:
        return list(self._services.values())

    def get(self, service_id: str) -> ServiceDefinition | None:
        return self._services.get(service_id)

"""Persistent service options store and validation."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from .models import ServiceDefinition, ServiceOptionDefinition


class ServiceOptionsManager:
    """Stores dashboard-configured options and maps them to env vars."""

    def __init__(self, state_path: Path):
        self.state_path = state_path
        self._lock = threading.Lock()
        self._state: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self.state_path.exists():
            self._state = {}
            return
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            self._state = {}
            return
        services = payload.get("services") if isinstance(payload, dict) else {}
        if not isinstance(services, dict):
            self._state = {}
            return
        out: dict[str, dict[str, Any]] = {}
        for service_id, values in services.items():
            if isinstance(values, dict):
                out[str(service_id)] = dict(values)
        self._state = out

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"services": self._state}
        self.state_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def _normalize_value(self, option: ServiceOptionDefinition, value: Any) -> Any:
        kind = option.kind
        if kind == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in {"true", "1", "yes", "on"}:
                    return True
                if lowered in {"false", "0", "no", "off"}:
                    return False
            if isinstance(value, (int, float)):
                return bool(value)
            raise ValueError(f"Invalid boolean value for {option.option_id}")

        if kind == "integer":
            if isinstance(value, bool):
                raise ValueError(f"Invalid integer value for {option.option_id}")
            try:
                return int(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid integer value for {option.option_id}") from exc

        if kind in {"string", "select"}:
            text = "" if value is None else str(value)
            if kind == "select" and option.allowed_values and text not in option.allowed_values:
                raise ValueError(f"Invalid option value for {option.option_id}")
            return text

        return value

    def _effective_value(self, service_id: str, option: ServiceOptionDefinition) -> Any:
        service_state = self._state.get(service_id, {})
        if option.option_id in service_state:
            return service_state[option.option_id]
        return option.default

    def _is_set(self, option: ServiceOptionDefinition, value: Any) -> bool:
        if value is None:
            return False
        if option.kind == "boolean":
            return True
        if option.kind == "integer":
            return True
        if option.kind in {"string", "select"}:
            return bool(str(value).strip())
        return True

    def list_options(self, service: ServiceDefinition) -> list[dict[str, Any]]:
        control = service.control
        if control is None:
            return []

        with self._lock:
            out: list[dict[str, Any]] = []
            for option in control.options:
                current = self._effective_value(service.service_id, option)
                normalized = self._normalize_value(option, current)
                is_set = self._is_set(option, normalized)
                item = {
                    "id": option.option_id,
                    "label": option.label,
                    "type": option.kind,
                    "description": option.description,
                    "required": option.required,
                    "secret": option.secret,
                    "allowed_values": option.allowed_values,
                    "default": option.default,
                    "is_set": is_set,
                }
                if option.secret:
                    item["value"] = None
                else:
                    item["value"] = normalized
                out.append(item)
            return out

    def update_options(self, service: ServiceDefinition, raw_values: dict[str, Any]) -> list[dict[str, Any]]:
        control = service.control
        if control is None:
            raise ValueError(f"Control not configured for service {service.service_id}")

        options = {opt.option_id: opt for opt in control.options}
        with self._lock:
            service_state = dict(self._state.get(service.service_id, {}))
            for key, raw in raw_values.items():
                option = options.get(key)
                if option is None:
                    continue

                # Secret strings: empty payload means "keep current" to avoid accidental wipe.
                if option.secret and option.kind in {"string", "select"}:
                    if raw is None:
                        continue
                    if isinstance(raw, str) and not raw.strip():
                        continue

                normalized = self._normalize_value(option, raw)
                service_state[key] = normalized

            for option in control.options:
                val = service_state.get(option.option_id, option.default)
                normalized = self._normalize_value(option, val)
                if option.required:
                    if normalized is None or (isinstance(normalized, str) and not normalized.strip()):
                        raise ValueError(f"Missing required option {option.option_id}")
                service_state[option.option_id] = normalized

            self._state[service.service_id] = service_state
            self._save()

        return self.list_options(service)

    def options_env(self, service: ServiceDefinition) -> dict[str, str]:
        control = service.control
        if control is None:
            return {}

        with self._lock:
            out: dict[str, str] = {}
            for option in control.options:
                value = self._effective_value(service.service_id, option)
                normalized = self._normalize_value(option, value)
                if normalized is None:
                    continue
                if option.kind == "boolean":
                    out[option.env_var] = "true" if bool(normalized) else "false"
                else:
                    out[option.env_var] = str(normalized)
            return out

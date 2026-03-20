"""Persistent dashboard UI settings and service visibility."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from .models import ServiceDefinition

DEFAULT_SETTINGS = {
    "refresh_interval_sec": 5,
    "show_stopped_services": True,
    "default_advanced_tab": "automatic",
    "service_order": "manual",
    "show_alerts_in_home": True,
    "log_retention_days": 15,
    "recent_rows_limit": 30,
}

VALID_REFRESH_INTERVALS = {0, 5, 10, 30}
VALID_ADVANCED_TABS = {"automatic", "options", "logs", "inspector"}
VALID_SERVICE_ORDER = {"manual", "group", "status"}


class DashboardSettingsManager:
    """Stores dashboard preferences and per-service visibility."""

    def __init__(self, state_path: Path):
        self.state_path = state_path
        self._lock = threading.Lock()
        self._preferences: dict[str, Any] = dict(DEFAULT_SETTINGS)
        self._service_visibility: dict[str, bool] = {}
        self._load()

    def _load(self) -> None:
        if not self.state_path.exists():
            return
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return

        if isinstance(payload, dict):
            preferences = payload.get("preferences")
            if isinstance(preferences, dict):
                for key, value in preferences.items():
                    try:
                        self._preferences[key] = self._normalize_preference(key, value)
                    except ValueError:
                        continue

            service_visibility = payload.get("service_visibility")
            if isinstance(service_visibility, dict):
                out: dict[str, bool] = {}
                for service_id, visible in service_visibility.items():
                    out[str(service_id)] = bool(visible)
                self._service_visibility = out

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "preferences": self._preferences,
            "service_visibility": self._service_visibility,
        }
        self.state_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def _normalize_preference(self, key: str, value: Any) -> Any:
        if key == "refresh_interval_sec":
            numeric = int(value)
            if numeric not in VALID_REFRESH_INTERVALS:
                raise ValueError("Invalid refresh interval")
            return numeric

        if key == "show_stopped_services":
            return bool(value)

        if key == "default_advanced_tab":
            text = str(value).strip().lower()
            if text not in VALID_ADVANCED_TABS:
                raise ValueError("Invalid advanced tab")
            return text

        if key == "service_order":
            text = str(value).strip().lower()
            if text not in VALID_SERVICE_ORDER:
                raise ValueError("Invalid service order")
            return text

        if key == "show_alerts_in_home":
            return bool(value)

        if key == "log_retention_days":
            numeric = int(value)
            if numeric < 1 or numeric > 365:
                raise ValueError("Invalid retention days")
            return numeric

        if key == "recent_rows_limit":
            numeric = int(value)
            if numeric < 10 or numeric > 500:
                raise ValueError("Invalid recent rows limit")
            return numeric

        raise ValueError(f"Unknown preference: {key}")

    def snapshot(self, services: list[ServiceDefinition]) -> dict[str, Any]:
        with self._lock:
            service_visibility = {
                service.service_id: self._service_visibility.get(service.service_id, True)
                for service in services
            }
            return {
                "preferences": dict(self._preferences),
                "service_visibility": service_visibility,
            }

    def is_visible(self, service_id: str) -> bool:
        with self._lock:
            return self._service_visibility.get(service_id, True)

    def update(
        self,
        *,
        services: list[ServiceDefinition],
        preferences: dict[str, Any] | None = None,
        service_visibility: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        service_ids = {service.service_id for service in services}
        with self._lock:
            if preferences:
                for key, value in preferences.items():
                    self._preferences[key] = self._normalize_preference(str(key), value)

            if service_visibility:
                for service_id, visible in service_visibility.items():
                    service_id = str(service_id)
                    if service_id not in service_ids:
                        continue
                    self._service_visibility[service_id] = bool(visible)

            self._save()

            return {
                "preferences": dict(self._preferences),
                "service_visibility": {
                    service.service_id: self._service_visibility.get(service.service_id, True)
                    for service in services
                },
            }

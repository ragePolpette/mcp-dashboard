"""Tests for dashboard settings persistence and service visibility."""

from __future__ import annotations

from pathlib import Path
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.dashboard_settings import DashboardSettingsManager  # noqa: E402
from app.models import ServiceControlDefinition, ServiceDefinition, ServiceLogSource  # noqa: E402


def _service(service_id: str) -> ServiceDefinition:
    return ServiceDefinition(
        service_id=service_id,
        name=service_id,
        log_sources=[ServiceLogSource(path=Path(f"{service_id}.log"), channel="stdout")],
        control=ServiceControlDefinition(workdir=Path("."), start_command=["python", "-m", service_id]),
    )


def test_dashboard_settings_defaults_and_visibility():
    with tempfile.TemporaryDirectory() as tmp:
        settings = DashboardSettingsManager(Path(tmp) / "runtime" / "dashboard_settings.json")
        services = [_service("llm-context"), _service("llm-memory")]

        snapshot = settings.snapshot(services)

        assert snapshot["preferences"]["refresh_interval_sec"] == 5
        assert snapshot["preferences"]["show_stopped_services"] is True
        assert snapshot["service_visibility"]["llm-context"] is True
        assert snapshot["service_visibility"]["llm-memory"] is True


def test_dashboard_settings_update_persists_preferences_and_visibility():
    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "runtime" / "dashboard_settings.json"
        settings = DashboardSettingsManager(state_path)
        services = [_service("llm-context"), _service("llm-memory")]

        updated = settings.update(
            services=services,
            preferences={
                "refresh_interval_sec": 10,
                "default_advanced_tab": "logs",
                "service_order": "status",
                "show_alerts_in_home": False,
                "log_retention_days": 21,
                "recent_rows_limit": 80,
            },
            service_visibility={"llm-memory": False},
        )

        assert updated["preferences"]["refresh_interval_sec"] == 10
        assert updated["preferences"]["default_advanced_tab"] == "logs"
        assert updated["preferences"]["service_order"] == "status"
        assert updated["preferences"]["show_alerts_in_home"] is False
        assert updated["preferences"]["log_retention_days"] == 21
        assert updated["preferences"]["recent_rows_limit"] == 80
        assert updated["service_visibility"]["llm-memory"] is False

        reloaded = DashboardSettingsManager(state_path)
        snapshot = reloaded.snapshot(services)
        assert snapshot["preferences"]["refresh_interval_sec"] == 10
        assert snapshot["service_visibility"]["llm-memory"] is False

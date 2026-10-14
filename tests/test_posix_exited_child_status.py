"""Regression: an MCP that exits during startup must not appear running."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.models import ServiceControlDefinition, ServiceDefinition  # noqa: E402
from app.process_manager import ServiceProcessManager  # noqa: E402


@pytest.mark.skipif(os.name == "nt", reason="POSIX child reaping only")
def test_failed_start_is_not_running(tmp_path, monkeypatch):
    control = ServiceControlDefinition(
        workdir=tmp_path,
        start_command=[sys.executable, "-c", "import sys; sys.exit(2)"],
        port=19871,
        startup_timeout_sec=1,
        pid_file=tmp_path / "failed.pid",
    )
    service = ServiceDefinition(service_id="failed", name="Failed", log_sources=[], control=control)
    manager = ServiceProcessManager()
    monkeypatch.setattr(manager, "_pid_from_port", lambda port: None)
    result = manager.start(service)
    assert result["ok"] is False
    assert result["status"]["running"] is False
    assert not control.pid_file.exists()

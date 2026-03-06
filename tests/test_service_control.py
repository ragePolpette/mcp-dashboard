"""Tests for service control registry and process manager basics."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models import ServiceControlDefinition, ServiceDefinition, ServiceLogSource  # noqa: E402
from app.process_manager import ServiceProcessManager  # noqa: E402
from app.services_registry import ServiceRegistry  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def test_registry_parses_control_block():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        config_dir = tmp_dir / "config"
        config_dir.mkdir(parents=True)

        services_path = config_dir / "services.json"
        _write_json(
            services_path,
            {
                "services": [
                    {
                        "id": "svc-a",
                        "name": "Service A",
                        "control": {
                            "workdir": "../work/svc-a",
                            "start_command": ["python", "-m", "svc.server"],
                            "host": "127.0.0.1",
                            "port": 9001,
                            "pid_file": "../runtime/svc-a.pid",
                        },
                        "log_sources": [
                            {
                                "path": "../logs/svc-a.err.log",
                                "channel": "stderr",
                                "tags": ["dev"],
                            }
                        ],
                    }
                ]
            },
        )

        registry = ServiceRegistry(services_path)
        service = registry.get("svc-a")

        assert service is not None
        assert service.control is not None
        assert service.control.start_command == ["python", "-m", "svc.server"]
        assert service.control.port == 9001
        assert service.control.workdir.name == "svc-a"


def test_process_status_without_control_is_safe():
    manager = ServiceProcessManager()
    service = ServiceDefinition(
        service_id="svc-no-control",
        name="No Control",
        log_sources=[ServiceLogSource(path=Path("dummy.log"), channel="stderr")],
        parser_chain=[],
        rule_sets=[],
        control=None,
    )

    status = manager.status(service)
    assert status["control_available"] is False
    assert status["running"] is False
    assert status["last_error"] == "control_not_configured"


def test_start_applies_env_overrides():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        out_file = tmp_dir / "env.txt"
        pid_file = tmp_dir / "svc.pid"

        script = (
            "import os,time,pathlib; "
            f"pathlib.Path(r'{str(out_file)}').write_text(os.getenv('TEST_OPT',''),encoding='utf-8'); "
            "time.sleep(5)"
        )

        service = ServiceDefinition(
            service_id="svc-env",
            name="Service Env",
            log_sources=[ServiceLogSource(path=tmp_dir / "dummy.log", channel="stderr")],
            control=ServiceControlDefinition(
                workdir=tmp_dir,
                start_command=[sys.executable, "-c", script],
                pid_file=pid_file,
            ),
        )

        manager = ServiceProcessManager()
        start = manager.start(service, env_overrides={"TEST_OPT": "enabled"})
        assert start["ok"] is True or start["result"] in {"started_unverified", "started"}

        deadline = time.time() + 2.0
        while time.time() < deadline and not out_file.exists():
            time.sleep(0.1)

        assert out_file.exists()
        assert out_file.read_text(encoding="utf-8") == "enabled"

        stop = manager.stop(service)
        assert stop["ok"] is True


def test_start_sets_hidden_flags_and_unbuffered_python(monkeypatch):
    captured: dict[str, object] = {}

    class DummyProc:
        pid = 4321

    def fake_popen(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        return DummyProc()

    manager = ServiceProcessManager()
    service = ServiceDefinition(
        service_id="svc-hidden",
        name="Service Hidden",
        log_sources=[ServiceLogSource(path=Path("dummy.log"), channel="stderr")],
        parser_chain=[],
        rule_sets=[],
        control=ServiceControlDefinition(
            workdir=Path("."),
            start_command=["python", "-c", "print('ok')"],
            pid_file=None,
        ),
    )

    monkeypatch.setattr("app.process_manager.subprocess.Popen", fake_popen)

    start = manager.start(service, env_overrides={"TEST_OPT": "enabled"})

    assert start["result"] in {"started", "started_unverified"}
    assert captured["env"]["TEST_OPT"] == "enabled"
    assert captured["env"]["PYTHONUNBUFFERED"] == "1"
    assert captured["env"]["PYTHONIOENCODING"] == "utf-8"
    assert captured["creationflags"] == manager._build_creationflags()


def test_start_redirects_stdout_and_stderr_to_logs():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        stdout_log = tmp_dir / "svc.out.log"
        stderr_log = tmp_dir / "svc.err.log"
        pid_file = tmp_dir / "svc.pid"

        script = (
            "import sys,time; "
            "print('stdout-line', flush=True); "
            "print('stderr-line', file=sys.stderr, flush=True); "
            "time.sleep(5)"
        )

        service = ServiceDefinition(
            service_id="svc-logs",
            name="Service Logs",
            log_sources=[ServiceLogSource(path=stdout_log, channel="stdout")],
            parser_chain=[],
            rule_sets=[],
            control=ServiceControlDefinition(
                workdir=tmp_dir,
                start_command=[sys.executable, "-c", script],
                pid_file=pid_file,
                stdout_log=stdout_log,
                stderr_log=stderr_log,
            ),
        )

        manager = ServiceProcessManager()
        start = manager.start(service)
        assert start["result"] in {"started", "started_unverified"}

        deadline = time.time() + 2.0
        while time.time() < deadline and (
            (not stdout_log.exists() or "stdout-line" not in stdout_log.read_text(encoding="utf-8", errors="replace"))
            or (not stderr_log.exists() or "stderr-line" not in stderr_log.read_text(encoding="utf-8", errors="replace"))
        ):
            time.sleep(0.1)

        assert "stdout-line" in stdout_log.read_text(encoding="utf-8", errors="replace")
        assert "stderr-line" in stderr_log.read_text(encoding="utf-8", errors="replace")

        stop = manager.stop(service)
        assert stop["ok"] is True

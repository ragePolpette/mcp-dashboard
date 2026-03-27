"""Tests for service control registry and process manager basics."""

from __future__ import annotations

import json
import socket
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


def test_registry_runtime_mode_prefers_runtime_logs_and_runtime_log_paths():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        config_dir = tmp_dir / "Binah" / "mcp-dashboard" / "backend" / "config"
        config_dir.mkdir(parents=True)
        runtime_log = tmp_dir / "Binah" / "tools" / "_runtime_logs" / "svc.out.log"
        runtime_log.parent.mkdir(parents=True)
        runtime_log.write_text("runtime-line\n", encoding="utf-8")

        services_path = config_dir / "services.json"
        _write_json(
            services_path,
            {
                "services": [
                    {
                        "id": "svc-runtime",
                        "name": "Service Runtime",
                        "control": {
                            "workdir": "../../../llm-db-dev-mcp",
                            "start_command": ["node", "src/server.js"],
                            "stdout_log": "../../../tools/_dev_runtime_logs/svc.out.log",
                            "stderr_log": "../../../tools/_dev_runtime_logs/svc.err.log",
                        },
                        "log_sources": [
                            {
                                "path": "../../../tools/_runtime_logs/svc.out.log",
                                "channel": "stdout",
                                "tags": ["runtime", "binah"],
                            },
                            {
                                "path": "../../../tools/_dev_runtime_logs/svc.out.log",
                                "channel": "stdout",
                                "tags": ["dev", "yetzirah"],
                            },
                        ],
                    }
                ]
            },
        )

        registry = ServiceRegistry(services_path)
        service = registry.get("svc-runtime")

        assert service is not None
        assert service.control is not None
        assert "_runtime_logs" in str(service.control.stdout_log)
        assert "_runtime_logs" in str(service.control.stderr_log)
        assert len(service.log_sources) == 1
        assert "runtime" in service.log_sources[0].tags


def test_registry_runtime_mode_falls_back_to_legacy_runtime_logs_when_needed():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        config_dir = tmp_dir / "Binah" / "mcp-dashboard" / "backend" / "config"
        config_dir.mkdir(parents=True)
        legacy_log = tmp_dir / "Binah" / "tools" / "_dev_runtime_logs" / "svc.out.log"
        legacy_log.parent.mkdir(parents=True)
        legacy_log.write_text("legacy-line\n", encoding="utf-8")

        services_path = config_dir / "services.json"
        _write_json(
            services_path,
            {
                "services": [
                    {
                        "id": "svc-runtime-fallback",
                        "name": "Service Runtime Fallback",
                        "control": {
                            "workdir": "../../../llm-db-dev-mcp",
                            "start_command": ["node", "src/server.js"],
                            "stdout_log": "../../../tools/_dev_runtime_logs/svc.out.log",
                        },
                        "log_sources": [
                            {
                                "path": "../../../tools/_runtime_logs/svc.out.log",
                                "channel": "stdout",
                                "tags": ["runtime", "binah"],
                            },
                            {
                                "path": "../../../tools/_dev_runtime_logs/svc.out.log",
                                "channel": "stdout",
                                "tags": ["dev", "yetzirah"],
                            },
                        ],
                    }
                ]
            },
        )

        registry = ServiceRegistry(services_path)
        service = registry.get("svc-runtime-fallback")

        assert service is not None
        assert len(service.log_sources) == 1
        assert "runtime" in service.log_sources[0].tags
        assert "binah" in service.log_sources[0].tags
        assert "legacy-runtime" in service.log_sources[0].tags
        assert "dev" not in service.log_sources[0].tags


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


def test_status_includes_health_payload(monkeypatch):
    manager = ServiceProcessManager()
    service = ServiceDefinition(
        service_id="svc-health",
        name="Service Health",
        log_sources=[ServiceLogSource(path=Path("dummy.log"), channel="stderr")],
        parser_chain=[],
        rule_sets=[],
        control=ServiceControlDefinition(
            workdir=Path("."),
            start_command=["python", "-c", "print('ok')"],
            host="127.0.0.1",
            port=9999,
            health_url="http://127.0.0.1:9999/health",
        ),
    )

    monkeypatch.setattr(manager, "_read_pid", lambda _pid_file: None)
    monkeypatch.setattr(manager, "_pid_from_port", lambda _port: 4321)
    monkeypatch.setattr(manager, "_is_port_open", lambda _host, _port: True)
    monkeypatch.setattr(
        manager,
        "_probe_health",
        lambda _url: {
            "ok": True,
            "payload": {
                "status": "ready",
                "write_enabled": False,
                "ingest_enabled": False,
            },
        },
    )

    status = manager.status(service)

    assert status["running"] is True
    assert status["health_ok"] is True
    assert status["health_details"]["status"] == "ready"
    assert status["health_details"]["write_enabled"] is False


def test_probe_health_parses_json_payload(monkeypatch):
    manager = ServiceProcessManager()

    class FakeResponse:
        status = 200

        def read(self):
            return b'{"status":"ready","write_enabled":false,"ingest_enabled":false}'

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("app.process_manager.urllib.request.urlopen", lambda req, timeout=1.5: FakeResponse())

    payload = manager._probe_health("http://127.0.0.1:8765/health")

    assert payload["ok"] is True
    assert payload["payload"]["status"] == "ready"
    assert payload["payload"]["write_enabled"] is False


def test_probe_health_treats_socket_timeout_as_unhealthy(monkeypatch):
    manager = ServiceProcessManager()

    def raise_timeout(req, timeout=1.5):
        raise socket.timeout("timed out while reading response")

    monkeypatch.setattr("app.process_manager.urllib.request.urlopen", raise_timeout)

    payload = manager._probe_health("http://127.0.0.1:8765/health")

    assert payload == {"ok": False, "payload": None}


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

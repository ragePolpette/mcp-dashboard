"""Process control manager for MCP services in dashboard."""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

from .models import ServiceControlDefinition, ServiceDefinition


@dataclass(slots=True)
class ServiceStatus:
    service_id: str
    control_available: bool
    running: bool
    pid: int | None
    host: str | None
    port: int | None
    health_ok: bool | None
    last_error: str | None = None


class ServiceProcessManager:
    """Starts/stops services using explicit per-service config."""

    def __init__(self) -> None:
        self._locks: dict[str, threading.Lock] = {}

    def _lock_for(self, service_id: str) -> threading.Lock:
        lock = self._locks.get(service_id)
        if lock is None:
            lock = threading.Lock()
            self._locks[service_id] = lock
        return lock

    def status(self, service: ServiceDefinition) -> dict:
        control = service.control
        if control is None:
            return asdict(
                ServiceStatus(
                    service_id=service.service_id,
                    control_available=False,
                    running=False,
                    pid=None,
                    host=None,
                    port=None,
                    health_ok=None,
                    last_error="control_not_configured",
                )
            )

        pid_from_file = self._read_pid(control.pid_file)
        pid_running = self._is_pid_running(pid_from_file) if pid_from_file else False

        pid_from_port = self._pid_from_port(control.port) if control.port else None
        port_running = self._is_port_open(control.host, control.port) if control.port else False

        running = bool(pid_running or port_running or pid_from_port)
        pid = pid_from_port or pid_from_file
        health_ok = self._probe_health(control.health_url)

        if control.pid_file and pid_from_file and not pid_running and not pid_from_port:
            try:
                control.pid_file.unlink(missing_ok=True)
            except OSError:
                pass

        return asdict(
            ServiceStatus(
                service_id=service.service_id,
                control_available=True,
                running=running,
                pid=pid,
                host=control.host,
                port=control.port,
                health_ok=health_ok,
                last_error=None,
            )
        )

    def start(self, service: ServiceDefinition, env_overrides: dict[str, str] | None = None) -> dict:
        with self._lock_for(service.service_id):
            return self._start_unlocked(service, env_overrides=env_overrides)

    def stop(self, service: ServiceDefinition) -> dict:
        with self._lock_for(service.service_id):
            return self._stop_unlocked(service)

    def restart(self, service: ServiceDefinition, env_overrides: dict[str, str] | None = None) -> dict:
        with self._lock_for(service.service_id):
            stop_res = self._stop_unlocked(service)
            start_res = self._start_unlocked(service, env_overrides=env_overrides)
            return {
                "ok": bool(start_res.get("ok")),
                "service_id": service.service_id,
                "action": "restart",
                "stop": stop_res,
                "start": start_res,
                "status": start_res.get("status"),
            }

    def _start_unlocked(self, service: ServiceDefinition, env_overrides: dict[str, str] | None = None) -> dict:
        control = self._require_control(service)
        before = self.status(service)
        if before["running"]:
            return {
                "ok": True,
                "service_id": service.service_id,
                "action": "start",
                "result": "already_running",
                "status": before,
            }

        control.workdir.mkdir(parents=True, exist_ok=True)
        self._ensure_parent_dirs(control)

        stdout_handle = self._open_log_file(control.stdout_log)
        stderr_handle = self._open_log_file(control.stderr_log)

        env = self._build_process_env(control, env_overrides=env_overrides)
        creationflags = self._build_creationflags()

        try:
            proc = subprocess.Popen(
                control.start_command,
                cwd=str(control.workdir),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=stdout_handle or subprocess.DEVNULL,
                stderr=stderr_handle or subprocess.DEVNULL,
                creationflags=creationflags,
            )
        finally:
            if stdout_handle:
                stdout_handle.close()
            if stderr_handle:
                stderr_handle.close()

        if control.pid_file:
            control.pid_file.write_text(str(proc.pid), encoding="utf-8")

        self._wait_startup(control)
        after = self.status(service)

        return {
            "ok": bool(after["running"]),
            "service_id": service.service_id,
            "action": "start",
            "result": "started" if after["running"] else "started_unverified",
            "pid": after["pid"] or proc.pid,
            "status": after,
        }

    def _stop_unlocked(self, service: ServiceDefinition) -> dict:
        control = self._require_control(service)
        before = self.status(service)
        pids = self._collect_candidate_pids(control, before)
        killed_any = False

        for pid in pids:
            if self._terminate_pid(pid):
                killed_any = True

        if control.pid_file:
            try:
                control.pid_file.unlink(missing_ok=True)
            except OSError:
                pass

        self._wait_shutdown(control)
        after = self.status(service)

        return {
            "ok": not after["running"],
            "service_id": service.service_id,
            "action": "stop",
            "result": "stopped" if not after["running"] else "still_running",
            "killed_any": killed_any,
            "status_before": before,
            "status": after,
        }

    def _require_control(self, service: ServiceDefinition) -> ServiceControlDefinition:
        if service.control is None:
            raise ValueError(f"Control not configured for service {service.service_id}")
        return service.control

    def _ensure_parent_dirs(self, control: ServiceControlDefinition) -> None:
        for path in (control.pid_file, control.stdout_log, control.stderr_log):
            if path is not None:
                path.parent.mkdir(parents=True, exist_ok=True)

    def _open_log_file(self, path: Path | None):
        if path is None:
            return None
        return path.open("a", encoding="utf-8")

    def _build_process_env(
        self,
        control: ServiceControlDefinition,
        env_overrides: dict[str, str] | None = None,
    ) -> dict[str, str]:
        env = os.environ.copy()
        env.update(control.env)
        if env_overrides:
            env.update(env_overrides)

        start_exe = str(control.start_command[0]).lower() if control.start_command else ""
        if "python" in start_exe:
            env.setdefault("PYTHONUNBUFFERED", "1")
            env.setdefault("PYTHONIOENCODING", "utf-8")

        return env

    def _build_creationflags(self) -> int:
        if os.name != "nt":
            return 0

        create_new_process_group = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        create_no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        return create_new_process_group | create_no_window

    def _wait_startup(self, control: ServiceControlDefinition) -> None:
        if control.port is None:
            return
        timeout = max(1, control.startup_timeout_sec)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._is_port_open(control.host, control.port):
                return
            time.sleep(0.25)

    def _wait_shutdown(self, control: ServiceControlDefinition) -> None:
        if control.port is None:
            return
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if not self._is_port_open(control.host, control.port):
                return
            time.sleep(0.2)

    def _read_pid(self, pid_file: Path | None) -> int | None:
        if pid_file is None or not pid_file.exists():
            return None
        try:
            raw = pid_file.read_text(encoding="utf-8").strip()
            return int(raw) if raw else None
        except (OSError, ValueError):
            return None

    def _collect_candidate_pids(self, control: ServiceControlDefinition, status: dict) -> list[int]:
        pids: set[int] = set()
        pid = status.get("pid")
        if isinstance(pid, int):
            pids.add(pid)

        pid_from_file = self._read_pid(control.pid_file)
        if pid_from_file:
            pids.add(pid_from_file)

        if control.port:
            pid_from_port = self._pid_from_port(control.port)
            if pid_from_port:
                pids.add(pid_from_port)

        return sorted(pids)

    def _is_pid_running(self, pid: int | None) -> bool:
        if not pid:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
        return True

    def _terminate_pid(self, pid: int) -> bool:
        if pid <= 0:
            return False
        if os.name == "nt":
            proc = subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode == 0:
                return True
            merged = f"{proc.stdout}\n{proc.stderr}".lower()
            return "not found" in merged

        try:
            os.kill(pid, signal.SIGTERM)
            return True
        except OSError:
            return False

    def _is_port_open(self, host: str, port: int | None) -> bool:
        if port is None:
            return False
        try:
            with socket.create_connection((host, port), timeout=0.8):
                return True
        except OSError:
            return False

    def _pid_from_port(self, port: int | None) -> int | None:
        if port is None:
            return None

        if os.name == "nt":
            proc = subprocess.run(
                ["netstat", "-ano", "-p", "tcp"],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode != 0:
                return None
            needle = f":{port}"
            for raw_line in proc.stdout.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) < 5:
                    continue
                local_addr = parts[1]
                state = parts[3].upper()
                pid_raw = parts[4]
                if state != "LISTENING":
                    continue
                if not local_addr.endswith(needle):
                    continue
                try:
                    return int(pid_raw)
                except ValueError:
                    return None
            return None

        proc = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return None
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.isdigit():
                return int(line)
        return None

    def _probe_health(self, url: str | None) -> bool | None:
        if not url:
            return None
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=1.5) as response:
                return 200 <= response.status < 400
        except (urllib.error.URLError, TimeoutError, ValueError):
            return False

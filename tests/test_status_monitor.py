"""Tests for the background status cache, per-service locks and dashboard shutdown."""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import main  # noqa: E402
from app.main import app  # noqa: E402
from app.models import ServiceDefinition  # noqa: E402
from app.process_manager import ServiceProcessManager  # noqa: E402
from app.status_monitor import ServiceStatusMonitor  # noqa: E402
from dashboard_client import dashboard_client  # noqa: E402


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


def _service(service_id: str = "svc-a") -> ServiceDefinition:
    return ServiceDefinition(service_id=service_id, name=service_id, log_sources=[])


def _counting_status():
    calls: list[str] = []

    def status(service: ServiceDefinition) -> dict:
        calls.append(service.service_id)
        return {"service_id": service.service_id, "call": len(calls)}

    return calls, status


def _mark_running(monitor: ServiceStatusMonitor, monkeypatch) -> None:
    monkeypatch.setattr(ServiceStatusMonitor, "running", property(lambda _self: True))


def test_monitor_without_poller_always_reads_live():
    calls, status = _counting_status()
    monitor = ServiceStatusMonitor(status, lambda: [])

    monitor.get(_service())
    monitor.get(_service())

    assert calls == ["svc-a", "svc-a"]


def test_monitor_serves_cached_status_while_fresh(monkeypatch):
    calls, status = _counting_status()
    clock = FakeClock()
    service = _service()
    monitor = ServiceStatusMonitor(status, lambda: [service], interval_seconds=3, clock=clock)
    _mark_running(monitor, monkeypatch)

    monitor.refresh_all()
    clock.now += 5
    assert monitor.get(service)["call"] == 1
    clock.now += 2
    assert monitor.get(service)["call"] == 2
    assert calls == ["svc-a", "svc-a"]


def test_invalidate_forces_a_fresh_read(monkeypatch):
    calls, status = _counting_status()
    service = _service()
    monitor = ServiceStatusMonitor(status, lambda: [service], clock=FakeClock())
    _mark_running(monitor, monkeypatch)

    monitor.refresh_all()
    monitor.invalidate("svc-a")
    assert monitor.get(service)["call"] == 2

    monitor.invalidate()
    assert monitor.get(service)["call"] == 3


def test_poll_started_before_invalidation_cannot_overwrite_newer_state(monkeypatch):
    service = _service()
    monitor = ServiceStatusMonitor(lambda _service: {}, lambda: [service], clock=FakeClock())
    _mark_running(monitor, monkeypatch)

    def slow_status(_service):
        monitor.invalidate("svc-a")
        return {"state": "stale"}

    monitor._status_fn = slow_status
    monitor.refresh(service)
    monitor._status_fn = lambda _service: {"state": "fresh"}

    assert monitor.get(service) == {"state": "fresh"}


def test_background_poller_refreshes_and_runs_tick_hooks():
    calls, status = _counting_status()
    ticks: list[int] = []
    monitor = ServiceStatusMonitor(status, lambda: [_service()], interval_seconds=0.5)
    monitor.add_tick_hook(lambda: ticks.append(1))

    monitor.start()
    try:
        deadline = time.monotonic() + 2
        while not calls and time.monotonic() < deadline:
            time.sleep(0.01)
        assert monitor.running
        assert monitor.get(_service())["call"] == 1
    finally:
        monitor.stop()

    assert ticks
    assert not monitor.running


def test_poller_survives_failing_probes_and_hooks():
    def failing(_service):
        raise RuntimeError("probe failed")

    monitor = ServiceStatusMonitor(failing, lambda: [_service()])
    monitor.add_tick_hook(lambda: 1 / 0)

    monitor.run_tick_hooks()
    monitor.refresh_all()


def test_overview_reads_status_from_the_monitor(monkeypatch):
    monkeypatch.setattr("app.main.pipeline.read_tail", lambda _service, tail=2000: [])
    monkeypatch.setattr("app.main.registry.list_services", lambda: [_service("svc-overview")])
    monkeypatch.setattr(
        "app.main.settings_manager.snapshot",
        lambda _services: {"preferences": {}, "service_visibility": {"svc-overview": True}},
    )
    monkeypatch.setattr("app.main.status_monitor.get", lambda service: {"cached_for": service.service_id})

    def forbidden(*_args, **_kwargs):
        raise AssertionError("overview must not probe services synchronously")

    monkeypatch.setattr("app.main.process_manager.status", forbidden)

    response = dashboard_client(app).get("/api/dashboard/overview")

    assert response.status_code == 200
    assert response.json()["services"][0]["runtime"] == {"cached_for": "svc-overview"}


def test_service_actions_invalidate_the_status_cache(monkeypatch):
    invalidated: list[str | None] = []
    service = main.registry.list_services()[0]
    monkeypatch.setattr("app.main.status_monitor.invalidate", lambda service_id=None: invalidated.append(service_id))
    monkeypatch.setattr("app.main.process_manager.stop", lambda _service: {"ok": True})

    response = dashboard_client(app).post(f"/api/services/{service.service_id}/stop")

    assert response.status_code == 200
    assert invalidated == [service.service_id]


def test_lock_creation_is_atomic_across_threads():
    manager = ServiceProcessManager()

    class SlowDict(dict):
        def get(self, key, default=None):
            value = super().get(key, default)
            time.sleep(0.01)
            return value

    manager._locks = SlowDict()
    results: list[object] = []
    threads = [threading.Thread(target=lambda: results.append(manager._lock_for("svc"))) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len({id(lock) for lock in results}) == 1


def test_dashboard_shutdown_is_graceful_before_forcing_exit():
    events: list[str] = []
    done = threading.Event()

    def force_exit(code: int) -> None:
        events.append(f"exit:{code}")
        done.set()

    thread = main._schedule_dashboard_shutdown(
        0,
        fallback_seconds=0.05,
        request_shutdown=lambda: events.append("signal"),
        force_exit=force_exit,
    )
    assert done.wait(2)
    thread.join(1)

    assert events == ["signal", "exit:0"]


def test_dashboard_shutdown_forces_exit_when_the_signal_fails():
    events: list[str] = []
    done = threading.Event()

    def broken_signal() -> None:
        raise OSError("no signal support")

    def force_exit(code: int) -> None:
        events.append(f"exit:{code}")
        done.set()

    main._schedule_dashboard_shutdown(0, fallback_seconds=5, request_shutdown=broken_signal, force_exit=force_exit)

    assert done.wait(2)
    assert events == ["exit:0"]


def test_pid_lookup_tolerates_a_missing_or_hanging_port_tool(monkeypatch):
    import subprocess

    manager = ServiceProcessManager()

    def missing_tool(*_args, **_kwargs):
        raise FileNotFoundError("lsof")

    monkeypatch.setattr("app.process_manager.subprocess.run", missing_tool)
    assert manager._pid_from_port(9) is None

    def hanging_tool(command, **_kwargs):
        raise subprocess.TimeoutExpired(command, 5)

    monkeypatch.setattr("app.process_manager.subprocess.run", hanging_tool)
    assert manager._pid_from_port(9) is None

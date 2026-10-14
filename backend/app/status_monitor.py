"""Background poller that caches service runtime status for the dashboard endpoints."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterable
from typing import Any

from .models import ServiceDefinition

StatusFn = Callable[[ServiceDefinition], dict[str, Any]]
ServicesFn = Callable[[], Iterable[ServiceDefinition]]
TickHook = Callable[[], None]


class ServiceStatusMonitor:
    """Keeps a short-lived cache of service status refreshed by a background thread.

    While the poller is not running (for example in unit tests or before the app
    lifespan starts) every read computes the status live, so callers always get
    a value and never a stale one from a previous configuration.
    """

    def __init__(
        self,
        status_fn: StatusFn,
        services_fn: ServicesFn,
        *,
        interval_seconds: float = 3.0,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._status_fn = status_fn
        self._services_fn = services_fn
        self.interval_seconds = max(0.5, float(interval_seconds))
        self._clock = clock
        self._cache: dict[str, tuple[float, int, dict[str, Any]]] = {}
        self._generation: dict[str, int] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._tick_hooks: list[TickHook] = []

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def max_age_seconds(self) -> float:
        return self.interval_seconds * 2

    def add_tick_hook(self, hook: TickHook) -> None:
        self._tick_hooks.append(hook)

    def get(self, service: ServiceDefinition) -> dict[str, Any]:
        if self.running:
            with self._lock:
                cached = self._cache.get(service.service_id)
            if cached is not None and self._clock() - cached[0] <= self.max_age_seconds:
                return dict(cached[2])
        return self.refresh(service)

    def refresh(self, service: ServiceDefinition) -> dict[str, Any]:
        with self._lock:
            generation = self._generation.get(service.service_id, 0)
        status = self._status_fn(service)
        with self._lock:
            # Drop results computed before an invalidation so that a slow poll
            # cannot overwrite the state observed after start/stop/restart.
            if self._generation.get(service.service_id, 0) == generation:
                self._cache[service.service_id] = (self._clock(), generation, dict(status))
        return status

    def invalidate(self, service_id: str | None = None) -> None:
        with self._lock:
            if service_id is None:
                for key in list(self._generation) + list(self._cache):
                    self._generation[key] = self._generation.get(key, 0) + 1
                self._cache.clear()
                return
            self._generation[service_id] = self._generation.get(service_id, 0) + 1
            self._cache.pop(service_id, None)

    def refresh_all(self) -> None:
        for service in list(self._services_fn()):
            if self._stop_event.is_set():
                return
            try:
                self.refresh(service)
            except Exception:  # noqa: BLE001 - one failing probe must not stop the poller
                self.invalidate(service.service_id)

    def run_tick_hooks(self) -> None:
        for hook in self._tick_hooks:
            try:
                hook()
            except Exception:  # noqa: BLE001 - background hooks are best effort
                continue

    def start(self) -> None:
        if self.running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="dashboard-status-poller", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=timeout)
        self._thread = None
        with self._lock:
            self._cache.clear()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self.run_tick_hooks()
            self.refresh_all()
            self._stop_event.wait(self.interval_seconds)


__all__ = ["ServiceStatusMonitor"]

"""Persistent registry of Jenkins MCP deploy destinations and their policy."""

from __future__ import annotations

import copy
import json
import re
import threading
from pathlib import Path
from typing import Any

from .fs_utils import atomic_write_json

POLICIES = ("allow", "confirm", "deny")
DEFAULT_POLICIES = ("confirm", "deny")
ENV_VAR = "JENKINS_DEMO_POLICIES"
# Same rule as the MCP (DemoPolicyRegistry): exact names, no patterns.
_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")


def normalize_registry(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Validate a registry payload and return its canonical form.

    The default policy applies to destinations missing from the list and can never
    be ``allow``: a destination that appears in Jenkins must not become launchable
    without confirmation.
    """
    source = payload or {}
    default_policy = str(source.get("default_policy") or "confirm").strip().lower()
    if default_policy not in DEFAULT_POLICIES:
        raise ValueError("default_policy must be confirm or deny.")

    raw_demos = source.get("demos") or []
    if not isinstance(raw_demos, list):
        raise ValueError("demos must be a list of {name, policy}.")
    demos: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw_demos:
        if not isinstance(item, dict):
            raise ValueError("demos must be a list of {name, policy}.")
        name = str(item.get("name") or "").strip()
        if not _NAME_RE.fullmatch(name):
            raise ValueError(
                f"Invalid destination name: {name!r}. Use the exact Jenkins value "
                "(letters, digits, _, - or ., max 64 characters)."
            )
        if name in seen:
            raise ValueError(f"Duplicate destination: {name}")
        policy = str(item.get("policy") or "").strip().lower()
        if policy not in POLICIES:
            raise ValueError(f"Invalid policy for {name}: must be allow, confirm or deny.")
        seen.add(name)
        demos.append({"name": name, "policy": policy})
    return {"default_policy": default_policy, "demos": demos}


def registry_runtime_value(registry: dict[str, Any]) -> dict[str, Any]:
    """Shape expected by the MCP and returned by its /admin/policies endpoint."""
    return {
        "default": registry["default_policy"],
        "demos": {item["name"]: item["policy"] for item in registry["demos"]},
    }


class JenkinsDemoRegistry:
    def __init__(self, state_path: Path) -> None:
        self.state_path = Path(state_path)
        self._lock = threading.RLock()
        self._registry = normalize_registry(None)
        self._load()

    def _load(self) -> None:
        if not self.state_path.exists():
            return
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return
        if isinstance(payload, dict):
            # An invalid saved registry is ignored: the defaults (every destination
            # needs confirmation) stay in place, never anything more permissive.
            try:
                self._registry = normalize_registry(payload)
            except ValueError:
                self._registry = normalize_registry(None)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._registry)

    def replace(self, payload: dict[str, Any]) -> dict[str, Any]:
        registry = normalize_registry(payload)
        with self._lock:
            self._registry = registry
            atomic_write_json(self.state_path, {"version": 1, **registry})
            return copy.deepcopy(registry)

    def runtime_value(self) -> dict[str, Any]:
        with self._lock:
            return registry_runtime_value(self._registry)

    def runtime_env(self) -> dict[str, str]:
        return {ENV_VAR: json.dumps(self.runtime_value(), ensure_ascii=True, separators=(",", ":"))}

    def classify(self, choices: list[str]) -> dict[str, Any]:
        """Compare the Jenkins choices with the registry (exact names)."""
        with self._lock:
            known = {item["name"]: item["policy"] for item in self._registry["demos"]}
            default_policy = self._registry["default_policy"]
        return {
            "choices": list(choices),
            "new": [name for name in choices if name not in known],
            "missing": [name for name in known if name not in choices],
            "effective_policies": {name: known.get(name, default_policy) for name in choices},
            "default_policy": default_policy,
        }

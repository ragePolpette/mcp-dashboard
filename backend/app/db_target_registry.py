"""Persistent registry for SQL MCP database targets."""

from __future__ import annotations

import copy
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from .secret_vault import DashboardSecretVault, LocalSecretVaultError

ALLOWED_DB_KINDS = {"sqlserver"}
ALLOWED_STATUSES = {"active", "disabled"}
ALLOWED_WRITE_POLICIES = {"allow", "approval_required", "deny"}
ALLOWED_ANONYMIZATION_MODES = {"off", "direct", "deterministic", "hybrid", "llm-strict"}
ALLOWED_ANONYMIZATION_PROVIDERS = {"none", "lmstudio", "ollama"}
DEFAULT_ALLOWED_TOOLS = ["db_target_info", "db_policy_info", "db_read", "db_write"]


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if isinstance(payload, dict):
        return payload
    return None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _clean_text(value: Any, *, fallback: str = "") -> str:
    if value is None:
        return fallback
    return str(value).strip()


def _clean_bool(value: Any, *, fallback: bool = False) -> bool:
    if value is None:
        return fallback
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return fallback


def _clean_int(value: Any, *, fallback: int, minimum: int = 1) -> int:
    if value is None or value == "":
        return fallback
    if isinstance(value, bool):
        return fallback
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(minimum, numeric)


def _default_connection_env_var(target_id: str) -> str:
    normalized = _clean_text(target_id).replace("-", "_")
    normalized = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in normalized)
    normalized = normalized.strip("_").upper()
    return f"DB_{normalized}_CONNECTION_STRING"


def _normalize_vault_ref(ref: Any, *, vault: DashboardSecretVault | None = None) -> str:
    text = _clean_text(ref)
    if not text:
        return ""
    if vault is not None:
        return vault.normalize_ref(text)
    if text.startswith("vault://"):
        return text
    return f"vault://{text}"


def _unique_text_list(values: Any, *, fallback: list[str]) -> list[str]:
    raw_values = values if isinstance(values, list) else fallback
    seen: set[str] = set()
    out: list[str] = []
    for raw in raw_values:
        text = _clean_text(raw)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _nested_value(raw: dict[str, Any], key: str, nested_key: str, fallback: Any = None) -> Any:
    if key in raw:
        value = raw.get(key)
        if value is not None:
            return value
    nested = raw.get(nested_key)
    if isinstance(nested, dict) and nested_key in {"connection", "policy", "anonymization", "limits", "state"}:
        return nested.get(key)
    return fallback


def _default_bootstrap_targets() -> list[dict[str, Any]]:
    return [
        {
            "target_id": "dev-main",
            "display_name": "Dev Main",
            "environment": "dev",
            "db_kind": "sqlserver",
            "status": "active",
            "connection": {
                "env_var": "DB_DEV_MAIN_CONNECTION_STRING",
                "vault_ref": "",
            },
            "policy": {
                "read_enabled": True,
                "write_policy": "allow",
            },
            "anonymization": {
                "enabled": False,
                "mode": "off",
                "provider": "none",
                "model": "",
            },
            "limits": {
                "max_rows": 200,
                "max_result_bytes": 262144,
            },
            "allowed_tools": DEFAULT_ALLOWED_TOOLS,
            "state": {
                "runtime_status": "seeded",
                "last_synced_at": None,
                "last_error": None,
            },
        },
        {
            "target_id": "prod-main",
            "display_name": "Prod Main",
            "environment": "prod",
            "db_kind": "sqlserver",
            "status": "active",
            "connection": {
                "env_var": "DB_PROD_MAIN_CONNECTION_STRING",
                "vault_ref": "",
            },
            "policy": {
                "read_enabled": True,
                "write_policy": "deny",
            },
            "anonymization": {
                "enabled": True,
                "mode": "hybrid",
                "provider": "lmstudio",
                "model": "google/gemma-3-4b",
            },
            "limits": {
                "max_rows": 100,
                "max_result_bytes": 131072,
            },
            "allowed_tools": DEFAULT_ALLOWED_TOOLS,
            "state": {
                "runtime_status": "seeded",
                "last_synced_at": None,
                "last_error": None,
            },
        },
    ]


class DbTargetRegistry:
    """Persistent registry and runtime exporter for SQL MCP DB targets."""

    def __init__(
        self,
        state_path: Path,
        runtime_path: Path,
        bootstrap_path: Path,
        *,
        vault: DashboardSecretVault | None = None,
    ) -> None:
        self.state_path = Path(state_path)
        self.runtime_path = Path(runtime_path)
        self.bootstrap_path = Path(bootstrap_path)
        self._vault = vault
        self._lock = threading.RLock()
        self._targets: list[dict[str, Any]] = []
        self._load()

    def _load_source_targets(self) -> list[dict[str, Any]]:
        payload = _read_json(self.state_path)
        if payload is not None:
            targets = payload.get("targets")
            if isinstance(targets, list):
                return targets

        bootstrap_payload = _read_json(self.bootstrap_path)
        if bootstrap_payload is not None and isinstance(bootstrap_payload.get("targets"), list):
            return bootstrap_payload["targets"]

        return _default_bootstrap_targets()

    def _load(self) -> None:
        with self._lock:
            self._targets = [self._normalize_target(target) for target in self._load_source_targets()]
            self._save()
            self._export_runtime()

    def _save(self) -> None:
        _write_json(
            self.state_path,
            {
                "version": 1,
                "targets": copy.deepcopy(self._targets),
            },
        )

    def _export_runtime(self) -> None:
        _write_json(self.runtime_path, self.runtime_snapshot())

    def _merge_section(
        self,
        raw: dict[str, Any],
        existing: dict[str, Any],
        section: str,
    ) -> dict[str, Any]:
        raw_section = raw.get(section)
        merged: dict[str, Any] = {}
        if isinstance(existing.get(section), dict):
            merged.update(copy.deepcopy(existing[section]))
        if isinstance(raw_section, dict):
            merged.update(raw_section)
        return merged

    def _normalize_target(
        self,
        raw: dict[str, Any],
        *,
        existing: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        source = copy.deepcopy(existing or {})
        source.update(raw)

        target_id = _clean_text(source.get("target_id") or (existing or {}).get("target_id"))
        if not target_id:
            raise ValueError("target_id is required.")

        display_name = _clean_text(source.get("display_name") or (existing or {}).get("display_name"), fallback=target_id)
        environment = _clean_text(source.get("environment") or (existing or {}).get("environment"), fallback="dev").lower()
        if not environment:
            raise ValueError("environment is required.")

        db_kind = _clean_text(source.get("db_kind") or (existing or {}).get("db_kind"), fallback="sqlserver").lower()
        if db_kind not in ALLOWED_DB_KINDS:
            raise ValueError("db_kind must be sqlserver.")

        status = _clean_text(source.get("status") or (existing or {}).get("status"), fallback="active").lower()
        if status not in ALLOWED_STATUSES:
            raise ValueError("status must be active or disabled.")

        connection_existing = (existing or {}).get("connection", {}) if isinstance((existing or {}).get("connection"), dict) else {}
        connection_raw = self._merge_section(source, existing or {}, "connection")
        connection_env_var = _clean_text(
            connection_raw.get("env_var")
            or source.get("connection_env_var")
            or connection_existing.get("env_var")
            or _default_connection_env_var(target_id),
        )
        connection_vault_ref = _normalize_vault_ref(
            connection_raw.get("vault_ref")
            or source.get("connection_vault_ref")
            or connection_existing.get("vault_ref"),
            vault=self._vault,
        )

        policy_existing = (existing or {}).get("policy", {}) if isinstance((existing or {}).get("policy"), dict) else {}
        policy_raw = self._merge_section(source, existing or {}, "policy")
        read_enabled = _clean_bool(
            policy_raw.get("read_enabled")
            if "read_enabled" in policy_raw
            else source.get("read_enabled", policy_existing.get("read_enabled", True)),
            fallback=True,
        )
        write_policy = _clean_text(
            policy_raw.get("write_policy")
            or source.get("write_policy")
            or policy_existing.get("write_policy"),
            fallback="deny",
        ).lower()
        if write_policy not in ALLOWED_WRITE_POLICIES:
            raise ValueError("write_policy must be allow, approval_required, or deny.")
        if environment == "prod":
            write_policy = "deny"

        anonymization_existing = (
            existing or {}
        ).get("anonymization", {}) if isinstance((existing or {}).get("anonymization"), dict) else {}
        anonymization_raw = self._merge_section(source, existing or {}, "anonymization")
        anonymization_enabled = _clean_bool(
            anonymization_raw.get("enabled")
            if "enabled" in anonymization_raw
            else source.get("anonymization_enabled", anonymization_existing.get("enabled", False)),
            fallback=False,
        )
        anonymization_mode = _clean_text(
            anonymization_raw.get("mode")
            or source.get("anonymization_mode")
            or anonymization_existing.get("mode"),
            fallback="off",
        ).lower()
        anonymization_provider = _clean_text(
            anonymization_raw.get("provider")
            or source.get("anonymization_provider")
            or anonymization_existing.get("provider"),
            fallback="none",
        ).lower()
        anonymization_model = _clean_text(
            anonymization_raw.get("model")
            or source.get("anonymization_model")
            or anonymization_existing.get("model"),
        )

        limits_existing = (existing or {}).get("limits", {}) if isinstance((existing or {}).get("limits"), dict) else {}
        limits_raw = self._merge_section(source, existing or {}, "limits")
        max_rows = _clean_int(
            limits_raw.get("max_rows") if "max_rows" in limits_raw else source.get("max_rows", limits_existing.get("max_rows", 100)),
            fallback=100,
            minimum=1,
        )
        max_result_bytes = _clean_int(
            limits_raw.get("max_result_bytes")
            if "max_result_bytes" in limits_raw
            else source.get("max_result_bytes", limits_existing.get("max_result_bytes", 131072)),
            fallback=131072,
            minimum=1,
        )

        allowed_tools = _unique_text_list(
            source.get("allowed_tools") or (existing or {}).get("allowed_tools"),
            fallback=DEFAULT_ALLOWED_TOOLS,
        )

        state_existing = (existing or {}).get("state", {}) if isinstance((existing or {}).get("state"), dict) else {}
        state_raw = self._merge_section(source, existing or {}, "state")
        state = copy.deepcopy(state_existing)
        state.update(state_raw)
        state.setdefault("runtime_status", "ready" if status == "active" else "disabled")
        state.setdefault("last_synced_at", None)
        state.setdefault("last_error", None)

        if anonymization_enabled:
            if anonymization_mode not in ALLOWED_ANONYMIZATION_MODES:
                raise ValueError("Invalid anonymization mode.")
            if anonymization_mode == "off":
                raise ValueError("anonymization mode cannot be off when enabled.")
            if anonymization_provider not in ALLOWED_ANONYMIZATION_PROVIDERS or anonymization_provider == "none":
                raise ValueError("anonymization provider is required when anonymization is enabled.")
            if not anonymization_model:
                raise ValueError("anonymization model is required when anonymization is enabled.")
        else:
            anonymization_mode = "off"
            anonymization_provider = "none"
            anonymization_model = ""

        if environment == "prod":
            anonymization_enabled = True
            if anonymization_mode == "off":
                anonymization_mode = "hybrid"
            if anonymization_provider == "none" or not anonymization_model:
                raise ValueError("prod targets require anonymization provider and model.")

        if write_policy == "deny" and "db_write" in allowed_tools:
            allowed_tools = [tool for tool in allowed_tools if tool != "db_write"]

        return {
            "target_id": target_id,
            "display_name": display_name,
            "environment": environment,
            "db_kind": db_kind,
            "status": status,
            "connection": {
                "env_var": connection_env_var,
                "vault_ref": connection_vault_ref,
            },
            "policy": {
                "read_enabled": read_enabled,
                "write_policy": write_policy,
                "write_enabled": write_policy == "allow",
            },
            "anonymization": {
                "enabled": anonymization_enabled,
                "mode": anonymization_mode,
                "provider": anonymization_provider,
                "model": anonymization_model,
            },
            "limits": {
                "max_rows": max_rows,
                "max_result_bytes": max_result_bytes,
            },
            "allowed_tools": allowed_tools,
            "state": state,
        }

    def _target_index(self, target_id: str) -> int:
        for idx, target in enumerate(self._targets):
            if target.get("target_id") == target_id:
                return idx
        return -1

    def _connection_status(self, target: dict[str, Any]) -> dict[str, Any]:
        connection = target.get("connection", {}) if isinstance(target.get("connection"), dict) else {}
        ref = _clean_text(connection.get("vault_ref"))
        if not ref:
            return {
                "is_set": False,
                "is_ready": False,
                "source": "none",
                "status": "unset",
                "status_message": "Connessione non ancora collegata a un vault ref.",
            }

        if self._vault is None:
            return {
                "is_set": True,
                "is_ready": False,
                "source": "vault",
                "status": "vault_unavailable",
                "vault_ref": ref,
                "status_message": "Vault non disponibile nel backend corrente.",
            }

        vault_status = self._vault.status()
        if not vault_status["initialized"]:
            return {
                "is_set": True,
                "is_ready": False,
                "source": "vault",
                "status": "vault_uninitialized",
                "vault_ref": ref,
                "status_message": "Vault non inizializzato.",
            }
        if not vault_status["unlocked"]:
            return {
                "is_set": True,
                "is_ready": False,
                "source": "vault",
                "status": "vault_locked",
                "vault_ref": ref,
                "status_message": "Vault bloccato: sbloccalo per usare il ref.",
            }
        try:
            self._vault.resolve_secret(ref)
        except LocalSecretVaultError as exc:
            return {
                "is_set": True,
                "is_ready": False,
                "source": "vault",
                "status": "vault_ref_invalid",
                "vault_ref": ref,
                "status_message": exc.message,
            }
        return {
            "is_set": True,
            "is_ready": True,
            "source": "vault",
            "status": "ready",
            "vault_ref": ref,
            "status_message": "Vault ref valido e risolvibile.",
        }

    def _public_target(self, target: dict[str, Any]) -> dict[str, Any]:
        connection = copy.deepcopy(target.get("connection", {}))
        connection_status = self._connection_status(target)
        policy = copy.deepcopy(target.get("policy", {}))
        anonymization = copy.deepcopy(target.get("anonymization", {}))
        limits = copy.deepcopy(target.get("limits", {}))
        allowed_tools = copy.deepcopy(target.get("allowed_tools", []))
        runtime_allowed_tools = [
            tool
            for tool in allowed_tools
            if tool != "db_write" or policy.get("write_policy") == "allow"
        ]
        if target.get("status") != "active":
            runtime_allowed_tools = [tool for tool in runtime_allowed_tools if tool != "db_write"]

        return {
            "target_id": target["target_id"],
            "display_name": target["display_name"],
            "environment": target["environment"],
            "db_kind": target["db_kind"],
            "status": target["status"],
            "connection": {
                **connection,
                **connection_status,
            },
            "policy": {
                **policy,
                "effective_write_enabled": policy.get("write_policy") == "allow" and target["status"] == "active",
            },
            "anonymization": anonymization,
            "limits": limits,
            "allowed_tools": allowed_tools,
            "runtime": {
                "write_enabled": policy.get("write_policy") == "allow" and target["status"] == "active",
                "allowed_tools": runtime_allowed_tools,
                "anonymization_required": target["environment"] == "prod",
            },
            "state": copy.deepcopy(target.get("state", {})),
        }

    def list_targets(self) -> list[dict[str, Any]]:
        with self._lock:
            return [copy.deepcopy(self._public_target(target)) for target in self._targets]

    def get_target(self, target_id: str) -> dict[str, Any] | None:
        with self._lock:
            idx = self._target_index(target_id)
            if idx < 0:
                return None
            return copy.deepcopy(self._public_target(self._targets[idx]))

    def create_target(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            target_id = _clean_text(payload.get("target_id"))
            if not target_id:
                raise ValueError("target_id is required.")
            if self._target_index(target_id) >= 0:
                raise ValueError(f"Duplicate target_id: {target_id}")

            target = self._normalize_target(payload)
            self._targets.append(target)
            self._save()
            self._export_runtime()
            return copy.deepcopy(self._public_target(target))

    def update_target(self, target_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            idx = self._target_index(target_id)
            if idx < 0:
                raise ValueError(f"Unknown target_id: {target_id}")
            current = self._targets[idx]
            merged = copy.deepcopy(current)
            merged.update(payload)
            merged["target_id"] = target_id
            target = self._normalize_target(merged, existing=current)
            self._targets[idx] = target
            self._save()
            self._export_runtime()
            return copy.deepcopy(self._public_target(target))

    def delete_target(self, target_id: str) -> dict[str, Any]:
        with self._lock:
            idx = self._target_index(target_id)
            if idx < 0:
                raise ValueError(f"Unknown target_id: {target_id}")
            target = self._targets.pop(idx)
            self._save()
            self._export_runtime()
            return copy.deepcopy(self._public_target(target))

    def runtime_snapshot(self) -> dict[str, Any]:
        with self._lock:
            targets: list[dict[str, Any]] = []
            for target in self._targets:
                policy = target.get("policy", {})
                runtime_allowed_tools = [
                    tool
                    for tool in target.get("allowed_tools", [])
                    if tool != "db_write" or policy.get("write_policy") == "allow"
                ]
                if target.get("status") != "active":
                    runtime_allowed_tools = [tool for tool in runtime_allowed_tools if tool != "db_write"]
                targets.append(
                    {
                        "target_id": target["target_id"],
                        "display_name": target["display_name"],
                        "environment": target["environment"],
                        "db_kind": target["db_kind"],
                        "status": target["status"],
                        "connection_env_var": target.get("connection", {}).get("env_var", ""),
                        "connection_vault_ref": target.get("connection", {}).get("vault_ref", ""),
                        "read_enabled": bool(policy.get("read_enabled", True)),
                        "write_enabled": policy.get("write_policy") == "allow" and target["status"] == "active",
                        "write_policy": policy.get("write_policy", "deny"),
                        "anonymization_enabled": bool(target.get("anonymization", {}).get("enabled", False)),
                        "anonymization_mode": target.get("anonymization", {}).get("mode", "off"),
                        "anonymization_provider": target.get("anonymization", {}).get("provider", "none"),
                        "anonymization_model": target.get("anonymization", {}).get("model", ""),
                        "max_rows": target.get("limits", {}).get("max_rows", 100),
                        "max_result_bytes": target.get("limits", {}).get("max_result_bytes", 131072),
                        "allowed_tools": runtime_allowed_tools,
                        "state": copy.deepcopy(target.get("state", {})),
                    }
                )

            payload = {
                "version": 1,
                "generated_at": datetime.now().astimezone().isoformat(),
                "target_count": len(targets),
                "targets": targets,
            }
            return payload

    def runtime_env(self) -> dict[str, str]:
        with self._lock:
            env_overrides: dict[str, str] = {
                "TARGETS_FILE": str(self.runtime_path),
            }
            if self._vault is None:
                return env_overrides

            for target in self._targets:
                if target.get("status") != "active":
                    continue
                connection = target.get("connection", {})
                if not isinstance(connection, dict):
                    continue
                env_var = _clean_text(connection.get("env_var"))
                vault_ref = _clean_text(connection.get("vault_ref"))
                if not env_var or not vault_ref:
                    continue
                try:
                    env_overrides[env_var] = self._vault.resolve_secret(vault_ref)
                except LocalSecretVaultError:
                    continue
            return env_overrides

    def secret_ref_usage(self) -> dict[str, list[dict[str, str]]]:
        usage: dict[str, list[dict[str, str]]] = {}
        with self._lock:
            for target in self._targets:
                connection = target.get("connection", {})
                if not isinstance(connection, dict):
                    continue
                vault_ref = _clean_text(connection.get("vault_ref"))
                if not vault_ref:
                    continue
                usage.setdefault(vault_ref, []).append(
                    {
                        "target_id": target["target_id"],
                        "field_id": "connection",
                    }
                )
        return usage


__all__ = ["DbTargetRegistry"]

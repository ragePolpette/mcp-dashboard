"""Persistent service options store and validation."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from .models import ServiceDefinition, ServiceOptionDefinition
from .secret_vault import DashboardSecretVault, LocalSecretVaultError


class ServiceOptionsManager:
    """Stores dashboard-configured options and maps them to env vars."""

    def __init__(self, state_path: Path, vault: DashboardSecretVault | None = None):
        self.state_path = state_path
        self._vault = vault
        self._lock = threading.Lock()
        self._state: dict[str, dict[str, Any]] = {}
        self._secret_state: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self.state_path.exists():
            self._state = {}
            return
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            self._state = {}
            return
        services = payload.get("services") if isinstance(payload, dict) else {}
        if not isinstance(services, dict):
            self._state = {}
            return
        out: dict[str, dict[str, Any]] = {}
        for service_id, values in services.items():
            if isinstance(values, dict):
                out[str(service_id)] = dict(values)
        self._state = out

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"services": self._state}
        self.state_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def _normalize_value(self, option: ServiceOptionDefinition, value: Any) -> Any:
        kind = option.kind
        if kind == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in {"true", "1", "yes", "on"}:
                    return True
                if lowered in {"false", "0", "no", "off"}:
                    return False
            if isinstance(value, (int, float)):
                return bool(value)
            raise ValueError(f"Invalid boolean value for {option.option_id}")

        if kind == "integer":
            if isinstance(value, bool):
                raise ValueError(f"Invalid integer value for {option.option_id}")
            try:
                return int(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid integer value for {option.option_id}") from exc

        if kind in {"string", "select"}:
            text = "" if value is None else str(value)
            if kind == "select" and option.allowed_values and text not in option.allowed_values:
                raise ValueError(f"Invalid option value for {option.option_id}")
            return text

        return value

    def _is_set(self, option: ServiceOptionDefinition, value: Any) -> bool:
        if value is None:
            return False
        if option.kind == "boolean":
            return True
        if option.kind == "integer":
            return True
        if option.kind in {"string", "select"}:
            return bool(str(value).strip())
        return True

    def _persisted_secret_binding(self, service_id: str, option: ServiceOptionDefinition) -> dict[str, Any] | None:
        service_state = self._state.get(service_id, {})
        raw = service_state.get(option.option_id)
        if not isinstance(raw, dict):
            return None
        if raw.get("source") != "vault":
            return None
        ref = raw.get("ref")
        if not isinstance(ref, str) or not ref.strip():
            return None
        return {"source": "vault", "ref": ref}

    def _secret_binding_info(self, service_id: str, option: ServiceOptionDefinition) -> dict[str, Any]:
        secret_state = self._secret_state.get(service_id, {})
        if option.option_id in secret_state and self._is_set(option, secret_state[option.option_id]):
            return {
                "source": "session",
                "is_set": True,
                "is_ready": True,
                "vault_ref": None,
                "status_message": "Valore presente solo nella memoria della dashboard corrente.",
            }

        binding = self._persisted_secret_binding(service_id, option)
        if binding is None:
            return {
                "source": "none",
                "is_set": False,
                "is_ready": False,
                "vault_ref": None,
                "status_message": "Valore non impostato.",
            }

        if self._vault is None:
            return {
                "source": "vault",
                "is_set": True,
                "is_ready": False,
                "vault_ref": binding["ref"],
                "status_message": "Vault non disponibile nel backend corrente.",
            }

        vault_status = self._vault.status()
        if not vault_status["initialized"]:
            return {
                "source": "vault",
                "is_set": True,
                "is_ready": False,
                "vault_ref": binding["ref"],
                "status_message": "Vault non inizializzato.",
            }
        if not vault_status["unlocked"]:
            return {
                "source": "vault",
                "is_set": True,
                "is_ready": False,
                "vault_ref": binding["ref"],
                "status_message": "Vault bloccato: sbloccalo per usare il riferimento.",
            }
        try:
            self._vault.resolve_secret(binding["ref"])
        except LocalSecretVaultError as exc:
            return {
                "source": "vault",
                "is_set": True,
                "is_ready": False,
                "vault_ref": binding["ref"],
                "status_message": exc.message,
            }
        return {
            "source": "vault",
            "is_set": True,
            "is_ready": True,
            "vault_ref": binding["ref"],
            "status_message": "Riferimento valido risolto dal vault locale.",
        }

    def list_options(self, service: ServiceDefinition) -> list[dict[str, Any]]:
        control = service.control
        if control is None:
            return []

        with self._lock:
            out: list[dict[str, Any]] = []
            for option in control.options:
                if option.secret:
                    binding = self._secret_binding_info(service.service_id, option)
                    out.append(
                        {
                            "id": option.option_id,
                            "label": option.label,
                            "type": option.kind,
                            "description": option.description,
                            "required": option.required,
                            "secret": option.secret,
                            "allowed_values": option.allowed_values,
                            "default": option.default,
                            "is_set": binding["is_set"],
                            "is_ready": binding["is_ready"],
                            "value": None,
                            "secret_source": binding["source"],
                            "vault_ref": binding["vault_ref"],
                            "status_message": binding["status_message"],
                        }
                    )
                    continue

                service_state = self._state.get(service.service_id, {})
                current = service_state.get(option.option_id, option.default)
                normalized = self._normalize_value(option, current)
                is_set = self._is_set(option, normalized)
                out.append(
                    {
                        "id": option.option_id,
                        "label": option.label,
                        "type": option.kind,
                        "description": option.description,
                        "required": option.required,
                        "secret": option.secret,
                        "allowed_values": option.allowed_values,
                        "default": option.default,
                        "is_set": is_set,
                        "value": normalized,
                    }
                )
            return out

    def _update_secret_option(
        self,
        service_id: str,
        option: ServiceOptionDefinition,
        raw: Any,
        service_state: dict[str, Any],
        secret_state: dict[str, Any],
    ) -> None:
        if isinstance(raw, dict):
            source = str(raw.get("source") or "").strip().lower()
            if source == "vault":
                if self._vault is None:
                    raise ValueError(f"Vault not available for {option.option_id}")
                ref_raw = raw.get("ref")
                if ref_raw is None or not str(ref_raw).strip():
                    raise ValueError(f"Missing vault reference for {option.option_id}")
                service_state[option.option_id] = {
                    "source": "vault",
                    "ref": self._vault.normalize_ref(str(ref_raw)),
                }
                secret_state.pop(option.option_id, None)
                return
            if source == "session":
                value = raw.get("value")
                if value is None or (isinstance(value, str) and not value.strip()):
                    if option.option_id in secret_state:
                        service_state.pop(option.option_id, None)
                        return
                    raise ValueError(f"Missing session value for {option.option_id}")
                normalized = self._normalize_value(option, value)
                secret_state[option.option_id] = normalized
                service_state.pop(option.option_id, None)
                return
            if source == "clear":
                service_state.pop(option.option_id, None)
                secret_state.pop(option.option_id, None)
                return

        if raw is None:
            return
        if isinstance(raw, str) and not raw.strip():
            return
        normalized = self._normalize_value(option, raw)
        secret_state[option.option_id] = normalized
        service_state.pop(option.option_id, None)

    def update_options(self, service: ServiceDefinition, raw_values: dict[str, Any]) -> list[dict[str, Any]]:
        control = service.control
        if control is None:
            raise ValueError(f"Control not configured for service {service.service_id}")

        options = {opt.option_id: opt for opt in control.options}
        with self._lock:
            service_state = dict(self._state.get(service.service_id, {}))
            secret_state = dict(self._secret_state.get(service.service_id, {}))
            for key, raw in raw_values.items():
                option = options.get(key)
                if option is None:
                    continue

                if option.secret:
                    self._update_secret_option(service.service_id, option, raw, service_state, secret_state)
                    continue

                normalized = self._normalize_value(option, raw)
                service_state[key] = normalized

            for option in control.options:
                if option.secret:
                    session_value = secret_state.get(option.option_id)
                    is_set = self._is_set(option, session_value)
                    if not is_set:
                        persisted = service_state.get(option.option_id)
                        is_set = isinstance(persisted, dict) and persisted.get("source") == "vault" and bool(persisted.get("ref"))
                    if option.required and not is_set:
                        raise ValueError(f"Missing required option {option.option_id}")
                    continue

                val = service_state.get(option.option_id, option.default)
                normalized = self._normalize_value(option, val)
                if option.required and (normalized is None or (isinstance(normalized, str) and not normalized.strip())):
                    raise ValueError(f"Missing required option {option.option_id}")
                service_state[option.option_id] = normalized

            self._state[service.service_id] = service_state
            if secret_state:
                self._secret_state[service.service_id] = secret_state
            else:
                self._secret_state.pop(service.service_id, None)
            self._save()

        return self.list_options(service)

    def options_env(self, service: ServiceDefinition) -> dict[str, str]:
        control = service.control
        if control is None:
            return {}

        with self._lock:
            out: dict[str, str] = {}
            service_state = self._state.get(service.service_id, {})
            secret_state = self._secret_state.get(service.service_id, {})
            for option in control.options:
                if option.secret:
                    if option.option_id in secret_state and self._is_set(option, secret_state[option.option_id]):
                        out[option.env_var] = str(secret_state[option.option_id])
                        continue

                    binding = service_state.get(option.option_id)
                    if isinstance(binding, dict) and binding.get("source") == "vault" and binding.get("ref"):
                        if self._vault is None:
                            raise ValueError(f"Vault not available for option {option.option_id}")
                        try:
                            out[option.env_var] = self._vault.resolve_secret(str(binding["ref"]))
                        except LocalSecretVaultError as exc:
                            raise ValueError(f"{option.label or option.option_id}: {exc.message}") from exc
                        continue

                    continue

                value = service_state.get(option.option_id, option.default)
                normalized = self._normalize_value(option, value)
                if normalized is None:
                    continue
                if option.kind == "boolean":
                    out[option.env_var] = "true" if bool(normalized) else "false"
                else:
                    out[option.env_var] = str(normalized)
            return out

    def missing_required_options(self, service: ServiceDefinition) -> list[str]:
        control = service.control
        if control is None:
            return []

        missing: list[str] = []
        with self._lock:
            service_state = self._state.get(service.service_id, {})
            secret_state = self._secret_state.get(service.service_id, {})
            for option in control.options:
                if not option.required:
                    continue
                if option.secret:
                    if option.option_id in secret_state and self._is_set(option, secret_state[option.option_id]):
                        continue
                    binding = service_state.get(option.option_id)
                    if isinstance(binding, dict) and binding.get("source") == "vault" and binding.get("ref"):
                        continue
                    missing.append(option.label or option.option_id)
                    continue

                value = service_state.get(option.option_id, option.default)
                normalized = self._normalize_value(option, value)
                if not self._is_set(option, normalized):
                    missing.append(option.label or option.option_id)
        return missing

    def scrub_persisted_secrets(self, services: list[ServiceDefinition]) -> bool:
        changed = False
        with self._lock:
            for service in services:
                control = service.control
                if control is None:
                    continue

                secret_ids = {option.option_id for option in control.options if option.secret}
                if not secret_ids:
                    continue

                service_state = self._state.get(service.service_id)
                if not service_state:
                    continue

                sanitized: dict[str, Any] = {}
                service_changed = False
                for key, value in service_state.items():
                    if key not in secret_ids:
                        sanitized[key] = value
                        continue
                    if isinstance(value, dict) and value.get("source") == "vault" and isinstance(value.get("ref"), str):
                        sanitized[key] = value
                        continue
                    service_changed = True

                if not service_changed:
                    continue

                changed = True
                if sanitized:
                    self._state[service.service_id] = sanitized
                else:
                    self._state.pop(service.service_id, None)

            if changed:
                self._save()

        return changed

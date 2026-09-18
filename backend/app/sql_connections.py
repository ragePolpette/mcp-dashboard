"""SQL-authentication profiles stored only as encrypted vault connection strings."""
from __future__ import annotations

import hashlib
import re
from typing import Any



def parse_connection_string(value: str) -> dict[str, str]:
    """Read standard SqlClient strings, including doubled quoted delimiters."""
    result: dict[str, str] = {}
    index = 0
    while index < len(value):
        while index < len(value) and (value[index].isspace() or value[index] == ";"):
            index += 1
        if index == len(value):
            break
        end = value.find("=", index)
        if end < 0:
            raise ValueError("Formato della connessione esistente non supportato dal modulo.")
        key = value[index:end].strip().lower()
        index = end + 1
        while index < len(value) and value[index].isspace():
            index += 1
        if index < len(value) and value[index] in "\"'":
            quote = value[index]
            index += 1
            chars = []
            closed = False
            while index < len(value):
                char = value[index]
                index += 1
                if char == quote:
                    if index < len(value) and value[index] == quote:
                        chars.append(quote)
                        index += 1
                    else:
                        closed = True
                        break
                else:
                    chars.append(char)
            if not closed:
                raise ValueError("Formato della connessione esistente non supportato dal modulo.")
            text = "".join(chars)
            while index < len(value) and value[index].isspace():
                index += 1
            if index < len(value) and value[index] != ";":
                raise ValueError("Formato della connessione esistente non supportato dal modulo.")
        else:
            end = value.find(";", index)
            if end < 0:
                end = len(value)
            text = value[index:end].strip()
            index = end
        result[key] = text
        if index < len(value):
            index += 1
    return result


def validate_connection_string(value: str) -> None:
    """Validate the minimum SqlClient shape without returning the secret."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("La connection string del Vault e' vuota.")
    values = parse_connection_string(value)
    endpoint = _get(values, "server", "data source", "address", "addr", "network address")
    if not endpoint:
        raise ValueError("La connection string del Vault deve includere Server (o Data Source).")


def _get(values: dict[str, str], *keys: str, default: str = "") -> str:
    return next((values[key] for key in keys if key in values), default)


def _profile(values: dict[str, str]) -> dict[str, Any]:
    # Existing custom DSNs remain available through the advanced vault binding.
    known = {"server", "data source", "address", "addr", "network address", "database", "initial catalog",
             "user id", "uid", "user", "password", "pwd", "encrypt", "trustservercertificate", "trust server certificate"}
    if set(values) - known:
        raise ValueError("Connessione avanzata: modifica il segreto nel Vault per conservarne tutte le opzioni.")
    for key in ("encrypt", "trustservercertificate", "trust server certificate"):
        if key in values and values[key].lower() not in {"true", "false", "yes", "no"}:
            raise ValueError("Opzioni TLS avanzate: modifica il segreto nel Vault per conservarle.")
    endpoint = _get(values, "server", "data source", "address", "addr", "network address")
    server, separator, port = endpoint.rpartition(",")
    if not separator:
        server, port = endpoint, ""
    if port and not port.isdigit():
        raise ValueError("Porta non supportata nella connessione esistente.")
    return {
        "server": server,
        "port": int(port) if port else None,
        "database": _get(values, "database", "initial catalog"),
        "username": _get(values, "user id", "uid", "user"),
        "encrypt": _get(values, "encrypt", default="true").lower() in {"true", "yes", "mandatory", "strict"},
        "trust_server_certificate": _get(values, "trustservercertificate", "trust server certificate", default="false").lower() in {"true", "yes"},
        "password_set": bool(_get(values, "password", "pwd")),
    }


def _require_unlocked(vault) -> None:
    status = vault.status()
    if not status["initialized"] or not status["unlocked"]:
        raise ValueError("Inizializza e sblocca il Vault prima di configurare una connessione.")


def _existing_values(target, vault) -> dict[str, str]:
    ref = target.get("connection", {}).get("vault_ref", "")
    if not ref:
        return {}
    # Missing placeholder references are normal for newly seeded targets.
    if ref not in {entry["ref"] for entry in vault.list_entries()}:
        return {}
    return parse_connection_string(vault.resolve_secret(ref))


def read_connection_profile(target, vault) -> dict[str, Any]:
    _require_unlocked(vault)
    return _profile(_existing_values(target, vault))


def _text(payload, key, *, required=True, trim=True):
    value = payload.get(key, "")
    if not isinstance(value, str) or len(value) > 4096 or any(ord(c) < 32 for c in value):
        raise ValueError(f"Campo non valido: {key}.")
    if trim:
        value = value.strip()
    if required and not value:
        raise ValueError(f"Campo obbligatorio: {key}.")
    return value


def build_connection_string(payload, previous_values=None) -> str:
    if not isinstance(payload, dict):
        raise ValueError("Configurazione della connessione non valida.")
    server = _text(payload, "server")
    if re.search(r"[\s,;=\"']", server):
        raise ValueError("Inserisci solo il nome o indirizzo del server; usa il campo Porta separato.")
    database = _text(payload, "database")
    username = _text(payload, "username")
    password = _text(payload, "password", required=False, trim=False)
    if not password:
        password = _get(previous_values or {}, "password", "pwd")
    if not password:
        raise ValueError("Password obbligatoria per una nuova connessione.")
    port = payload.get("port")
    if port not in (None, ""):
        if isinstance(port, bool) or not str(port).isdigit() or not 1 <= int(port) <= 65535:
            raise ValueError("La porta deve essere un intero tra 1 e 65535.")
        if "\\" in server:
            raise ValueError("Specifica un'istanza nominata oppure una porta, non entrambe.")
        server += f",{int(port)}"
    encrypt = payload.get("encrypt", True)
    trust = payload.get("trust_server_certificate", False)
    if not isinstance(encrypt, bool) or not isinstance(trust, bool):
        raise ValueError("Opzioni TLS non valide.")

    def quote(text):
        return '"' + text.replace('"', '""') + '"'

    return ";".join([
        f"Server={quote(server)}", f"Database={quote(database)}", f"User Id={quote(username)}",
        f"Password={quote(password)}", f"Encrypt={str(encrypt).lower()}",
        f"TrustServerCertificate={str(trust).lower()}",
    ]) + ";"


def save_connection_profile(target, payload, vault, registry):
    _require_unlocked(vault)
    previous = _existing_values(target, vault)
    _profile(previous)  # Do not silently discard custom DSN options.
    connection_string = build_connection_string(payload, previous)
    # Own reference per target: editing one target never overwrites a shared secret.
    digest = hashlib.sha256(target["target_id"].encode()).hexdigest()
    ref = f"vault://db.connection.{digest}"
    previous_secret = None
    if ref in {entry["ref"] for entry in vault.list_entries()}:
        previous_secret = vault.resolve_secret(ref)
    vault.upsert_secret(ref, connection_string)
    try:
        registry.update_target(target["target_id"], {"connection": {"vault_ref": ref}})
    except Exception:
        if previous_secret is None:
            vault.delete_secret(ref)
        else:
            vault.upsert_secret(ref, previous_secret)
        raise
    return {"saved": True, "password_set": True, "vault_ref": ref}

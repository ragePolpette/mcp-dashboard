"""Reference helpers for the local secret vault."""

from __future__ import annotations

import re

from .errors import LocalSecretVaultError

REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
VAULT_SCHEME = "vault://"


def normalize_ref(ref: str) -> str:
    text = str(ref or "").strip()
    if not text:
        raise LocalSecretVaultError("E_REF_INVALID", "Vault reference is required.")
    if not text.startswith(VAULT_SCHEME):
        text = f"{VAULT_SCHEME}{text}"
    name = text[len(VAULT_SCHEME) :].strip()
    if not name or not REF_PATTERN.fullmatch(name):
        raise LocalSecretVaultError("E_REF_INVALID", "Vault reference contains unsupported characters.")
    return f"{VAULT_SCHEME}{name}"


def ref_name(ref: str) -> str:
    return normalize_ref(ref)[len(VAULT_SCHEME) :]


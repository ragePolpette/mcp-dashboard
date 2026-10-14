"""Reference helpers for the local secret vault."""

from __future__ import annotations

import re

from .errors import LocalSecretVaultError

REF_MAX_LENGTH = 128
REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*(?:\.[A-Za-z0-9_-]+)*$")
LEGACY_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
VAULT_SCHEME = "vault://"


def _ref_body(ref: str) -> str:
    text = str(ref or "").strip()
    if not text:
        raise LocalSecretVaultError("E_REF_INVALID", "Vault reference is required.")
    if text.startswith(VAULT_SCHEME):
        text = text[len(VAULT_SCHEME) :].strip()
    return text


def _invalid_ref_error() -> LocalSecretVaultError:
    return LocalSecretVaultError(
        "E_REF_INVALID",
        "Invalid vault reference name. Use letters, digits, underscore or hyphen, "
        "with single dots as separators; no spaces, slashes or colons. Example: db.prod.connection_string",
    )


def normalize_ref(ref: str) -> str:
    name = _ref_body(ref)
    if not name or len(name) > REF_MAX_LENGTH or not REF_PATTERN.fullmatch(name):
        raise _invalid_ref_error()
    return f"{VAULT_SCHEME}{name}"


def normalize_legacy_ref(ref: str) -> str:
    """Normalize a reference created before the strict naming rules.

    Such names may contain slashes or colons. Callers must only accept them for
    entries that already exist in the vault metadata.
    """
    name = _ref_body(ref)
    if not name or not LEGACY_REF_PATTERN.fullmatch(name) or ".." in name.split("/"):
        raise _invalid_ref_error()
    return f"{VAULT_SCHEME}{name}"


def ref_name(ref: str) -> str:
    return normalize_ref(ref)[len(VAULT_SCHEME) :]

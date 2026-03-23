"""Errors for the local secret vault."""

from __future__ import annotations


class LocalSecretVaultError(Exception):
    """Structured error surfaced by the local secret vault."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


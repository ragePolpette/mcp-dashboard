"""Crypto helpers for the local secret vault."""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .errors import LocalSecretVaultError

STORE_VERSION = 1
KEY_BYTES = 32
NONCE_BYTES = 12


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


def require_passphrase(passphrase: str) -> None:
    if not isinstance(passphrase, str) or len(passphrase) < 12:
        raise LocalSecretVaultError(
            "E_PASSPHRASE_INVALID",
            "Passphrase must be at least 12 characters.",
        )


def derive_kek(passphrase: str, salt: bytes) -> bytes:
    require_passphrase(passphrase)
    kdf = Scrypt(salt=salt, length=KEY_BYTES, n=1 << 15, r=8, p=1)
    return kdf.derive(passphrase.encode("utf-8"))


def _aes_encrypt(key: bytes, plaintext: bytes, aad: bytes) -> dict[str, bytes]:
    nonce = os.urandom(NONCE_BYTES)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, aad)
    return {"nonce": nonce, "ciphertext": ciphertext}


def _aes_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes) -> bytes:
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ciphertext, aad)
    except Exception as exc:  # pragma: no cover - cryptography raises multiple concrete types
        raise LocalSecretVaultError(
            "E_DECRYPT_FAILED",
            "Secret store could not be decrypted with the provided passphrase.",
        ) from exc


def create_key_envelope(passphrase: str) -> tuple[dict[str, str | int], bytes]:
    require_passphrase(passphrase)
    dek = os.urandom(KEY_BYTES)
    salt = os.urandom(16)
    kek = derive_kek(passphrase, salt)
    aad = f"local-secret-vault:kek:v{STORE_VERSION}".encode("utf-8")
    wrapped = _aes_encrypt(kek, dek, aad)
    envelope = {
        "version": STORE_VERSION,
        "kdf": "scrypt",
        "salt": _b64(salt),
        "nonce": _b64(wrapped["nonce"]),
        "wrapped_dek": _b64(wrapped["ciphertext"]),
    }
    return envelope, dek


def unwrap_dek(passphrase: str, envelope: dict[str, str | int]) -> bytes:
    if not isinstance(envelope, dict) or envelope.get("version") != STORE_VERSION or envelope.get("kdf") != "scrypt":
        raise LocalSecretVaultError("E_STORE_CORRUPT", "Secret vault metadata is invalid or unsupported.")
    salt = _unb64(str(envelope["salt"]))
    kek = derive_kek(passphrase, salt)
    aad = f"local-secret-vault:kek:v{STORE_VERSION}".encode("utf-8")
    return _aes_decrypt(
        kek,
        _unb64(str(envelope["nonce"])),
        _unb64(str(envelope["wrapped_dek"])),
        aad,
    )


def encrypt_secret(dek: bytes, plaintext: str, ref: str) -> bytes:
    aad = f"local-secret-vault:secret:{ref}".encode("utf-8")
    encrypted = _aes_encrypt(dek, plaintext.encode("utf-8"), aad)
    return encrypted["nonce"] + encrypted["ciphertext"]


def decrypt_secret(dek: bytes, payload: bytes, ref: str) -> str:
    if len(payload) <= NONCE_BYTES:
        raise LocalSecretVaultError("E_STORE_CORRUPT", "Secret ciphertext is missing or corrupted.")
    nonce = payload[:NONCE_BYTES]
    ciphertext = payload[NONCE_BYTES:]
    aad = f"local-secret-vault:secret:{ref}".encode("utf-8")
    return _aes_decrypt(dek, nonce, ciphertext, aad).decode("utf-8")


"""Symmetric encryption helpers for stored connection configuration."""

import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import Settings, get_settings


def _fernet_from_secret(secret: str) -> Fernet:
    """
    Derive a Fernet key from the application secret.

    Args:
        secret: Long-lived application secret.

    Returns:
        Configured Fernet instance.
    """
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_config(plaintext: str, *, settings: Settings | None = None) -> str:
    """
    Encrypt a UTF-8 string for persistence.

    Args:
        plaintext: JSON or other textual configuration.
        settings: Optional settings override for tests.

    Returns:
        URL-safe base64 ciphertext string.
    """
    cfg = settings or get_settings()
    fernet = _fernet_from_secret(cfg.secret_key)
    token = fernet.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_config(ciphertext: str, *, settings: Settings | None = None) -> str:
    """
    Decrypt a value produced by :func:`encrypt_config`.

    Args:
        ciphertext: Encrypted payload.
        settings: Optional settings override for tests.

    Returns:
        Original plaintext string.
    """
    cfg = settings or get_settings()
    fernet = _fernet_from_secret(cfg.secret_key)
    return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")

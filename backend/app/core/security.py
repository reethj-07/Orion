"""JWT helpers, password hashing, and OAuth2-compatible security utilities."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from passlib.context import CryptContext

from app.core.config import Settings, get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Args:
        plain_password: User-supplied password.

    Returns:
        Bcrypt hash string suitable for persistence.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Verify a plaintext password against a stored bcrypt hash.

    Args:
        plain_password: Candidate password.
        password_hash: Stored hash.

    Returns:
        True if the password matches.
    """
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(
    subject: str,
    *,
    settings: Settings | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Encode a short-lived JWT access token.

    Args:
        subject: Subject identifier (typically user id as string).
        settings: Optional settings override for tests.
        extra_claims: Additional JWT claims to embed.

    Returns:
        Encoded JWT string.
    """
    cfg = settings or get_settings()
    now = datetime.now(tz=UTC)
    expire = now + timedelta(minutes=cfg.jwt_access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "jti": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, cfg.secret_key, algorithm=cfg.jwt_algorithm)


def create_refresh_token(
    subject: str,
    *,
    settings: Settings | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Encode a long-lived JWT refresh token.

    Args:
        subject: Subject identifier (typically user id as string).
        settings: Optional settings override for tests.
        extra_claims: Additional JWT claims to embed.

    Returns:
        Encoded JWT string.
    """
    cfg = settings or get_settings()
    now = datetime.now(tz=UTC)
    expire = now + timedelta(days=cfg.jwt_refresh_token_expire_days)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "refresh",
        "jti": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, cfg.secret_key, algorithm=cfg.jwt_algorithm)


def decode_token(token: str, *, settings: Settings | None = None) -> dict[str, Any]:
    """
    Decode and validate a JWT using the configured secret and algorithm.

    Args:
        token: JWT string.
        settings: Optional settings override for tests.

    Returns:
        Decoded payload dictionary.

    Raises:
        jwt.PyJWTError: If the token is invalid or expired.
    """
    cfg = settings or get_settings()
    return jwt.decode(token, cfg.secret_key, algorithms=[cfg.jwt_algorithm])


def subject_to_uuid(subject: str) -> UUID:
    """
    Parse a JWT subject string into a UUID.

    Args:
        subject: Subject claim value.

    Returns:
        Parsed UUID.

    Raises:
        ValueError: If the subject is not a valid UUID string.
    """
    return UUID(subject)

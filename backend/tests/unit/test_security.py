"""Unit tests for password hashing and JWT helpers."""

from uuid import uuid4

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    subject_to_uuid,
    verify_password,
)


def test_hash_and_verify_password_roundtrip() -> None:
    """Password hashing should verify successfully for the same plaintext."""
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_access_and_refresh_tokens_decode(settings) -> None:
    """Issued tokens should decode with expected claims."""
    user_id = uuid4()
    access = create_access_token(str(user_id), settings=settings)
    refresh = create_refresh_token(str(user_id), settings=settings)
    access_payload = decode_token(access, settings=settings)
    refresh_payload = decode_token(refresh, settings=settings)
    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"
    assert subject_to_uuid(str(access_payload["sub"])) == user_id


def test_decode_invalid_token_raises(settings) -> None:
    """Garbage tokens must raise a JWT error."""
    with pytest.raises(jwt.PyJWTError):
        decode_token("not-a-jwt", settings=settings)

"""Unit tests for AuthService with repository dependencies mocked."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from app.models.user import UserRole
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_register_creates_records_and_returns_tokens(settings) -> None:
    """Registration should persist org and user then return JWTs."""
    session = AsyncMock()
    redis = AsyncMock()
    org_id = uuid4()
    user_id = uuid4()

    org = MagicMock()
    org.id = org_id

    user = MagicMock()
    user.id = user_id
    user.email = "admin@example.com"
    user.role = UserRole.ADMIN
    user.org_id = org_id
    user.is_active = True

    with (
        patch("app.services.auth_service.UserRepository") as user_repo_cls,
        patch("app.services.auth_service.OrganizationRepository") as org_repo_cls,
    ):
        user_repo = user_repo_cls.return_value
        org_repo = org_repo_cls.return_value
        user_repo.get_by_email = AsyncMock(return_value=None)
        org_repo.create = AsyncMock(return_value=org)
        user_repo.create = AsyncMock(return_value=user)

        service = AuthService(session, redis, settings)
        result = await service.register(
            RegisterRequest(
                email="admin@example.com",
                password="supersecurepassword",
                organization_name="Acme Corp",
            )
        )

    assert result.user.email == "admin@example.com"
    assert result.tokens.access_token
    assert result.tokens.refresh_token
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_login_rejects_invalid_password(settings) -> None:
    """Login must fail when the password does not match the stored hash."""
    session = AsyncMock()
    redis = AsyncMock()
    user = MagicMock()
    user.hashed_password = "stored-hash"
    user.is_active = True

    with (
        patch("app.services.auth_service.UserRepository") as user_repo_cls,
        patch(
            "app.services.auth_service.verify_password",
            return_value=False,
        ),
    ):
        user_repo = user_repo_cls.return_value
        user_repo.get_by_email = AsyncMock(return_value=user)
        service = AuthService(session, redis, settings)
        from app.core.exceptions import UnauthorizedError

        with pytest.raises(UnauthorizedError):
            await service.login(
                LoginRequest(email="user@example.com", password="wrong-password"),
            )

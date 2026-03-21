"""Authentication workflows: registration, login, refresh, and logout."""

import time
from uuid import UUID

import jwt
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationAppError
from app.core.principal import AuthPrincipal
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    subject_to_uuid,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.pg.org_repo import OrganizationRepository
from app.repositories.pg.user_repo import UserRepository
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, TokenPair, UserPublic


class AuthService:
    """Coordinates credential verification and token lifecycle."""

    def __init__(self, session: AsyncSession, redis: Redis, settings: Settings) -> None:
        self._session = session
        self._redis = redis
        self._settings = settings
        self._users = UserRepository(session)
        self._orgs = OrganizationRepository(session)

    def _deny_key(self, jti: str) -> str:
        """Build a Redis key for a denylisted refresh token identifier."""
        return f"orion:auth:deny:{jti}"

    def _issue_tokens(self, user_id: UUID) -> TokenPair:
        """Mint access and refresh JWTs for a user."""
        subject = str(user_id)
        access = create_access_token(subject, settings=self._settings)
        refresh = create_refresh_token(subject, settings=self._settings)
        return TokenPair(access_token=access, refresh_token=refresh)

    def _to_public(self, user: User) -> UserPublic:
        """Map a User ORM row to a public schema."""
        return UserPublic(
            id=user.id,
            email=user.email,
            role=user.role,
            org_id=user.org_id,
            is_active=user.is_active,
        )

    async def register(self, payload: RegisterRequest) -> AuthResponse:
        """
        Create a new organization and its first admin user.

        Args:
            payload: Registration request body.

        Returns:
            Tokens and user projection.

        Raises:
            ConflictError: If the email is already registered.
        """
        existing = await self._users.get_by_email(payload.email)
        if existing is not None:
            raise ConflictError("An account with this email already exists")
        org = await self._orgs.create(name=payload.organization_name)
        hashed = hash_password(payload.password)
        user = await self._users.create(
            email=str(payload.email),
            hashed_password=hashed,
            org_id=org.id,
            role=UserRole.ADMIN,
        )
        await self._session.commit()
        tokens = self._issue_tokens(user.id)
        return AuthResponse(tokens=tokens, user=self._to_public(user))

    async def login(self, payload: LoginRequest) -> AuthResponse:
        """
        Authenticate a user with email and password credentials.

        Args:
            payload: Login request body.

        Returns:
            Tokens and user projection.

        Raises:
            UnauthorizedError: If credentials are invalid or the user is inactive.
        """
        user = await self._users.get_by_email(str(payload.email))
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is disabled")
        tokens = self._issue_tokens(user.id)
        return AuthResponse(tokens=tokens, user=self._to_public(user))

    async def refresh(self, refresh_token: str) -> TokenPair:
        """
        Exchange a valid refresh token for a new access token.

        Args:
            refresh_token: Previously issued refresh JWT.

        Returns:
            New token pair (refresh rotated for defense in depth).

        Raises:
            UnauthorizedError: If the token is invalid, expired, or revoked.
        """
        try:
            payload = decode_token(refresh_token, settings=self._settings)
        except jwt.PyJWTError as exc:
            raise UnauthorizedError("Invalid refresh token") from exc
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid refresh token")
        jti = payload.get("jti")
        if isinstance(jti, str) and await self._redis.get(self._deny_key(jti)):
            raise UnauthorizedError("Refresh token has been revoked")
        user_id = subject_to_uuid(str(payload["sub"]))
        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or inactive")
        return self._issue_tokens(user.id)

    async def logout(self, refresh_token: str | None) -> None:
        """
        Revoke a refresh token by adding its jti to the Redis denylist.

        Args:
            refresh_token: Refresh JWT to revoke, if provided.
        """
        if refresh_token is None:
            return
        try:
            payload = decode_token(refresh_token, settings=self._settings)
        except jwt.PyJWTError:
            return
        if payload.get("type") != "refresh":
            raise ValidationAppError("Provided token is not a refresh token")
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not isinstance(jti, str) or not isinstance(exp, int | float):
            return
        ttl = int(exp - time.time())
        if ttl > 0:
            await self._redis.set(self._deny_key(jti), "1", ex=ttl)

    async def authenticate_access_token(self, access_token: str) -> AuthPrincipal:
        """
        Validate an access token and load the associated principal.

        Args:
            access_token: JWT access token string.

        Returns:
            AuthPrincipal for the active user.

        Raises:
            UnauthorizedError: If the token or user state is invalid.
        """
        try:
            payload = decode_token(access_token, settings=self._settings)
        except jwt.PyJWTError as exc:
            raise UnauthorizedError("Invalid or expired access token") from exc
        if payload.get("type") != "access":
            raise UnauthorizedError("Invalid access token")
        user_id = subject_to_uuid(str(payload["sub"]))
        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or inactive")
        return AuthPrincipal(
            user_id=user.id,
            org_id=user.org_id,
            email=user.email,
            role=user.role,
        )

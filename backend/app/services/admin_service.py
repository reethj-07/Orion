"""Administrative operations for org-scoped resources."""

import hashlib
import secrets
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.principal import AuthPrincipal
from app.models.user import User, UserRole
from app.repositories.pg.api_key_repo import APIKeyRepository
from app.repositories.pg.user_repo import UserRepository
from app.schemas.admin import (
    APIKeyCreatedResponse,
    APIKeyCreateRequest,
    APIKeySummary,
)
from app.schemas.auth import UserPublic


class AdminService:
    """Handles privileged workflows such as API key lifecycle and role changes."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._api_keys = APIKeyRepository(session)

    def _to_public(self, user: User) -> UserPublic:
        """Map a User ORM row to a public schema."""
        return UserPublic(
            id=user.id,
            email=user.email,
            role=user.role,
            org_id=user.org_id,
            is_active=user.is_active,
        )

    async def list_users(self, principal: AuthPrincipal) -> list[UserPublic]:
        """
        List users within the administrator's organization.

        Args:
            principal: Authenticated administrator principal.

        Returns:
            Public user projections ordered by recency.
        """
        rows = await self._users.list_for_org(principal.org_id)
        return [self._to_public(row) for row in rows]

    async def update_user_role(
        self,
        principal: AuthPrincipal,
        user_id: UUID,
        role: UserRole,
    ) -> UserPublic:
        """
        Update a user's role within the same organization.

        Args:
            principal: Authenticated administrator principal.
            user_id: Target user identifier.
            role: New role assignment.

        Returns:
            Updated user projection.

        Raises:
            NotFoundError: When the user is not part of the organization.
        """
        user = await self._users.get_by_id(user_id)
        if user is None or user.org_id != principal.org_id:
            raise NotFoundError("User not found in organization")
        user.role = role
        await self._session.commit()
        await self._session.refresh(user)
        return self._to_public(user)

    async def create_api_key(
        self,
        principal: AuthPrincipal,
        payload: APIKeyCreateRequest,
    ) -> APIKeyCreatedResponse:
        """
        Mint a new API key returning the secret once.

        Args:
            principal: Authenticated administrator principal.
            payload: API key creation body.

        Returns:
            Response containing the raw secret and metadata identifiers.
        """
        raw_secret = f"orion_{secrets.token_urlsafe(32)}"
        digest = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()
        row = await self._api_keys.create(
            org_id=principal.org_id,
            key_hash=digest,
            scopes=payload.scopes,
            expires_at=payload.expires_at,
        )
        await self._session.commit()
        return APIKeyCreatedResponse(
            id=row.id,
            secret=raw_secret,
            scopes=row.scopes,
            expires_at=row.expires_at,
        )

    async def list_api_keys(self, principal: AuthPrincipal) -> list[APIKeySummary]:
        """
        List API key metadata without revealing secrets.

        Args:
            principal: Authenticated administrator principal.

        Returns:
            Summaries for each API key in the organization.
        """
        rows = await self._api_keys.list_for_org(principal.org_id)
        return [
            APIKeySummary(
                id=row.id,
                scopes=row.scopes,
                expires_at=row.expires_at,
                created_at=row.created_at,
            )
            for row in rows
        ]

"""Persistence operations for organization API keys."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey


class APIKeyRepository:
    """Encapsulates SQLAlchemy access patterns for API keys."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        org_id: UUID,
        key_hash: str,
        scopes: list[str],
        expires_at: datetime | None = None,
    ) -> APIKey:
        """
        Insert an API key metadata row.

        Args:
            org_id: Owning organization.
            key_hash: Hash of the secret key material.
            scopes: Authorized scopes.
            expires_at: Optional expiry timestamp.

        Returns:
            Persisted APIKey ORM instance.
        """
        row = APIKey(org_id=org_id, key_hash=key_hash, scopes=scopes, expires_at=expires_at)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def list_for_org(self, org_id: UUID) -> list[APIKey]:
        """
        List API keys for an organization.

        Args:
            org_id: Organization identifier.

        Returns:
            Matching API key rows.
        """
        stmt = select(APIKey).where(APIKey.org_id == org_id).order_by(APIKey.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

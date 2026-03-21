"""Persistence operations for organizations."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization


class OrganizationRepository:
    """Encapsulates SQLAlchemy access patterns for organizations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        name: str,
        plan: str = "standard",
        settings: dict[str, Any] | None = None,
    ) -> Organization:
        """
        Insert a new organization row.

        Args:
            name: Display name for the tenant.
            plan: Commercial plan identifier.
            settings: Optional settings JSON; defaults to empty dict.

        Returns:
            Persisted Organization ORM instance.
        """
        org = Organization(
            name=name,
            plan=plan,
            settings_json=settings or {},
        )
        self._session.add(org)
        await self._session.flush()
        await self._session.refresh(org)
        return org

    async def get_by_id(self, org_id: UUID) -> Organization | None:
        """
        Fetch an organization by primary key.

        Args:
            org_id: Organization identifier.

        Returns:
            Organization when found, otherwise None.
        """
        result = await self._session.execute(select(Organization).where(Organization.id == org_id))
        return result.scalar_one_or_none()

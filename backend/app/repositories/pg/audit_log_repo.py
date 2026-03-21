"""Persistence helpers for audit logs."""

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.user import User


class AuditLogRepository:
    """Encapsulates SQLAlchemy access patterns for audit logs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: str,
        metadata: dict[str, object],
    ) -> AuditLog:
        """
        Insert an audit log entry.

        Args:
            user_id: Acting user identifier, if any.
            action: Action verb label.
            resource_type: Resource category.
            resource_id: Resource identifier as string.
            metadata: Structured metadata payload.

        Returns:
            Persisted AuditLog ORM instance.
        """
        row = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def list_for_org(
        self,
        *,
        org_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        """
        List audit logs for actions performed by users in an organization.

        Args:
            org_id: Organization identifier.
            limit: Page size.
            offset: Page offset.

        Returns:
            Tuple of rows and total count.
        """
        stmt: Select[tuple[AuditLog]] = (
            select(AuditLog)
            .join(User, AuditLog.user_id == User.id)
            .where(User.org_id == org_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count_stmt = (
            select(func.count())
            .select_from(AuditLog)
            .join(User, AuditLog.user_id == User.id)
            .where(User.org_id == org_id)
        )
        total = int((await self._session.execute(count_stmt)).scalar_one())
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

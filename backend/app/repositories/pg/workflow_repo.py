"""Persistence operations for workflows."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow, WorkflowStatus


class WorkflowRepository:
    """Encapsulates SQLAlchemy access patterns for workflows."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID,
        org_id: UUID,
        title: str,
        task_description: str,
        status: WorkflowStatus = WorkflowStatus.DRAFT,
    ) -> Workflow:
        """
        Insert a workflow row.

        Args:
            user_id: Creating user identifier.
            org_id: Owning organization identifier.
            title: Short title for UI lists.
            task_description: Natural language task body.
            status: Initial workflow status.

        Returns:
            Persisted Workflow ORM instance.
        """
        row = Workflow(
            user_id=user_id,
            org_id=org_id,
            title=title,
            task_description=task_description,
            status=status,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get_for_org(self, org_id: UUID, workflow_id: UUID) -> Workflow | None:
        """
        Fetch a workflow scoped to an organization.

        Args:
            org_id: Organization identifier.
            workflow_id: Workflow primary key.

        Returns:
            Workflow when found and not soft-deleted, otherwise None.
        """
        stmt: Select[tuple[Workflow]] = select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.org_id == org_id,
            Workflow.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        *,
        user_id: UUID,
        org_id: UUID,
        limit: int = 50,
        offset: int = 0,
        status: WorkflowStatus | None = None,
    ) -> tuple[list[Workflow], int]:
        """
        List workflows for a user within an organization with optional status filter.

        Args:
            user_id: User identifier.
            org_id: Organization identifier.
            limit: Page size.
            offset: Page offset.
            status: Optional status filter.

        Returns:
            Tuple of rows and total count.
        """
        filters = [
            Workflow.user_id == user_id,
            Workflow.org_id == org_id,
            Workflow.deleted_at.is_(None),
        ]
        if status is not None:
            filters.append(Workflow.status == status)
        base = select(Workflow).where(*filters)
        count_stmt = select(func.count()).select_from(Workflow).where(*filters)
        total = int((await self._session.execute(count_stmt)).scalar_one())
        stmt = base.order_by(Workflow.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def update_status(
        self,
        workflow_id: UUID,
        *,
        status: WorkflowStatus,
        completed_at: datetime | None = None,
    ) -> None:
        """
        Update workflow status and optional completion timestamp.

        Args:
            workflow_id: Workflow identifier.
            status: New status value.
            completed_at: Optional completion timestamp.
        """
        row = await self._session.get(Workflow, workflow_id)
        if row is None:
            return
        row.status = status
        if completed_at is not None:
            row.completed_at = completed_at
        await self._session.flush()

    async def count_by_status_for_org(self, org_id: UUID) -> dict[WorkflowStatus, int]:
        """
        Count workflows grouped by status for an organization.

        Args:
            org_id: Organization identifier.

        Returns:
            Mapping of status to count excluding soft-deleted rows.
        """
        stmt = (
            select(Workflow.status, func.count())
            .where(
                Workflow.org_id == org_id,
                Workflow.deleted_at.is_(None),
            )
            .group_by(Workflow.status)
        )
        result = await self._session.execute(stmt)
        counts: dict[WorkflowStatus, int] = {}
        for status, count in result.all():
            counts[status] = int(count)
        return counts

    async def soft_delete(self, row: Workflow) -> None:
        """
        Mark a workflow as deleted without removing historical rows.

        Args:
            row: Workflow ORM instance.
        """
        row.deleted_at = datetime.now(tz=UTC)
        await self._session.flush()

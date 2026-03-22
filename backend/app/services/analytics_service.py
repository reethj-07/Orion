"""Analytics aggregation service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.infra_types import MotorDatabase
from app.core.principal import AuthPrincipal
from app.repositories.pg.audit_log_repo import AuditLogRepository
from app.repositories.pg.workflow_repo import WorkflowRepository
from app.schemas.analytics import AuditLogEntry, UsageStats


class AnalyticsService:
    """Combines PostgreSQL and MongoDB metrics for operator dashboards."""

    def __init__(self, session: AsyncSession, mongo: MotorDatabase) -> None:
        self._session = session
        self._mongo = mongo
        self._workflows = WorkflowRepository(session)
        self._audit = AuditLogRepository(session)

    async def usage(self, principal: AuthPrincipal) -> UsageStats:
        """
        Aggregate workflow counts and Mongo workflow result totals.

        Args:
            principal: Authenticated principal providing org scope.

        Returns:
            Usage statistics snapshot.
        """
        counts = await self._workflows.count_by_status_for_org(principal.org_id)
        serialized = {status.value: count for status, count in counts.items()}
        results_col = self._mongo["workflow_results"]
        workflow_results = int(
            await results_col.count_documents({"metadata.org_id": str(principal.org_id)}),
        )
        return UsageStats(
            workflow_counts=serialized,
            token_usage={"prompt": 0, "completion": 0},
            workflow_results=workflow_results,
        )

    async def audit_log(
        self,
        principal: AuthPrincipal,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AuditLogEntry], int]:
        """
        Return paginated audit log entries for the active organization.

        Args:
            principal: Authenticated administrator principal.
            limit: Page size.
            offset: Page offset.

        Returns:
            Tuple of audit rows and total count.
        """
        rows, total = await self._audit.list_for_org(org_id=principal.org_id, limit=limit, offset=offset)
        entries = [
            AuditLogEntry(
                id=row.id,
                user_id=row.user_id,
                action=row.action,
                resource_type=row.resource_type,
                resource_id=row.resource_id,
                metadata=row.metadata_json,
                created_at=row.created_at,
            )
            for row in rows
        ]
        return entries, total

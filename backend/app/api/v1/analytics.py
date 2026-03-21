"""Analytics routes for usage and audit visibility."""

from fastapi import APIRouter, Query, Request

from app.api.responses import pagination_meta, success_envelope
from app.core.dependencies import AdminPrincipal, CurrentPrincipal, DbSession, MongoDb
from app.schemas.analytics import AuditLogEntry, UsageStats
from app.schemas.common import APIResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/usage", response_model=APIResponse[UsageStats])
async def get_usage(
    request: Request,
    principal: CurrentPrincipal,
    session: DbSession,
    mongo: MongoDb,
) -> APIResponse[UsageStats]:
    """
    Return workflow and ingestion analytics for the active organization.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated principal.
        session: Database session.
        mongo: Mongo database handle.

    Returns:
        API envelope with usage statistics.
    """
    service = AnalyticsService(session, mongo)
    stats = await service.usage(principal)
    return success_envelope(request, stats)


@router.get("/audit-log", response_model=APIResponse[list[AuditLogEntry]])
async def get_audit_log(
    request: Request,
    principal: AdminPrincipal,
    session: DbSession,
    mongo: MongoDb,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> APIResponse[list[AuditLogEntry]]:
    """
    List audit log entries for organization administrators.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated administrator principal.
        session: Database session.
        mongo: Mongo database handle.
        limit: Page size.
        offset: Page offset.

    Returns:
        API envelope with audit rows.
    """
    service = AnalyticsService(session, mongo)
    entries, total = await service.audit_log(principal, limit=limit, offset=offset)
    meta = pagination_meta(total=total, page=(offset // limit) + 1, page_size=limit)
    return success_envelope(request, entries, meta=meta)

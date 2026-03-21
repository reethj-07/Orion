"""Workflow CRUD routes and SSE streaming."""

from uuid import UUID

from fastapi import APIRouter, Query, Request
from sse_starlette.sse import EventSourceResponse

from app.api.responses import pagination_meta, success_envelope
from app.core.dependencies import CurrentPrincipal, DbSession, MongoDb, RedisDep, SettingsDep
from app.core.sse import workflow_event_stream
from app.models.workflow import WorkflowStatus
from app.schemas.common import APIResponse
from app.schemas.workflow import (
    CreateWorkflowRequest,
    WorkflowDetailResponse,
    WorkflowResponse,
)
from app.services.workflow_service import WorkflowService

router = APIRouter()


@router.post("/", response_model=APIResponse[WorkflowResponse])
async def create_workflow(
    request: Request,
    principal: CurrentPrincipal,
    session: DbSession,
    mongo: MongoDb,
    settings: SettingsDep,
    payload: CreateWorkflowRequest,
) -> APIResponse[WorkflowResponse]:
    """
    Create a workflow from natural language input and dispatch execution.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated principal.
        session: Database session.
        mongo: Mongo database handle.
        settings: Application settings.
        payload: Creation body.

    Returns:
        API envelope with the created workflow summary.
    """
    service = WorkflowService(session, mongo, settings)
    result = await service.create_workflow(principal, payload)
    return success_envelope(request, result)


@router.get("/", response_model=APIResponse[list[WorkflowResponse]])
async def list_workflows(
    request: Request,
    principal: CurrentPrincipal,
    session: DbSession,
    mongo: MongoDb,
    settings: SettingsDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: WorkflowStatus | None = Query(default=None),
) -> APIResponse[list[WorkflowResponse]]:
    """
    List workflows for the authenticated user.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated principal.
        session: Database session.
        mongo: Mongo database handle.
        settings: Application settings.
        limit: Page size.
        offset: Page offset.
        status: Optional workflow status filter.

    Returns:
        API envelope with workflow summaries.
    """
    service = WorkflowService(session, mongo, settings)
    items, total = await service.list_workflows(principal, limit=limit, offset=offset, status=status)
    meta = pagination_meta(total=total, page=(offset // limit) + 1, page_size=limit)
    return success_envelope(request, items, meta=meta)


@router.get("/{workflow_id}/stream")
async def stream_workflow(
    principal: CurrentPrincipal,
    session: DbSession,
    mongo: MongoDb,
    settings: SettingsDep,
    redis: RedisDep,
    workflow_id: UUID,
) -> EventSourceResponse:
    """
    Stream workflow execution events from Redis pub/sub over SSE.

    Args:
        principal: Authenticated principal.
        session: Database session.
        mongo: Mongo database handle.
        settings: Application settings.
        redis: Redis client.
        workflow_id: Workflow identifier.

    Returns:
        ``EventSourceResponse`` streaming workflow updates.
    """
    service = WorkflowService(session, mongo, settings)
    await service.get_workflow(principal, workflow_id)
    return EventSourceResponse(workflow_event_stream(redis, str(workflow_id)))


@router.get("/{workflow_id}", response_model=APIResponse[WorkflowDetailResponse])
async def get_workflow(
    request: Request,
    principal: CurrentPrincipal,
    session: DbSession,
    mongo: MongoDb,
    settings: SettingsDep,
    workflow_id: UUID,
) -> APIResponse[WorkflowDetailResponse]:
    """
    Retrieve workflow detail including Mongo-backed traces.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated principal.
        session: Database session.
        mongo: Mongo database handle.
        settings: Application settings.
        workflow_id: Workflow identifier.

    Returns:
        API envelope with detailed workflow information.
    """
    service = WorkflowService(session, mongo, settings)
    detail = await service.get_workflow(principal, workflow_id)
    return success_envelope(request, detail)


@router.delete("/{workflow_id}", response_model=APIResponse[dict[str, str]])
async def delete_workflow(
    request: Request,
    principal: CurrentPrincipal,
    session: DbSession,
    mongo: MongoDb,
    settings: SettingsDep,
    workflow_id: UUID,
) -> APIResponse[dict[str, str]]:
    """
    Soft-delete a workflow.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated principal.
        session: Database session.
        mongo: Mongo database handle.
        settings: Application settings.
        workflow_id: Workflow identifier.

    Returns:
        API envelope confirming deletion.
    """
    service = WorkflowService(session, mongo, settings)
    await service.delete_workflow(principal, workflow_id)
    return success_envelope(request, {"status": "deleted"})

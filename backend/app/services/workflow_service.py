"""Business logic for workflow lifecycle and orchestration dispatch."""

from typing import Any
from uuid import UUID

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.principal import AuthPrincipal
from app.models.user import UserRole
from app.models.workflow import Workflow, WorkflowStatus
from app.repositories.mongo.agent_run_repo import AgentRunRepository
from app.repositories.pg.workflow_repo import WorkflowRepository
from app.schemas.workflow import (
    CreateWorkflowRequest,
    WorkflowDetailResponse,
    WorkflowResponse,
)
from app.tasks.workflow_tasks import execute_workflow_task


def _serialize_mongo_document(document: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    Convert MongoDB BSON types into JSON-serializable primitives.

    Args:
        document: Raw Mongo document.

    Returns:
        Serializable dictionary or None when input is None.
    """
    if document is None:
        return None

    def _transform(value: Any) -> Any:
        if isinstance(value, ObjectId):
            return str(value)
        if isinstance(value, dict):
            return {key: _transform(val) for key, val in value.items()}
        if isinstance(value, list):
            return [_transform(item) for item in value]
        return value

    return {key: _transform(val) for key, val in document.items()}


class WorkflowService:
    """Coordinates workflow persistence, dispatch, and result hydration."""

    def __init__(self, session: AsyncSession, mongo: AsyncIOMotorDatabase, settings: Settings) -> None:
        self._session = session
        self._mongo = mongo
        self._settings = settings
        self._repo = WorkflowRepository(session)
        self._agent_repo = AgentRunRepository(mongo)

    def _to_summary(self, row: Workflow) -> WorkflowResponse:
        """Map a Workflow ORM row to a summary schema."""
        return WorkflowResponse(
            id=row.id,
            org_id=row.org_id,
            user_id=row.user_id,
            title=row.title,
            status=row.status,
            task_description=row.task_description,
            created_at=row.created_at,
            completed_at=row.completed_at,
        )

    async def create_workflow(
        self,
        principal: AuthPrincipal,
        payload: CreateWorkflowRequest,
    ) -> WorkflowResponse:
        """
        Persist a workflow row and enqueue asynchronous execution.

        Args:
            principal: Authenticated principal initiating the workflow.
            payload: Creation request body.

        Returns:
            Newly created workflow summary.
        """
        row = await self._repo.create(
            user_id=principal.user_id,
            org_id=principal.org_id,
            title=payload.title,
            task_description=payload.task_description,
            status=WorkflowStatus.RUNNING,
        )
        await self._session.commit()
        execute_workflow_task.delay(str(row.id), str(principal.org_id), str(principal.user_id))
        refreshed = await self._repo.get_for_org(principal.org_id, row.id)
        if refreshed is None:
            return self._to_summary(row)
        return self._to_summary(refreshed)

    async def list_workflows(
        self,
        principal: AuthPrincipal,
        *,
        limit: int = 50,
        offset: int = 0,
        status: WorkflowStatus | None = None,
    ) -> tuple[list[WorkflowResponse], int]:
        """
        List workflows for the current user within their organization.

        Args:
            principal: Authenticated principal.
            limit: Page size.
            offset: Page offset.
            status: Optional status filter.

        Returns:
            Tuple of summaries and total count.
        """
        rows, total = await self._repo.list_for_user(
            user_id=principal.user_id,
            org_id=principal.org_id,
            limit=limit,
            offset=offset,
            status=status,
        )
        return [self._to_summary(row) for row in rows], total

    async def get_workflow(self, principal: AuthPrincipal, workflow_id: UUID) -> WorkflowDetailResponse:
        """
        Fetch a workflow with Mongo-backed trace and report payloads.

        Args:
            principal: Authenticated principal.
            workflow_id: Workflow identifier.

        Returns:
            Detailed workflow projection.

        Raises:
            NotFoundError: When the workflow does not exist.
            ForbiddenError: When the workflow belongs to another user.
        """
        row = await self._repo.get_for_org(principal.org_id, workflow_id)
        if row is None:
            raise NotFoundError("Workflow not found")
        if row.user_id != principal.user_id and principal.role != UserRole.ADMIN:
            raise ForbiddenError("Cannot access workflow owned by another user")
        mongo_doc = _serialize_mongo_document(await self._agent_repo.get_workflow_result(workflow_id))
        events = await self._agent_repo.list_agent_events(workflow_id)
        trace = [_serialize_mongo_document(event) or {} for event in events]
        report = mongo_doc
        summary = self._to_summary(row)
        return WorkflowDetailResponse(
            **summary.model_dump(),
            report=report,
            trace=trace,
        )

    async def delete_workflow(self, principal: AuthPrincipal, workflow_id: UUID) -> None:
        """
        Soft-delete a workflow when the caller is the owner or an admin.

        Args:
            principal: Authenticated principal.
            workflow_id: Workflow identifier.

        Raises:
            NotFoundError: When the workflow does not exist.
            ForbiddenError: When the caller cannot delete the workflow.
        """
        row = await self._repo.get_for_org(principal.org_id, workflow_id)
        if row is None:
            raise NotFoundError("Workflow not found")
        if row.user_id != principal.user_id and principal.role != UserRole.ADMIN:
            raise ForbiddenError("Cannot delete workflow owned by another user")
        await self._repo.soft_delete(row)
        await self._session.commit()

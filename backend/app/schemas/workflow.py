"""Workflow API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.workflow import WorkflowStatus


class CreateWorkflowRequest(BaseModel):
    """Payload for creating a new workflow."""

    title: str = Field(..., min_length=3, max_length=512)
    task_description: str = Field(..., min_length=10, max_length=20000)


class WorkflowResponse(BaseModel):
    """Workflow summary returned to API clients."""

    id: UUID
    org_id: UUID
    user_id: UUID
    title: str
    status: WorkflowStatus
    task_description: str
    created_at: datetime
    completed_at: datetime | None


class WorkflowDetailResponse(WorkflowResponse):
    """Workflow detail including persisted agent artifacts."""

    report: dict[str, Any] | None = None
    trace: list[dict[str, Any]] = Field(default_factory=list)


class WorkflowListResponse(BaseModel):
    """Paginated list wrapper."""

    items: list[WorkflowResponse]
    total: int

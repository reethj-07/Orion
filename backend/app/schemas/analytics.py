"""Analytics API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class UsageStats(BaseModel):
    """Aggregated usage metrics for dashboards."""

    workflow_counts: dict[str, int]
    token_usage: dict[str, int] = Field(default_factory=dict)
    workflow_results: int = 0


class AuditLogEntry(BaseModel):
    """Audit log projection for administrators."""

    id: UUID
    user_id: UUID | None
    action: str
    resource_type: str
    resource_id: str
    metadata: dict[str, Any]
    created_at: datetime

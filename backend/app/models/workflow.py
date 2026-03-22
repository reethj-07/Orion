"""Workflow execution record stored in PostgreSQL."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class WorkflowStatus(enum.StrEnum):
    """Lifecycle state for a workflow run."""

    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Workflow(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    User-initiated multi-agent workflow with title and status tracking.

    Attributes:
        id: Primary key.
        user_id: User who created the workflow.
        org_id: Owning organization.
        title: Short human-readable title.
        status: Current lifecycle status.
        task_description: Natural language task specification.
        created_at: Row creation timestamp.
        updated_at: Row last update timestamp.
        completed_at: Timestamp when workflow finished successfully or failed.
        deleted_at: Soft-delete timestamp when set.
    """

    __tablename__ = "workflows"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    org_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus),
        nullable=False,
        default=WorkflowStatus.DRAFT,
    )
    task_description: Mapped[str] = mapped_column(Text, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="workflows")
    organization: Mapped[Organization] = relationship("Organization", back_populates="workflows")

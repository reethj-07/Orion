"""Immutable audit log entries for security-sensitive actions."""

from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Record of a user action against a resource for compliance review.

    Attributes:
        id: Primary key.
        user_id: Acting user (nullable for system actions if extended later).
        action: Verb describing the action performed.
        resource_type: Type of resource affected.
        resource_id: Identifier of the affected resource.
        metadata: Arbitrary structured metadata for the event.
        created_at: Event timestamp (same as TimestampMixin.created_at).
        updated_at: Last update timestamp (audit rows are typically immutable).
    """

    __tablename__ = "audit_logs"

    user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )

    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs")

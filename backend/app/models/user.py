"""Application user model."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.organization import Organization
    from app.models.workflow import Workflow

from sqlalchemy import Boolean, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(enum.StrEnum):
    """Role used for coarse-grained authorization."""

    ADMIN = "admin"
    MEMBER = "member"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Authenticated user belonging to a single organization.

    Attributes:
        id: Primary key.
        email: Unique email address used for login.
        hashed_password: Bcrypt password hash.
        role: Authorization role within the organization.
        org_id: Owning organization foreign key.
        is_active: Whether the account may authenticate.
        created_at: Row creation timestamp.
        updated_at: Row last update timestamp.
    """

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.MEMBER)
    org_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")
    workflows: Mapped[list["Workflow"]] = relationship(
        "Workflow",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )

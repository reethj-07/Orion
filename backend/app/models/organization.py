"""Organization model representing a tenant."""

from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Tenant organization with plan metadata and arbitrary settings JSON.

    Attributes:
        id: Primary key.
        name: Human-readable organization name.
        plan: Commercial plan identifier.
        settings_json: JSON blob for feature flags and configuration.
        created_at: Row creation timestamp.
        updated_at: Row last update timestamp.
    """

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(64), nullable=False, default="standard")
    settings_json: Mapped[dict[str, Any]] = mapped_column(
        "settings",
        JSONB,
        nullable=False,
        default=dict,
    )

    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    workflows: Mapped[list["Workflow"]] = relationship(
        "Workflow",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    document_sources: Mapped[list["DocumentSource"]] = relationship(
        "DocumentSource",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

"""Organization-scoped API keys with hashed secrets."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class APIKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    API key metadata; the raw key is never stored, only a hash.

    Attributes:
        id: Primary key.
        org_id: Owning organization.
        key_hash: SHA-256 (or similar) hash of the API key material.
        scopes: List of allowed scopes for the key.
        expires_at: Optional expiry after which the key is invalid.
        created_at: Row creation timestamp.
        updated_at: Row last update timestamp.
    """

    __tablename__ = "api_keys"

    org_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    scopes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="api_keys")

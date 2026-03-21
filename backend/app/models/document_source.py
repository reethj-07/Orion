"""Registered document or data source for ingestion."""

import enum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DocumentSourceType(str, enum.Enum):
    """Supported ingestion source categories."""

    PDF = "pdf"
    URL = "url"
    TEXT = "text"
    DATABASE = "database"
    API = "api"


class DocumentSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Logical source of documents for an organization.

    Attributes:
        id: Primary key.
        org_id: Owning organization.
        name: Display name for the source.
        source_type: Category of the source connection.
        connection_config_encrypted: Encrypted JSON configuration blob.
        created_at: Row creation timestamp.
        updated_at: Row last update timestamp.
    """

    __tablename__ = "document_sources"

    org_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[DocumentSourceType] = mapped_column(
        Enum(DocumentSourceType),
        nullable=False,
    )
    connection_config_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    ingestion_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="document_sources",
    )

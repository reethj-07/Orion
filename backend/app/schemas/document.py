"""Document ingestion and listing schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.models.document_source import DocumentSourceType


class IngestUrlRequest(BaseModel):
    """Request body for ingesting a public URL."""

    name: str = Field(..., min_length=1, max_length=255)
    url: HttpUrl


class IngestTextRequest(BaseModel):
    """Request body for ingesting raw text."""

    name: str = Field(..., min_length=1, max_length=255)
    text: str = Field(..., min_length=1)


class DocumentResponse(BaseModel):
    """Document source projection returned to clients."""

    id: UUID
    org_id: UUID
    name: str
    source_type: DocumentSourceType
    ingestion_status: str
    last_error: str | None
    created_at: datetime


class IngestQueuedResponse(BaseModel):
    """Response after an ingestion job is queued."""

    document_id: UUID
    task_id: str
    message: str = "Ingestion task queued"

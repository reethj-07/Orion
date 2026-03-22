"""Business logic for document registration and ingestion orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.crypto import encrypt_config
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.principal import AuthPrincipal
from app.models.document_source import DocumentSource, DocumentSourceType
from app.repositories.pg.document_repo import DocumentRepository
from app.repositories.qdrant.vector_repo import VectorRepository
from app.schemas.document import (
    DocumentResponse,
    IngestQueuedResponse,
    IngestTextRequest,
    IngestUrlRequest,
)
from app.tasks.ingestion_tasks import ingest_document_task


class DocumentService:
    """Coordinates encrypted configuration storage and ingestion queueing."""

    def __init__(self, session: AsyncSession, settings: Settings, qdrant: AsyncQdrantClient) -> None:
        self._session = session
        self._settings = settings
        self._qdrant = qdrant
        self._repo = DocumentRepository(session)

    def _to_response(self, row: DocumentSource) -> DocumentResponse:
        """Map a DocumentSource ORM instance to an API schema."""
        return DocumentResponse(
            id=row.id,
            org_id=row.org_id,
            name=row.name,
            source_type=row.source_type,
            ingestion_status=row.ingestion_status,
            last_error=row.last_error,
            created_at=row.created_at,
        )

    async def ingest_url(self, principal: AuthPrincipal, payload: IngestUrlRequest) -> IngestQueuedResponse:
        """
        Register a URL source and enqueue asynchronous ingestion.

        Args:
            principal: Authenticated principal.
            payload: URL ingestion request body.

        Returns:
            Response containing identifiers for polling status indirectly via listing.
        """
        cfg = encrypt_config(json.dumps({"url": str(payload.url)}), settings=self._settings)
        row = await self._repo.create(
            org_id=principal.org_id,
            name=payload.name,
            source_type=DocumentSourceType.URL,
            connection_config_encrypted=cfg,
        )
        await self._session.commit()
        task = ingest_document_task.delay(str(row.id), str(principal.org_id))
        return IngestQueuedResponse(document_id=row.id, task_id=task.id)

    async def ingest_text(self, principal: AuthPrincipal, payload: IngestTextRequest) -> IngestQueuedResponse:
        """
        Register a raw text source and enqueue ingestion.

        Args:
            principal: Authenticated principal.
            payload: Text ingestion request body.

        Returns:
            Queued task metadata.
        """
        cfg = encrypt_config(json.dumps({"text": payload.text}), settings=self._settings)
        row = await self._repo.create(
            org_id=principal.org_id,
            name=payload.name,
            source_type=DocumentSourceType.TEXT,
            connection_config_encrypted=cfg,
        )
        await self._session.commit()
        task = ingest_document_task.delay(str(row.id), str(principal.org_id))
        return IngestQueuedResponse(document_id=row.id, task_id=task.id)

    async def ingest_pdf(self, principal: AuthPrincipal, upload: UploadFile) -> IngestQueuedResponse:
        """
        Persist an uploaded PDF to shared storage and enqueue ingestion.

        Args:
            principal: Authenticated principal.
            upload: Uploaded PDF file handle.

        Returns:
            Queued task metadata.

        Raises:
            ValidationAppError: When the file is not a PDF by content type or extension.
        """
        filename = upload.filename or "document.pdf"
        if not filename.lower().endswith(".pdf"):
            raise ValidationAppError("Only PDF uploads are supported for this endpoint")
        storage_root = Path(self._settings.ingest_storage_dir)
        storage_root.mkdir(parents=True, exist_ok=True)
        target = storage_root / f"{uuid4()}.pdf"
        content = await upload.read()
        if not content:
            raise ValidationAppError("Uploaded file is empty")
        target.write_bytes(content)
        cfg = encrypt_config(json.dumps({"path": str(target)}), settings=self._settings)
        row = await self._repo.create(
            org_id=principal.org_id,
            name=filename,
            source_type=DocumentSourceType.PDF,
            connection_config_encrypted=cfg,
        )
        await self._session.commit()
        task = ingest_document_task.delay(str(row.id), str(principal.org_id))
        return IngestQueuedResponse(document_id=row.id, task_id=task.id)

    async def list_documents(
        self,
        principal: AuthPrincipal,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[DocumentResponse], int]:
        """
        List document sources for the caller's organization.

        Args:
            principal: Authenticated principal.
            limit: Page size.
            offset: Page offset.

        Returns:
            Tuple of response models and total count.
        """
        rows, total = await self._repo.list_for_org(principal.org_id, limit=limit, offset=offset)
        return [self._to_response(row) for row in rows], total

    async def delete_document(self, principal: AuthPrincipal, document_id: UUID) -> None:
        """
        Remove a document source and purge associated vectors.

        Args:
            principal: Authenticated principal.
            document_id: Identifier of the document to remove.

        Raises:
            NotFoundError: When the document does not exist for the org.
        """
        row = await self._repo.get_for_org(principal.org_id, document_id)
        if row is None:
            raise NotFoundError("Document not found")
        vectors = VectorRepository(self._qdrant, self._settings)
        await vectors.delete_document_vectors(principal.org_id, document_id)
        await self._repo.delete(row)
        await self._session.commit()

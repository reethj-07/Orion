"""Background ingestion tasks executed by Celery workers."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from uuid import UUID

from app.core.config import get_settings
from app.core.crypto import decrypt_config
from app.core.database import create_pg_engine, create_qdrant_client, create_session_factory
from app.core.logging import get_logger
from app.models.document_source import DocumentSourceType
from app.pipelines.ingestion import (
    chunk_and_embed,
    load_documents_pdf,
    load_documents_text,
    load_documents_url,
)
from app.repositories.pg.document_repo import DocumentRepository
from app.repositories.qdrant.vector_repo import VectorRepository
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


async def _ingest_document_async(document_id: UUID, org_id: UUID) -> None:
    """
    Load configuration, chunk and embed content, and persist vectors in Qdrant.

    Args:
        document_id: Primary key of the document_sources row.
        org_id: Owning organization identifier.
    """
    settings = get_settings()
    engine = create_pg_engine(settings.database_url)
    factory = create_session_factory(engine)
    config_payload: dict[str, str]
    source_type: DocumentSourceType
    display_name: str

    async with factory() as session:
        repo = DocumentRepository(session)
        row = await repo.get_for_org(org_id, document_id)
        if row is None:
            logger.warning("ingestion_missing_document", document_id=str(document_id))
            return
        config_payload = json.loads(
            decrypt_config(row.connection_config_encrypted, settings=settings),
        )
        source_type = row.source_type
        display_name = row.name
        await repo.update_ingestion(document_id, status="processing")
        await session.commit()

    pdf_path: Path | None = None
    try:
        if source_type == DocumentSourceType.PDF:
            pdf_path = Path(config_payload["path"])
            documents = load_documents_pdf(pdf_path)
        elif source_type == DocumentSourceType.URL:
            documents = load_documents_url(config_payload["url"])
        elif source_type == DocumentSourceType.TEXT:
            documents = load_documents_text(config_payload["text"], display_name)
        else:
            raise ValueError(f"Unsupported source type for ingestion: {source_type}")

        batch = chunk_and_embed(documents, settings)
        client = create_qdrant_client(settings.qdrant_url)
        vector_repo = VectorRepository(client, settings)
        if batch.texts:
            await vector_repo.upsert_document_chunks(
                org_id=org_id,
                document_id=document_id,
                source_name=display_name,
                embeddings=batch.embeddings,
                texts=batch.texts,
                vector_size=batch.vector_size,
            )
        await client.close()

        async with factory() as session:
            repo = DocumentRepository(session)
            await repo.update_ingestion(document_id, status="completed", last_error=None)
            await session.commit()
    except Exception as exc:
        logger.exception("ingestion_failed", document_id=str(document_id))
        async with factory() as session:
            repo = DocumentRepository(session)
            await repo.update_ingestion(document_id, status="failed", last_error=str(exc))
            await session.commit()
        raise
    finally:
        if pdf_path is not None and pdf_path.exists():
            pdf_path.unlink(missing_ok=True)

    await engine.dispose()


@celery_app.task(name="orion.ingest_document")
def ingest_document_task(document_id: str, org_id: str) -> None:
    """
    Celery entrypoint that runs the async ingestion pipeline in an event loop.

    Args:
        document_id: UUID string for the document_sources row.
        org_id: UUID string for the organization.
    """
    asyncio.run(_ingest_document_async(UUID(document_id), UUID(org_id)))

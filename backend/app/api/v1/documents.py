"""Document ingestion and management routes."""

from uuid import UUID

from fastapi import APIRouter, File, Query, Request, UploadFile

from app.api.responses import pagination_meta, success_envelope
from app.core.dependencies import CurrentPrincipal, DocumentServiceDep
from app.schemas.common import APIResponse
from app.schemas.document import (
    DocumentResponse,
    IngestQueuedResponse,
    IngestTextRequest,
    IngestUrlRequest,
)

router = APIRouter()


@router.post("/ingest/url", response_model=APIResponse[IngestQueuedResponse])
async def ingest_url(
    request: Request,
    principal: CurrentPrincipal,
    service: DocumentServiceDep,
    payload: IngestUrlRequest,
) -> APIResponse[IngestQueuedResponse]:
    """
    Register a remote URL to be fetched, chunked, embedded, and indexed.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated principal.
        service: Document service instance.
        payload: URL ingestion payload.

    Returns:
        API envelope with queued task metadata.
    """
    result = await service.ingest_url(principal, payload)
    return success_envelope(request, result)


@router.post("/ingest/text", response_model=APIResponse[IngestQueuedResponse])
async def ingest_text(
    request: Request,
    principal: CurrentPrincipal,
    service: DocumentServiceDep,
    payload: IngestTextRequest,
) -> APIResponse[IngestQueuedResponse]:
    """
    Register inline text to be chunked, embedded, and indexed.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated principal.
        service: Document service instance.
        payload: Text ingestion payload.

    Returns:
        API envelope with queued task metadata.
    """
    result = await service.ingest_text(principal, payload)
    return success_envelope(request, result)


@router.post("/ingest/pdf", response_model=APIResponse[IngestQueuedResponse])
async def ingest_pdf(
    request: Request,
    principal: CurrentPrincipal,
    service: DocumentServiceDep,
    file: UploadFile = File(...),
) -> APIResponse[IngestQueuedResponse]:
    """
    Accept a PDF upload, persist it to shared storage, and enqueue ingestion.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated principal.
        service: Document service instance.
        file: Uploaded PDF file.

    Returns:
        API envelope with queued task metadata.
    """
    result = await service.ingest_pdf(principal, file)
    return success_envelope(request, result)


@router.get("/", response_model=APIResponse[list[DocumentResponse]])
async def list_documents(
    request: Request,
    principal: CurrentPrincipal,
    service: DocumentServiceDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> APIResponse[list[DocumentResponse]]:
    """
    List ingested document sources for the active organization.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated principal.
        service: Document service instance.
        limit: Page size.
        offset: Page offset.

    Returns:
        API envelope with document rows and pagination metadata.
    """
    items, total = await service.list_documents(principal, limit=limit, offset=offset)
    meta = pagination_meta(total=total, page=(offset // limit) + 1, page_size=limit)
    return success_envelope(request, items, meta=meta)


@router.delete("/{document_id}", response_model=APIResponse[dict[str, str]])
async def delete_document(
    request: Request,
    principal: CurrentPrincipal,
    service: DocumentServiceDep,
    document_id: UUID,
) -> APIResponse[dict[str, str]]:
    """
    Delete a document source and remove vectors from Qdrant.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated principal.
        service: Document service instance.
        document_id: Identifier of the document to delete.

    Returns:
        API envelope confirming deletion.
    """
    await service.delete_document(principal, document_id)
    return success_envelope(request, {"status": "deleted"})

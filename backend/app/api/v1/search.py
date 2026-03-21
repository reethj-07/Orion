"""Search routes."""

from fastapi import APIRouter, Request

from app.api.responses import success_envelope
from app.core.dependencies import CurrentPrincipal, QdrantDep, SettingsDep
from app.schemas.common import APIResponse
from app.schemas.search import HybridSearchRequest, SearchResult, SemanticSearchRequest
from app.services.search_service import SearchService

router = APIRouter()


@router.post("/semantic", response_model=APIResponse[list[SearchResult]])
async def semantic_search(
    request: Request,
    principal: CurrentPrincipal,
    qdrant: QdrantDep,
    settings: SettingsDep,
    payload: SemanticSearchRequest,
) -> APIResponse[list[SearchResult]]:
    """
    Perform semantic vector search over ingested documents.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated principal.
        qdrant: Qdrant client.
        settings: Application settings.
        payload: Search body.

    Returns:
        API envelope with ranked hits.
    """
    service = SearchService(qdrant, settings)
    results = await service.semantic_search(principal, payload)
    return success_envelope(request, results)


@router.post("/hybrid", response_model=APIResponse[list[SearchResult]])
async def hybrid_search(
    request: Request,
    principal: CurrentPrincipal,
    qdrant: QdrantDep,
    settings: SettingsDep,
    payload: HybridSearchRequest,
) -> APIResponse[list[SearchResult]]:
    """
    Perform hybrid semantic and lexical rescored search.

    Args:
        request: Incoming HTTP request.
        principal: Authenticated principal.
        qdrant: Qdrant client.
        settings: Application settings.
        payload: Hybrid search body.

    Returns:
        API envelope with ranked hits.
    """
    service = SearchService(qdrant, settings)
    results = await service.hybrid_search(principal, payload)
    return success_envelope(request, results)

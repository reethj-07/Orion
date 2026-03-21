"""Document analysis specialist using Qdrant semantic retrieval."""

from uuid import UUID

from qdrant_client import AsyncQdrantClient
from redis.asyncio import Redis

from app.agents.events import publish_workflow_update
from app.core.config import Settings
from app.core.embeddings import embed_text_async
from app.core.exceptions import ValidationAppError
from app.core.logging import get_logger
from app.repositories.qdrant.vector_repo import VectorRepository

logger = get_logger(__name__)


async def _embed_query(text: str, settings: Settings) -> list[float]:
    """
    Create an embedding vector for a query (OpenAI or local Ollama).

    Args:
        text: Query text to embed.
        settings: Application settings including provider and credentials.

    Returns:
        Embedding vector.

    Raises:
        RuntimeError: When configuration is invalid or the request fails.
    """
    try:
        return await embed_text_async(text, settings)
    except ValidationAppError as exc:
        raise RuntimeError(str(exc)) from exc


async def run_document_analysis(
    *,
    task: str,
    workflow_id: str,
    org_id: UUID,
    settings: Settings,
    redis: Redis,
    qdrant: AsyncQdrantClient,
) -> str:
    """
    Retrieve relevant document chunks and synthesize an answer with citations.

    Args:
        task: Natural language question or instruction.
        workflow_id: Workflow identifier for streaming updates.
        org_id: Organization identifier for collection selection.
        settings: Application settings.
        redis: Redis client for streaming.
        qdrant: Async Qdrant client.

    Returns:
        Markdown string containing retrieved context summaries.
    """
    await publish_workflow_update(
        redis,
        workflow_id,
        {"agent": "document_analysis", "status": "running", "detail": "Embedding query"},
    )
    try:
        vector = await _embed_query(task, settings)
    except Exception as exc:
        logger.warning("embedding_failed", error=str(exc))
        await publish_workflow_update(
            redis,
            workflow_id,
            {"agent": "document_analysis", "status": "failed", "detail": str(exc)},
        )
        return "Semantic retrieval skipped due to embedding configuration or network error."

    await publish_workflow_update(
        redis,
        workflow_id,
        {"agent": "document_analysis", "status": "running", "detail": "Searching vectors"},
    )
    repo = VectorRepository(qdrant, settings)
    hits = await repo.semantic_search(org_id, query_vector=vector, limit=8)
    if not hits:
        await publish_workflow_update(
            redis,
            workflow_id,
            {"agent": "document_analysis", "status": "completed", "detail": "No hits"},
        )
        return "No relevant ingested documents were found for this task."

    lines: list[str] = []
    for index, hit in enumerate(hits, start=1):
        preview = str(hit.get("text_preview", "")).strip()
        source = str(hit.get("source_name", "unknown"))
        score = float(hit.get("score", 0.0))
        lines.append(f"{index}. ({source}, score={score:.3f}) {preview}")

    memo = "### Retrieved evidence\n" + "\n".join(lines)
    await publish_workflow_update(
        redis,
        workflow_id,
        {"agent": "document_analysis", "status": "completed", "detail": "Evidence packaged"},
    )
    return memo

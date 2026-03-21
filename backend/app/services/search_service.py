"""Semantic and hybrid search orchestration."""

from uuid import UUID

import httpx
from qdrant_client import AsyncQdrantClient

from app.core.config import Settings
from app.core.exceptions import ValidationAppError
from app.core.principal import AuthPrincipal
from app.repositories.qdrant.vector_repo import VectorRepository
from app.schemas.search import HybridSearchRequest, SearchResult, SemanticSearchRequest


class SearchService:
    """Executes embedding-backed retrieval with optional lexical rescoring."""

    def __init__(self, qdrant: AsyncQdrantClient, settings: Settings) -> None:
        self._qdrant = qdrant
        self._settings = settings
        self._vectors = VectorRepository(qdrant, settings)

    async def _embed(self, text: str) -> list[float]:
        """
        Embed query text using OpenAI HTTP API.

        Args:
            text: Query string.

        Returns:
            Embedding vector.

        Raises:
            ValidationAppError: When credentials are missing.
        """
        if not self._settings.openai_api_key:
            raise ValidationAppError("OPENAI_API_KEY is required for search")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self._settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self._settings.embedding_model, "input": text},
            )
            response.raise_for_status()
            payload = response.json()
            return payload["data"][0]["embedding"]

    async def semantic_search(
        self,
        principal: AuthPrincipal,
        payload: SemanticSearchRequest,
    ) -> list[SearchResult]:
        """
        Run semantic search for the active organization.

        Args:
            principal: Authenticated principal providing org scope.
            payload: Search request body.

        Returns:
            Ranked list of search hits.
        """
        vector = await self._embed(payload.query)
        hits = await self._vectors.semantic_search(principal.org_id, query_vector=vector, limit=payload.limit)
        return [self._to_result(hit) for hit in hits]

    async def hybrid_search(
        self,
        principal: AuthPrincipal,
        payload: HybridSearchRequest,
    ) -> list[SearchResult]:
        """
        Combine semantic similarity with a lightweight lexical boost over previews.

        Args:
            principal: Authenticated principal providing org scope.
            payload: Hybrid search request body.

        Returns:
            Re-ranked list of search hits.
        """
        vector = await self._embed(payload.query)
        hits = await self._vectors.semantic_search(principal.org_id, query_vector=vector, limit=payload.limit * 3)
        tokens = {token.lower() for token in payload.query.split() if len(token) > 2}

        def score(hit: dict[str, object]) -> float:
            base = float(hit.get("score", 0.0))
            preview = str(hit.get("text_preview", "")).lower()
            matches = sum(1 for token in tokens if token in preview)
            boost = payload.keyword_boost * min(matches, 5)
            return base + boost

        ranked = sorted(hits, key=score, reverse=True)[: payload.limit]
        return [self._to_result(hit) for hit in ranked]

    def _to_result(self, hit: dict[str, object]) -> SearchResult:
        """Normalize a Qdrant payload dictionary into a SearchResult model."""
        doc_raw = hit.get("doc_id")
        doc_id = UUID(str(doc_raw)) if doc_raw else None
        return SearchResult(
            doc_id=doc_id,
            chunk_id=str(hit.get("chunk_id")) if hit.get("chunk_id") else None,
            source_name=str(hit.get("source_name")) if hit.get("source_name") else None,
            text_preview=str(hit.get("text_preview")) if hit.get("text_preview") else None,
            score=float(hit.get("score", 0.0)),
            payload={k: v for k, v in hit.items() if k not in {"score"}},
        )

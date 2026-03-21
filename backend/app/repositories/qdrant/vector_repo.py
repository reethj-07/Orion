"""Vector persistence and retrieval using Qdrant."""

from typing import Any
from uuid import UUID, uuid4

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as rest

from app.core.config import Settings, get_settings


def documents_collection_name(org_id: UUID) -> str:
    """
    Build the Qdrant collection name for organization documents.

    Args:
        org_id: Organization identifier.

    Returns:
        Collection name string safe for Qdrant naming rules.
    """
    return f"org_{str(org_id).replace('-', '_')}_documents"


def web_cache_collection_name(org_id: UUID) -> str:
    """
    Build the Qdrant collection name for cached web content.

    Args:
        org_id: Organization identifier.

    Returns:
        Collection name string safe for Qdrant naming rules.
    """
    return f"org_{str(org_id).replace('-', '_')}_web_cache"


class VectorRepository:
    """Async vector operations against Qdrant."""

    def __init__(self, client: AsyncQdrantClient, settings: Settings | None = None) -> None:
        self._client = client
        self._settings = settings or get_settings()

    async def ensure_collection(
        self,
        collection: str,
        *,
        vector_size: int = 1536,
    ) -> None:
        """
        Create a collection if it does not already exist.

        Args:
            collection: Target collection name.
            vector_size: Embedding dimension for cosine distance vectors.
        """
        exists = await self._client.collection_exists(collection)
        if exists:
            return
        await self._client.create_collection(
            collection_name=collection,
            vectors_config=rest.VectorParams(size=vector_size, distance=rest.Distance.COSINE),
        )

    async def upsert_document_chunks(
        self,
        *,
        org_id: UUID,
        document_id: UUID,
        source_name: str,
        embeddings: list[list[float]],
        texts: list[str],
        vector_size: int,
    ) -> None:
        """
        Upsert chunked embeddings for a document into the org collection.

        Args:
            org_id: Owning organization identifier.
            document_id: Logical document identifier in PostgreSQL.
            source_name: Human-readable document name.
            embeddings: Embedding vectors aligned with texts.
            texts: Chunk text aligned with embeddings.
            vector_size: Embedding width used when ensuring the collection.
        """
        if len(embeddings) != len(texts):
            raise ValueError("embeddings and texts must have the same length")
        collection = documents_collection_name(org_id)
        await self.ensure_collection(collection, vector_size=vector_size)
        points: list[rest.PointStruct] = []
        for index, (vector, text) in enumerate(zip(embeddings, texts, strict=True)):
            chunk_id = str(uuid4())
            preview = text[:500]
            payload: dict[str, Any] = {
                "org_id": str(org_id),
                "doc_id": str(document_id),
                "chunk_id": chunk_id,
                "source_name": source_name,
                "page_num": None,
                "text_preview": preview,
                "text": text,
            }
            points.append(
                rest.PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload=payload,
                )
            )
        await self._client.upsert(collection_name=collection, points=points, wait=True)

    async def delete_document_vectors(self, org_id: UUID, document_id: UUID) -> None:
        """
        Remove all vectors associated with a document id.

        Args:
            org_id: Organization identifier selecting the collection.
            document_id: Document identifier stored in vector payloads.
        """
        collection = documents_collection_name(org_id)
        exists = await self._client.collection_exists(collection)
        if not exists:
            return
        await self._client.delete(
            collection_name=collection,
            points_selector=rest.FilterSelector(
                filter=rest.Filter(
                    must=[
                        rest.FieldCondition(
                            key="doc_id",
                            match=rest.MatchValue(value=str(document_id)),
                        )
                    ]
                )
            ),
            wait=True,
        )

    async def semantic_search(
        self,
        org_id: UUID,
        *,
        query_vector: list[float],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Perform a nearest-neighbor search for a query embedding.

        Args:
            org_id: Organization identifier selecting the collection.
            query_vector: Query embedding.
            limit: Maximum hits to return.

        Returns:
            List of payload dictionaries augmented with similarity scores.
        """
        collection = documents_collection_name(org_id)
        if not await self._client.collection_exists(collection):
            return []
        results = await self._client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
        )
        hits: list[dict[str, Any]] = []
        for hit in results:
            payload = hit.payload or {}
            hits.append({**payload, "score": hit.score})
        return hits

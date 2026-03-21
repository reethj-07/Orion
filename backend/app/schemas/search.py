"""Search API schemas."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    """Semantic vector search request."""

    query: str = Field(..., min_length=3, max_length=4000)
    limit: int = Field(default=10, ge=1, le=50)


class HybridSearchRequest(SemanticSearchRequest):
    """Hybrid search combining semantic similarity with lexical heuristics."""

    keyword_boost: float = Field(default=0.35, ge=0.0, le=1.0)


class SearchResult(BaseModel):
    """Single search hit."""

    doc_id: UUID | None = None
    chunk_id: str | None = None
    source_name: str | None = None
    text_preview: str | None = None
    score: float
    payload: dict[str, Any] = Field(default_factory=dict)

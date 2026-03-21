"""Text embedding via OpenAI API or local Ollama (no paid API required for Ollama)."""

from __future__ import annotations

import httpx

from app.core.config import Settings
from app.core.exceptions import ValidationAppError


def _ollama_base(settings: Settings) -> str:
    return settings.ollama_base_url.rstrip("/")


async def embed_text_async(text: str, settings: Settings) -> list[float]:
    """
    Produce a single embedding vector for downstream search or RAG.

    Args:
        text: Input text.
        settings: Embedding provider and model configuration.

    Returns:
        Embedding vector.

    Raises:
        ValidationAppError: When configuration is invalid or the request fails.
    """
    if settings.embedding_provider == "ollama":
        url = f"{_ollama_base(settings)}/api/embeddings"
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                json={"model": settings.ollama_embed_model, "prompt": text},
            )
            response.raise_for_status()
            payload = response.json()
            vector = payload.get("embedding")
            if not vector:
                raise ValidationAppError("Ollama returned an empty embedding")
            return list(vector)

    if not settings.openai_api_key:
        raise ValidationAppError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={"model": settings.embedding_model, "input": text},
        )
        response.raise_for_status()
        payload = response.json()
        return payload["data"][0]["embedding"]


def embed_texts_batch_sync(texts: list[str], settings: Settings) -> list[list[float]]:
    """
    Embed many texts synchronously (used from Celery ingestion tasks).

    Args:
        texts: Chunk texts to embed.
        settings: Provider configuration.

    Returns:
        List of embedding vectors aligned with ``texts``.

    Raises:
        ValidationAppError: When configuration is invalid or a request fails.
    """
    if not texts:
        return []

    if settings.embedding_provider == "ollama":
        url = f"{_ollama_base(settings)}/api/embeddings"
        out: list[list[float]] = []
        with httpx.Client(timeout=120.0) as client:
            for chunk in texts:
                response = client.post(
                    url,
                    json={"model": settings.ollama_embed_model, "prompt": chunk},
                )
                response.raise_for_status()
                payload = response.json()
                vector = payload.get("embedding")
                if not vector:
                    raise ValidationAppError("Ollama returned an empty embedding")
                out.append(list(vector))
        return out

    if not settings.openai_api_key:
        raise ValidationAppError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
    # OpenAI batch API accepts multiple inputs; single request reduces round trips.
    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={"model": settings.embedding_model, "input": texts},
        )
        response.raise_for_status()
        payload = response.json()
        data = sorted(payload["data"], key=lambda row: row["index"])
        return [row["embedding"] for row in data]

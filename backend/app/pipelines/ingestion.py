"""Document loading, chunking, and embedding for vector ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from llama_index.core import Document, Settings as LlamaSettings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.readers.file import PyMuPDFReader
from llama_index.readers.web import SimpleWebPageReader

from app.core.config import Settings
from app.core.exceptions import ValidationAppError


@dataclass(slots=True)
class ChunkBatch:
    """Chunk texts and aligned embedding vectors ready for vector storage."""

    texts: list[str]
    embeddings: list[list[float]]
    vector_size: int


def _configure_embed_model(settings: Settings) -> OpenAIEmbedding:
    """
    Configure the LlamaIndex global embedding model for OpenAI.

    Args:
        settings: Application settings including API keys.

    Returns:
        Configured OpenAIEmbedding instance.

    Raises:
        ValidationAppError: When the OpenAI API key is not configured.
    """
    if not settings.openai_api_key:
        raise ValidationAppError("OPENAI_API_KEY is required for embeddings")
    embed_model = OpenAIEmbedding(
        api_key=settings.openai_api_key,
        model=settings.embedding_model,
    )
    LlamaSettings.embed_model = embed_model
    return embed_model


def load_documents_pdf(path: Path) -> list[Document]:
    """
    Load a PDF file into LlamaIndex documents.

    Args:
        path: Filesystem path to the PDF.

    Returns:
        List of loaded documents.
    """
    reader = PyMuPDFReader()
    return reader.load(file_path=str(path))


def load_documents_url(url: str) -> list[Document]:
    """
    Load a web page into LlamaIndex documents.

    Args:
        url: Public HTTP or HTTPS URL.

    Returns:
        List of loaded documents.
    """
    reader = SimpleWebPageReader()
    return reader.load_data([url])


def load_documents_text(text: str, name: str) -> list[Document]:
    """
    Wrap raw text as a LlamaIndex document.

    Args:
        text: Full textual content.
        name: Logical file name for metadata.

    Returns:
        Single-document list.
    """
    return [Document(text=text, metadata={"file_name": name})]


def chunk_and_embed(documents: Iterable[Document], settings: Settings) -> ChunkBatch:
    """
    Split documents into chunks and embed them using the configured embed model.

    Args:
        documents: Source documents to process.
        settings: Application settings controlling embedding configuration.

    Returns:
        ChunkBatch containing texts, embeddings, and vector width.

    Raises:
        ValidationAppError: When embedding configuration is invalid.
    """
    embed_model = _configure_embed_model(settings)
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    nodes = splitter.get_nodes_from_documents(list(documents))
    texts = [node.get_content() for node in nodes]
    if not texts:
        return ChunkBatch(texts=[], embeddings=[], vector_size=0)
    embeddings = embed_model.get_text_embedding_batch(texts)
    width = len(embeddings[0]) if embeddings else 0
    return ChunkBatch(texts=texts, embeddings=embeddings, vector_size=width)

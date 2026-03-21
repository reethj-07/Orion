"""Unit tests for text ingestion helpers."""

from app.pipelines.ingestion import load_documents_text


def test_load_documents_text_wraps_content() -> None:
    """Text ingestion should produce a single LlamaIndex document."""
    documents = load_documents_text("hello world", name="memo.txt")
    assert len(documents) == 1
    assert "hello world" in documents[0].text

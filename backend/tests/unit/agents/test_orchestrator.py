"""Tests for LangGraph orchestration compilation."""

from unittest.mock import MagicMock

from app.agents.orchestrator import build_workflow_graph
from app.core.config import Settings


def test_build_workflow_graph_compiles() -> None:
    """The workflow graph should compile without requiring live services."""
    settings = Settings(
        secret_key="test-secret-key-for-jwt-signing-32b",
        database_url="postgresql+asyncpg://u:p@localhost/db",
        mongodb_uri="mongodb://localhost:27017",
    )
    redis = MagicMock()
    qdrant = MagicMock()
    graph = build_workflow_graph(settings, redis, qdrant)
    assert graph is not None

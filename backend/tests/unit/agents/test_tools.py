"""Web search tool wiring."""

from app.agents.tools import build_web_search_tool
from app.core.config import Settings


def test_duckduckgo_tool_when_provider_is_duckduckgo() -> None:
    """DuckDuckGo search should be available without API keys."""
    settings = Settings(
        secret_key="test-secret-key-for-jwt-signing-32b",
        database_url="postgresql+asyncpg://u:p@localhost/db",
        mongodb_uri="mongodb://localhost:27017",
        web_search_provider="duckduckgo",
    )
    tool = build_web_search_tool(settings)
    assert tool is not None


def test_no_tool_when_search_disabled() -> None:
    """Explicit none provider should skip search."""
    settings = Settings(
        secret_key="test-secret-key-for-jwt-signing-32b",
        database_url="postgresql+asyncpg://u:p@localhost/db",
        mongodb_uri="mongodb://localhost:27017",
        web_search_provider="none",
    )
    assert build_web_search_tool(settings) is None


def test_tavily_without_key_falls_back_to_duckduckgo() -> None:
    """Missing Tavily key should not break the web researcher."""
    settings = Settings(
        secret_key="test-secret-key-for-jwt-signing-32b",
        database_url="postgresql+asyncpg://u:p@localhost/db",
        mongodb_uri="mongodb://localhost:27017",
        web_search_provider="tavily",
        tavily_api_key=None,
    )
    tool = build_web_search_tool(settings)
    assert tool is not None

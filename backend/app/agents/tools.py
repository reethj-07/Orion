"""LangChain-compatible tools for specialist agents."""

from typing import Any

import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool

from app.core.config import Settings


def build_tavily_search_tool(settings: Settings):
    """
    Build a Tavily-backed search tool when an API key is configured.

    Args:
        settings: Application settings containing optional Tavily credentials.

    Returns:
        A LangChain tool callable, or None when Tavily is not configured.
    """
    if not settings.tavily_api_key:
        return None

    @tool("tavily_search")
    async def tavily_search(query: str) -> str:
        """
        Execute a live web search using the Tavily API.

        Args:
            query: Natural language search query.

        Returns:
            Concatenated textual snippets from search results.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "search_depth": "advanced",
                },
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            results = payload.get("results", [])
            lines = [item.get("content", "") for item in results if item.get("content")]
            return "\n".join(lines) if lines else "No results returned."

    return tavily_search


async def scrape_url_text(url: str) -> str:
    """
    Fetch a URL and extract visible text using BeautifulSoup.

    Args:
        url: HTTP or HTTPS URL.

    Returns:
        Extracted text content.
    """
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)

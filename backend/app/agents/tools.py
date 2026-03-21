"""LangChain-compatible tools for specialist agents."""

import asyncio
from typing import Any

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from langchain_core.tools import tool

from app.core.config import Settings


def build_duckduckgo_search_tool():
    """
    Build a DuckDuckGo-backed search tool (no API key; suitable for zero-cost setups).

    Returns:
        A LangChain async tool callable.
    """

    @tool("web_search")
    async def web_search(query: str) -> str:
        """
        Run a web search and return short snippets from top results.

        Args:
            query: Natural language search query.

        Returns:
            Concatenated snippets from search hits.
        """

        def _run() -> str:
            lines: list[str] = []
            with DDGS() as ddgs:
                for item in ddgs.text(query, max_results=5):
                    title = str(item.get("title", "")).strip()
                    body = str(item.get("body", "")).strip()
                    if title or body:
                        lines.append(f"{title}: {body}")
            return "\n".join(lines) if lines else "No results returned."

        return await asyncio.to_thread(_run)

    return web_search


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
                    "search_depth": "basic",
                },
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            results = payload.get("results", [])
            lines = [item.get("content", "") for item in results if item.get("content")]
            return "\n".join(lines) if lines else "No results returned."

    return tavily_search


def build_web_search_tool(settings: Settings):
    """
    Build a web search tool from ``WEB_SEARCH_PROVIDER``.

    If ``tavily`` is selected but ``TAVILY_API_KEY`` is missing, falls back to DuckDuckGo so
    development stays usable without paid keys.

    Args:
        settings: Application settings.

    Returns:
        LangChain tool, or None when search is explicitly disabled.
    """
    if settings.web_search_provider == "none":
        return None
    if settings.web_search_provider == "tavily":
        tavily = build_tavily_search_tool(settings)
        if tavily is not None:
            return tavily
    return build_duckduckgo_search_tool()


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

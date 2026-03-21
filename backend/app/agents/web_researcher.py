"""Web research specialist agent."""

from app.agents.events import publish_workflow_update
from app.agents.tools import build_tavily_search_tool, scrape_url_text
from app.core.config import Settings
from app.core.logging import get_logger
from redis.asyncio import Redis

logger = get_logger(__name__)


async def run_web_research(
    *,
    task: str,
    workflow_id: str,
    settings: Settings,
    redis: Redis,
) -> str:
    """
    Collect external context using Tavily (when configured) and lightweight scraping.

    Args:
        task: User task text used to derive queries.
        workflow_id: Workflow identifier for streaming updates.
        settings: Application settings.
        redis: Redis client for pub/sub streaming.

    Returns:
        Consolidated textual research memo.
    """
    await publish_workflow_update(
        redis,
        workflow_id,
        {"agent": "web_research", "status": "running", "detail": "Gathering web context"},
    )
    tool = build_tavily_search_tool(settings)
    snippets: list[str] = []
    if tool is not None:
        try:
            result = await tool.ainvoke({"query": task})
            snippets.append(str(result))
        except Exception as exc:  # pragma: no cover - network failures
            logger.warning("tavily_search_failed", error=str(exc))
            snippets.append("Live search failed; continuing with direct fetch only.")
    else:
        snippets.append("Tavily API key not configured; skipping live search.")

    await publish_workflow_update(
        redis,
        workflow_id,
        {"agent": "web_research", "status": "running", "detail": "Scraping referenced URLs"},
    )

    memo_parts = list(snippets)
    if task.startswith("http://") or task.startswith("https://"):
        try:
            page_text = await scrape_url_text(task)
            memo_parts.append(page_text[:8000])
        except Exception as exc:  # pragma: no cover - network failures
            logger.warning("scrape_failed", error=str(exc))
            memo_parts.append(f"Unable to scrape task URL: {exc}")

    memo = "\n\n".join(memo_parts)
    await publish_workflow_update(
        redis,
        workflow_id,
        {"agent": "web_research", "status": "completed", "detail": "Research memo ready"},
    )
    return memo

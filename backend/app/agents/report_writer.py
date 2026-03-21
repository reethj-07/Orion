"""Report writer agent synthesizing markdown output."""

from langchain_core.messages import HumanMessage
from redis.asyncio import Redis

from app.agents.events import publish_workflow_update
from app.agents.llm import get_chat_model
from app.core.config import Settings


async def run_report_writer(
    *,
    task: str,
    agent_outputs: dict[str, str],
    workflow_id: str,
    settings: Settings,
    redis: Redis,
) -> str:
    """
    Combine intermediate agent outputs into a structured markdown report.

    Args:
        task: Original workflow task description.
        agent_outputs: Map of agent name to textual memo.
        workflow_id: Workflow identifier for streaming updates.
        settings: Application settings controlling LLM selection.
        redis: Redis client for streaming updates.

    Returns:
        Markdown report including confidence estimate section.
    """
    await publish_workflow_update(
        redis,
        workflow_id,
        {"agent": "report_writer", "status": "running", "detail": "Synthesizing report"},
    )
    llm = get_chat_model(settings)
    sections = "\n\n".join(f"## {name}\n{body}" for name, body in agent_outputs.items())
    base_prompt = (
        "You are a senior analyst. Using the research memos below, write a polished markdown report "
        "with numbered citations, an executive summary, and a final section titled "
        "'Confidence' with a score between 0 and 1.\n\n"
        f"## Task\n{task}\n\n## Research Memos\n{sections}"
    )
    if llm is None:
        report = (
            f"# Workflow Summary\n\n{base_prompt}\n\n"
            "## Confidence\n0.55 (LLM provider not configured; deterministic fallback used.)"
        )
    else:
        message = await llm.ainvoke([HumanMessage(content=base_prompt)])
        report = str(message.content)

    await publish_workflow_update(
        redis,
        workflow_id,
        {"agent": "report_writer", "status": "completed", "detail": "Report finalized"},
    )
    return report

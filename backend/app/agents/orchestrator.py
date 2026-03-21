"""LangGraph orchestration wiring specialist agents into a linear state machine."""

from uuid import UUID

from langgraph.graph import END, START, StateGraph
from qdrant_client import AsyncQdrantClient
from redis.asyncio import Redis

from app.agents.data_analyst import run_data_analysis
from app.agents.doc_analyst import run_document_analysis
from app.agents.report_writer import run_report_writer
from app.agents.state import WorkflowState
from app.agents.web_researcher import run_web_research
from app.core.config import Settings


class GraphRuntime:
    """Callable node bundle with shared infrastructure handles."""

    def __init__(self, settings: Settings, redis: Redis, qdrant: AsyncQdrantClient) -> None:
        self._settings = settings
        self._redis = redis
        self._qdrant = qdrant

    async def planning(self, state: WorkflowState) -> WorkflowState:
        """
        Initialize a deterministic execution plan for downstream routing metadata.

        Args:
            state: Current LangGraph state.

        Returns:
            Partial state update describing the planned agents.
        """
        plan = [
            {"agent": "web_research", "intent": "external_context"},
            {"agent": "document_analysis", "intent": "internal_rag"},
            {"agent": "data_analysis", "intent": "quantitative_pass"},
            {"agent": "report_writer", "intent": "synthesis"},
        ]
        return {
            "plan": plan,
            "current_step": "planning",
            "status": "planning_complete",
        }

    async def web_research(self, state: WorkflowState) -> WorkflowState:
        """Execute the web research agent."""
        text = await run_web_research(
            task=state["task"],
            workflow_id=state["workflow_id"],
            settings=self._settings,
            redis=self._redis,
        )
        return {
            "agent_outputs": {"web_research": text},
            "current_step": "web_research",
            "status": "web_research_complete",
        }

    async def document_analysis(self, state: WorkflowState) -> WorkflowState:
        """Execute the document analysis agent."""
        text = await run_document_analysis(
            task=state["task"],
            workflow_id=state["workflow_id"],
            org_id=UUID(state["org_id"]),
            settings=self._settings,
            redis=self._redis,
            qdrant=self._qdrant,
        )
        return {
            "agent_outputs": {"document_analysis": text},
            "current_step": "document_analysis",
            "status": "document_analysis_complete",
        }

    async def data_analysis(self, state: WorkflowState) -> WorkflowState:
        """Execute the sandboxed data analysis agent."""
        text = await run_data_analysis(
            task=state["task"],
            workflow_id=state["workflow_id"],
            redis=self._redis,
        )
        return {
            "agent_outputs": {"data_analysis": text},
            "current_step": "data_analysis",
            "status": "data_analysis_complete",
        }

    async def report_writer(self, state: WorkflowState) -> WorkflowState:
        """Execute the reporting agent."""
        outputs = state.get("agent_outputs", {})
        text = await run_report_writer(
            task=state["task"],
            agent_outputs=outputs,
            workflow_id=state["workflow_id"],
            settings=self._settings,
            redis=self._redis,
        )
        return {
            "agent_outputs": {"report_writer": text},
            "current_step": "report_writer",
            "status": "report_complete",
        }


def build_workflow_graph(
    settings: Settings,
    redis: Redis,
    qdrant: AsyncQdrantClient,
):
    """
    Compile the multi-agent LangGraph workflow.

    Args:
        settings: Application settings.
        redis: Redis client for streaming updates.
        qdrant: Async Qdrant client for retrieval.

    Returns:
        Compiled LangGraph runnable.
    """
    runtime = GraphRuntime(settings, redis, qdrant)
    graph = StateGraph(WorkflowState)
    graph.add_node("planning", runtime.planning)
    graph.add_node("web_research", runtime.web_research)
    graph.add_node("document_analysis", runtime.document_analysis)
    graph.add_node("data_analysis", runtime.data_analysis)
    graph.add_node("report_writer", runtime.report_writer)
    graph.add_edge(START, "planning")
    graph.add_edge("planning", "web_research")
    graph.add_edge("web_research", "document_analysis")
    graph.add_edge("document_analysis", "data_analysis")
    graph.add_edge("data_analysis", "report_writer")
    graph.add_edge("report_writer", END)
    return graph.compile()

"""Shared LangGraph state definitions."""

import operator
from typing import Annotated, TypedDict


def _merge_dicts(left: dict[str, str], right: dict[str, str]) -> dict[str, str]:
    """Reducer that shallow-merges string dictionaries for agent outputs."""
    merged = dict(left)
    merged.update(right)
    return merged


class WorkflowState(TypedDict, total=False):
    """
    Mutable workflow state flowing between LangGraph nodes.

    Attributes:
        workflow_id: Primary key of the workflow row in PostgreSQL.
        org_id: Owning organization identifier.
        user_id: User that initiated the workflow.
        task: Natural language task description.
        plan: Structured plan produced by the orchestrator.
        agent_outputs: Accumulated textual outputs keyed by agent name.
        current_step: Name of the agent currently executing.
        status: Coarse workflow status label for streaming.
        errors: Collected error messages from non-fatal failures.
    """

    workflow_id: str
    org_id: str
    user_id: str
    task: str
    plan: list[dict[str, str]]
    agent_outputs: Annotated[dict[str, str], _merge_dicts]
    current_step: str
    status: str
    errors: Annotated[list[str], operator.add]

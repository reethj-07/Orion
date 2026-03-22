"""Workflow execution tasks dispatched to Celery workers."""

from __future__ import annotations

import asyncio
from uuid import UUID

from celery import Task

from app.core.logging import get_logger
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="orion.execute_workflow", bind=True, max_retries=3)
def execute_workflow_task(self: Task, workflow_id: str, org_id: str, user_id: str) -> str:
    """
    Execute a LangGraph workflow asynchronously.

    Args:
        workflow_id: Primary key of the workflow row.
        org_id: Owning organization identifier.
        user_id: User that initiated the workflow.

    Returns:
        The workflow identifier once execution completes.
    """
    _ = self
    from app.agents.runner import run_workflow_graph

    logger.info(
        "workflow_task_started",
        workflow_id=workflow_id,
        org_id=org_id,
        user_id=user_id,
    )
    asyncio.run(run_workflow_graph(UUID(workflow_id), UUID(org_id), UUID(user_id)))
    return workflow_id

"""Persistence for agent execution traces and workflow results in MongoDB."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.infra_types import MotorDatabase


class AgentRunRepository:
    """Stores flexible agent traces and final workflow artifacts."""

    def __init__(self, database: MotorDatabase) -> None:
        self._runs = database["agent_runs"]
        self._results = database["workflow_results"]

    async def record_agent_event(
        self,
        *,
        workflow_id: UUID,
        agent_type: str,
        status: str,
        payload: dict[str, Any],
    ) -> None:
        """
        Insert or update a high-level agent event for a workflow.

        Args:
            workflow_id: Owning workflow identifier.
            agent_type: Logical agent name.
            status: Event status label.
            payload: Arbitrary structured payload for the event.
        """
        document = {
            "workflow_id": str(workflow_id),
            "agent_type": agent_type,
            "status": status,
            "payload": payload,
            "timestamp": datetime.now(tz=UTC),
        }
        await self._runs.insert_one(document)

    async def save_workflow_result(
        self,
        *,
        workflow_id: UUID,
        markdown_report: str,
        sources: list[dict[str, Any]],
        confidence_score: float,
        metadata: dict[str, Any],
        trace: list[dict[str, Any]],
    ) -> None:
        """
        Persist the final synthesized report for a workflow.

        Args:
            workflow_id: Workflow identifier.
            markdown_report: Render-ready markdown output.
            sources: Structured citation metadata.
            confidence_score: Model-estimated confidence in [0, 1].
            metadata: Additional metadata for analytics.
            trace: Full agent trace for auditing.
        """
        await self._results.update_one(
            {"workflow_id": str(workflow_id)},
            {
                "$set": {
                    "workflow_id": str(workflow_id),
                    "markdown_report": markdown_report,
                    "sources": sources,
                    "confidence_score": confidence_score,
                    "metadata": metadata,
                    "trace": trace,
                    "updated_at": datetime.now(tz=UTC),
                }
            },
            upsert=True,
        )

    async def get_workflow_result(self, workflow_id: UUID) -> dict[str, Any] | None:
        """
        Load the stored workflow result document if present.

        Args:
            workflow_id: Workflow identifier.

        Returns:
            Mongo document or None when missing.
        """
        return await self._results.find_one({"workflow_id": str(workflow_id)})

    async def list_agent_events(self, workflow_id: UUID) -> list[dict[str, Any]]:
        """
        Return ordered agent events for a workflow.

        Args:
            workflow_id: Workflow identifier.

        Returns:
            List of Mongo documents.
        """
        cursor = self._runs.find({"workflow_id": str(workflow_id)}).sort("timestamp", 1)
        return await cursor.to_list(length=None)

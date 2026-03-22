"""Entrypoint used by Celery workers to execute compiled LangGraph workflows."""

from datetime import UTC, datetime
from uuid import UUID

from app.agents.orchestrator import build_workflow_graph
from app.agents.state import WorkflowState
from app.core.config import get_settings
from app.core.database import (
    create_motor_client,
    create_pg_engine,
    create_qdrant_client,
    create_redis_client,
    create_session_factory,
    get_motor_database,
)
from app.core.logging import get_logger
from app.models.workflow import WorkflowStatus
from app.repositories.mongo.agent_run_repo import AgentRunRepository
from app.repositories.pg.workflow_repo import WorkflowRepository

logger = get_logger(__name__)


async def run_workflow_graph(workflow_id: UUID, org_id: UUID, user_id: UUID) -> None:
    """
    Load workflow context, execute the LangGraph pipeline, and persist results.

    Args:
        workflow_id: Workflow identifier.
        org_id: Owning organization identifier.
        user_id: User that created the workflow.
    """
    settings = get_settings()
    engine = create_pg_engine(settings.database_url)
    factory = create_session_factory(engine)
    redis = create_redis_client(settings.redis_url)
    qdrant = create_qdrant_client(settings.qdrant_url)
    motor_client = create_motor_client(settings.mongodb_uri)
    mongo_db = get_motor_database(motor_client, settings.mongodb_db)
    agent_repo = AgentRunRepository(mongo_db)
    task_description = ""
    try:
        async with factory() as session:
            wf_repo = WorkflowRepository(session)
            workflow = await wf_repo.get_for_org(org_id, workflow_id)
            if workflow is None:
                logger.error("workflow_missing", workflow_id=str(workflow_id))
                return
            task_description = workflow.task_description
            await wf_repo.update_status(workflow_id, status=WorkflowStatus.RUNNING)
            await session.commit()

        graph = build_workflow_graph(settings, redis, qdrant)
        initial: WorkflowState = {
            "workflow_id": str(workflow_id),
            "org_id": str(org_id),
            "user_id": str(user_id),
            "task": task_description,
            "agent_outputs": {},
            "errors": [],
        }
        final_state = await graph.ainvoke(initial)
        report = final_state.get("agent_outputs", {}).get("report_writer", "")

        for name, body in final_state.get("agent_outputs", {}).items():
            await agent_repo.record_agent_event(
                workflow_id=workflow_id,
                agent_type=name,
                status="completed",
                payload={"preview": body[:400]},
            )

        async with factory() as session:
            wf_repo = WorkflowRepository(session)
            await wf_repo.update_status(
                workflow_id,
                status=WorkflowStatus.COMPLETED,
                completed_at=datetime.now(tz=UTC),
            )
            await session.commit()

        trace = [{"agent": name, "preview": body[:500]} for name, body in final_state.get("agent_outputs", {}).items()]
        await agent_repo.save_workflow_result(
            workflow_id=workflow_id,
            markdown_report=report,
            sources=[],
            confidence_score=0.72,
            metadata={
                "org_id": str(org_id),
                "agents": list(final_state.get("agent_outputs", {}).keys()),
            },
            trace=trace,
        )
    except Exception:
        logger.exception("workflow_failed", workflow_id=str(workflow_id))
        async with factory() as session:
            wf_repo = WorkflowRepository(session)
            await wf_repo.update_status(
                workflow_id,
                status=WorkflowStatus.FAILED,
                completed_at=datetime.now(tz=UTC),
            )
            await session.commit()
        raise
    finally:
        await qdrant.close()
        await redis.close()
        motor_client.close()
        await engine.dispose()

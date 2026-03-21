"""Celery application configured from environment-driven settings."""

from celery import Celery

from app.core.config import get_settings


def create_celery_app() -> Celery:
    """
    Build a Celery application instance with JSON serialization defaults.

    Returns:
        Configured Celery app.
    """
    settings = get_settings()
    application = Celery(
        "orion",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=[
            "app.tasks.ingestion_tasks",
            "app.tasks.workflow_tasks",
        ],
    )
    application.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        broker_connection_retry_on_startup=True,
    )
    return application


celery_app = create_celery_app()

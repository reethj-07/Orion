"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router, limiter
from app.core.config import get_settings
from app.core.database import (
    create_motor_client,
    create_pg_engine,
    create_qdrant_client,
    create_redis_client,
    create_session_factory,
    get_motor_database,
)
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Initialize shared clients on startup and release resources on shutdown.

    Args:
        app: FastAPI application instance.

    Yields:
        Control back to the application runtime after startup completes.
    """
    settings = get_settings()
    configure_logging(json_logs=settings.app_env == "production")

    engine = create_pg_engine(settings.database_url)
    app.state.session_factory = create_session_factory(engine)
    app.state.pg_engine = engine

    motor = create_motor_client(settings.mongodb_uri)
    app.state.mongo_client = motor
    app.state.mongo_db = get_motor_database(motor, settings.mongodb_db)

    redis_client = create_redis_client(settings.redis_url)
    app.state.redis = redis_client

    qdrant = create_qdrant_client(settings.qdrant_url)
    app.state.qdrant = qdrant

    app.state.limiter = limiter

    logger.info("application_startup_complete", app=settings.app_name)
    yield

    await qdrant.close()
    await redis_client.aclose()
    motor.close()
    await engine.dispose()
    logger.info("application_shutdown_complete")


def create_app() -> FastAPI:
    """
    Construct and configure the FastAPI application.

    Returns:
        Fully wired FastAPI instance.
    """
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        version="0.1.0",
    )
    application.add_middleware(SlowAPIMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestContextMiddleware)
    register_exception_handlers(application)
    application.include_router(api_router)

    @application.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        """Return a simple health status for probes."""
        return {"status": "ok"}

    return application


app = create_app()

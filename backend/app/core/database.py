"""Async database engines and client factories for PostgreSQL, MongoDB, Redis, and Qdrant."""

from typing import cast

from motor.motor_asyncio import AsyncIOMotorClient
from qdrant_client import AsyncQdrantClient
from redis.asyncio import from_url as redis_from_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.infra_types import MotorClient, MotorDatabase, RedisJSON


def create_pg_engine(database_url: str) -> AsyncEngine:
    """
    Create an async SQLAlchemy engine for PostgreSQL.

    Args:
        database_url: SQLAlchemy URL using the asyncpg driver.

    Returns:
        Configured async engine with pool pre-ping enabled.
    """
    return create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Build an async session factory bound to the given engine.

    Args:
        engine: Async SQLAlchemy engine.

    Returns:
        Session factory producing AsyncSession instances.
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


def create_motor_client(mongodb_uri: str) -> MotorClient:
    """
    Create a Motor client for MongoDB.

    Args:
        mongodb_uri: MongoDB connection URI.

    Returns:
        AsyncIOMotorClient instance.
    """
    return AsyncIOMotorClient(mongodb_uri)


def get_motor_database(client: MotorClient, db_name: str) -> MotorDatabase:
    """
    Select a database from a Motor client.

    Args:
        client: Motor client.
        db_name: Logical database name.

    Returns:
        AsyncIOMotorDatabase handle.
    """
    return client[db_name]


def create_redis_client(redis_url: str) -> RedisJSON:
    """
    Create an asyncio-compatible Redis client.

    Args:
        redis_url: Redis URL including db index if needed.

    Returns:
        Redis client instance.
    """
    return cast(RedisJSON, redis_from_url(redis_url, decode_responses=True))


def create_qdrant_client(qdrant_url: str) -> AsyncQdrantClient:
    """
    Create an async Qdrant client.

    Args:
        qdrant_url: HTTP URL for the Qdrant service.

    Returns:
        AsyncQdrantClient instance.
    """
    return AsyncQdrantClient(url=qdrant_url)

"""Concrete type parameters for third-party generic clients (mypy + decode_responses)."""

from typing import Any, TypeAlias

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import Redis

# Redis clients created with decode_responses=True return str values.
RedisJSON: TypeAlias = Redis[str]
# Motor uses BSON documents as dicts at the Python boundary.
MotorDatabase: TypeAlias = AsyncIOMotorDatabase[dict[str, Any]]
MotorClient: TypeAlias = AsyncIOMotorClient[dict[str, Any]]

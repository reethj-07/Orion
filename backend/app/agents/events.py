"""Redis pub/sub helpers for workflow streaming."""

import json
from typing import Any

from redis.asyncio import Redis


async def publish_workflow_update(redis: Redis, workflow_id: str, payload: dict[str, Any]) -> None:
    """
    Publish a JSON-serialized workflow event to the workflow-specific channel.

    Args:
        redis: Async Redis client.
        workflow_id: Workflow identifier used to build the channel name.
        payload: Serializable event body for SSE consumers.
    """
    channel = f"workflow:{workflow_id}"
    await redis.publish(channel, json.dumps(payload, default=str))

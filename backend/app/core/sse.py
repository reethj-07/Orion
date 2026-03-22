"""Server-Sent Event helpers backed by Redis pub/sub."""

from collections.abc import AsyncIterator
from typing import Any

from app.core.infra_types import RedisJSON


async def workflow_event_stream(redis: RedisJSON, workflow_id: str) -> AsyncIterator[dict[str, Any]]:
    """
    Yield SSE-compatible dictionaries sourced from Redis pub/sub messages.

    Args:
        redis: Async Redis client subscribed for the duration of the stream.
        workflow_id: Workflow identifier used to derive the channel name.

    Yields:
        Dictionaries understood by ``sse_starlette.EventSourceResponse``.
    """
    channel = f"workflow:{workflow_id}"
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)
    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            data = message["data"]
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            yield {"event": "workflow", "data": data}
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()

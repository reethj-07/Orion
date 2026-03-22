"""Data analysis specialist with a restricted execution sandbox."""

import json
from typing import Any

from redis.asyncio import Redis
from RestrictedPython import compile_restricted

from app.agents.events import publish_workflow_update
from app.core.logging import get_logger

logger = get_logger(__name__)


def _execute_restricted(code: str) -> dict[str, Any]:
    """
    Execute Python code in a restricted global namespace.

    Args:
        code: Python statements assigning to ``result`` (a JSON-serializable value).

    Returns:
        Dictionary of local variables after execution.

    Raises:
        ValueError: When the code fails restricted compilation.
    """
    byte_code = compile_restricted(code, "<data_analyst>", "exec")
    if byte_code is None:
        raise ValueError("Provided analysis code failed restricted compilation.")
    safe_globals: dict[str, Any] = {
        "__builtins__": {
            "range": range,
            "len": len,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "float": float,
            "int": int,
            "round": round,
            "sorted": sorted,
            "list": list,
            "dict": dict,
            "zip": zip,
        }
    }
    locals_map: dict[str, Any] = {}
    exec(byte_code, safe_globals, locals_map)
    return locals_map


async def run_data_analysis(
    *,
    task: str,
    workflow_id: str,
    redis: Redis,
) -> str:
    """
    Produce a lightweight analytic artifact suitable for dashboard rendering.

    Args:
        task: Natural language task (used as context only for this implementation).
        workflow_id: Workflow identifier for streaming updates.
        redis: Redis client for streaming.

    Returns:
        JSON string describing a simple chart payload and narrative summary.
    """
    await publish_workflow_update(
        redis,
        workflow_id,
        {"agent": "data_analysis", "status": "running", "detail": "Running sandboxed analysis"},
    )
    code = (
        "series = [{'x': i, 'y': i * i} for i in range(1, 8)]\n"
        "result = {'type': 'line', 'data': series, 'summary': 'Quadratic growth sample'}"
    )
    try:
        locals_map = _execute_restricted(code)
        payload = locals_map.get("result", {})
        narrative = (
            f"Automated quantitative pass for task context: {task[:200]}\n\n" f"```{json.dumps(payload, indent=2)}```"
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("data_analysis_failed", error=str(exc))
        narrative = f"Data analysis sandbox could not complete: {exc}"
    await publish_workflow_update(
        redis,
        workflow_id,
        {"agent": "data_analysis", "status": "completed", "detail": "Analysis memo ready"},
    )
    return narrative

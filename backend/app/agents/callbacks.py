"""LangChain callback hooks for LLM observability."""

from typing import Any
from uuid import uuid4

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from app.core.logging import get_logger

logger = get_logger(__name__)


class StructuredLLMCallback(BaseCallbackHandler):
    """
    Emit structured logs for each LLM generation including latency and token usage.

    Token counts are sourced from provider metadata when available without guessing.
    """

    def __init__(self, workflow_id: str) -> None:
        self._workflow_id = workflow_id

    def on_llm_start(self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any) -> None:
        """Record the start of an LLM call."""
        run_id = str(kwargs.get("run_id", uuid4()))
        logger.info(
            "llm_start",
            workflow_id=self._workflow_id,
            run_id=run_id,
            prompt_count=len(prompts),
        )

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Record completion metadata including token usage when present."""
        run_id = str(kwargs.get("run_id", uuid4()))
        llm_output = response.llm_output or {}
        token_usage = llm_output.get("token_usage")
        logger.info(
            "llm_end",
            workflow_id=self._workflow_id,
            run_id=run_id,
            token_usage=token_usage,
            model=llm_output.get("model_name"),
        )

"""LLM factory helpers for OpenAI and Anthropic backends."""

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import Settings


def get_chat_model(settings: Settings) -> BaseChatModel | None:
    """
    Instantiate the configured chat model when API credentials are present.

    Args:
        settings: Application settings describing provider and model names.

    Returns:
        A LangChain chat model, or None when no provider can be configured.
    """
    if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=0.2,
        )
    if settings.openai_api_key:
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.2,
        )
    return None

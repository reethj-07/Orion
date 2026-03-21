"""LLM factory helpers: local Ollama (free) or OpenAI / Anthropic APIs."""

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.config import Settings


def get_chat_model(settings: Settings) -> BaseChatModel | None:
    """
    Instantiate the configured chat model.

    Ollama requires no API key (local inference). OpenAI / Anthropic require keys.

    Args:
        settings: Application settings describing provider and model names.

    Returns:
        A LangChain chat model, or None when no provider can be configured.
    """
    if settings.llm_provider == "ollama":
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.2,
        )
    if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=0.2,
        )
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.2,
        )
    return None

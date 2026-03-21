"""Application settings loaded from environment variables via Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

WebSearchProvider = Literal["duckduckgo", "tavily", "none"]
EmbeddingProvider = Literal["openai", "ollama"]
LLMProvider = Literal["openai", "anthropic", "ollama"]


class Settings(BaseSettings):
    """Strongly typed application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="Orion", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(..., alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=15, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")

    database_url: str = Field(..., alias="DATABASE_URL")
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongodb_db: str = Field(default="orion", alias="MONGODB_DB")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/1", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", alias="CELERY_RESULT_BACKEND")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(
        default="claude-3-5-haiku-20241022",
        alias="ANTHROPIC_MODEL",
    )
    llm_provider: LLMProvider = Field(default="ollama", alias="LLM_PROVIDER")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    embedding_provider: EmbeddingProvider = Field(default="ollama", alias="EMBEDDING_PROVIDER")

    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.2", alias="OLLAMA_MODEL")
    ollama_embed_model: str = Field(default="nomic-embed-text", alias="OLLAMA_EMBED_MODEL")

    web_search_provider: WebSearchProvider = Field(default="duckduckgo", alias="WEB_SEARCH_PROVIDER")
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")

    cors_origins: str = Field(
        default="http://localhost:3000",
        alias="CORS_ORIGINS",
    )
    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    rate_limit_default: str = Field(default="100/minute", alias="RATE_LIMIT_DEFAULT")
    ingest_storage_dir: str = Field(default="/tmp/orion-ingest", alias="INGEST_STORAGE_DIR")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: str | list[str]) -> str:
        """Normalize CORS origins to a comma-separated string for parsing."""
        if isinstance(value, list):
            return ",".join(value)
        return str(value)

    def cors_origin_list(self) -> list[str]:
        """Return parsed CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance (singleton per process)."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear the settings cache (used in tests)."""
    get_settings.cache_clear()

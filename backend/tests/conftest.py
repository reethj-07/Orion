"""Shared pytest fixtures for Orion backend tests."""

import os
from collections.abc import Iterator

import pytest

from app.core.config import Settings, clear_settings_cache, get_settings


@pytest.fixture(autouse=True)
def _configure_test_env() -> Iterator[None]:
    """
    Provide deterministic environment variables for settings-dependent tests.

    Yields:
        Control after environment mutation.
    """
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-jwt-signing-32b")
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://orion:orion@localhost:5432/orion_test")
    os.environ.setdefault("MONGODB_URI", "mongodb://orion:orion@localhost:27017/?authSource=admin")
    os.environ.setdefault("MONGODB_DB", "orion_test")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
    clear_settings_cache()
    yield
    clear_settings_cache()


@pytest.fixture()
def settings() -> Settings:
    """Return a cached Settings instance bound to the test environment."""
    return get_settings()

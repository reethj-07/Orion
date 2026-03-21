"""Integration tests using Docker services or testcontainers."""

import pytest


@pytest.mark.skip(reason="Integration suite requires running Docker Compose services.")
def test_placeholder_integration() -> None:
    """Placeholder ensuring the integration package is collected by pytest."""
    assert True

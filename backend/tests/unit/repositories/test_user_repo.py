"""Unit tests for UserRepository query construction."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.engine import Result

from app.repositories.pg.user_repo import UserRepository


@pytest.mark.asyncio
async def test_get_by_email_returns_user_when_present() -> None:
    """get_by_email should return the scalar result from the database."""
    session = AsyncMock()
    user = MagicMock()
    user.email = "found@example.com"
    result = MagicMock(spec=Result)
    result.scalar_one_or_none.return_value = user
    session.execute = AsyncMock(return_value=result)

    repo = UserRepository(session)
    found = await repo.get_by_email("Found@Example.com")

    assert found is user
    session.execute.assert_awaited_once()

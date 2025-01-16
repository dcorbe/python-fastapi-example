"""Unit tests for user endpoint functionality."""

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from user import User

from .user import get_current_user_details

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_user() -> MagicMock:
    """Create a mock user."""
    mock_user = MagicMock(spec=User)
    mock_user.id = uuid4()
    mock_user.email = "test@example.com"
    mock_user.email_verified = True
    mock_user.created_at = datetime.now(UTC)
    mock_user.last_login = datetime.now(UTC)
    mock_user.failed_login_attempts = 0
    mock_user.locked_until = None
    return mock_user


async def test_user_endpoint_success(mock_user: MagicMock) -> None:
    """Test successful user info retrieval."""
    result = await get_current_user_details(mock_user)

    assert result is not None
    assert result.id == mock_user.id
    assert result.email == mock_user.email
    assert result.email_verified == mock_user.email_verified
    assert result.created_at == mock_user.created_at
    assert result.last_login == mock_user.last_login


@pytest.mark.parametrize(
    "field,value",
    [
        ("email", "new@example.com"),
        ("email_verified", False),
        ("failed_login_attempts", 3),
    ],
)
async def test_user_endpoint_field_changes(
    mock_user: MagicMock,
    field: str,
    value: str | bool | int,
) -> None:
    """Test that endpoint correctly reflects user field changes."""
    setattr(mock_user, field, value)
    result = await get_current_user_details(mock_user)

    assert getattr(result, field) == value

"""Unit tests for the hello endpoint."""
import uuid
from unittest.mock import MagicMock
import pytest
from example.hello import hello_world, Hello
from user import User

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_user() -> MagicMock:
    """Create a mock authenticated user."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    return user


async def test_hello_world(mock_user: MagicMock) -> None:
    """Test the hello world endpoint returns correct message and user ID."""
    result = await hello_world(mock_user)
    
    assert isinstance(result, Hello)
    assert result.message == "This is a protected endpoint"
    assert result.user_id == mock_user.id

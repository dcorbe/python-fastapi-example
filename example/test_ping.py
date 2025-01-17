"""Unit tests for the ping endpoint."""

import pytest

from example.ping import Ping, ping_endpoint

pytestmark = pytest.mark.asyncio


async def test_ping_endpoint() -> None:
    """Test the ping endpoint returns 'pong'."""
    result = await ping_endpoint()
    assert isinstance(result, Ping)
    assert result.ping == "pong"

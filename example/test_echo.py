"""Unit tests for the echo endpoint."""

import json
import pytest
from fastapi import Request
from fastapi.responses import JSONResponse


@pytest.mark.asyncio
async def test_echo() -> None:
    """Test basic echo functionality."""
    # Create a simple request mock
    request = Request(
        scope={
            "type": "http",
            "method": "POST",
            "headers": [(b"content-type", b"application/json")],
            "path": "/echo",
        }
    )
    request._body = b'{"test": "data"}'

    # Mock authenticated user
    user = type("User", (), {"id": 1, "email": "test@example.com"})()

    # Import here to avoid circular imports
    from example.echo import echo

    response: JSONResponse = await echo(request, user)

    # Parse response
    content = json.loads(bytes(response.body))

    # Basic assertions
    assert content["method"] == "POST"
    assert content["body"] == '{"test": "data"}'
    assert content["headers"]["content-type"] == "application/json"


@pytest.mark.asyncio
async def test_echo_empty_body() -> None:
    """Test echo with empty body."""
    request = Request(
        scope={
            "type": "http",
            "method": "POST",
            "headers": [(b"content-type", b"application/json")],
            "path": "/echo",
        }
    )
    request._body = b""

    user = type("User", (), {"id": 1, "email": "test@example.com"})()

    from example.echo import echo

    response: JSONResponse = await echo(request, user)

    content = json.loads(bytes(response.body))
    assert content["body"] is None

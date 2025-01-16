"""Unit tests for the error endpoint."""

import pytest
from fastapi import HTTPException

from example.error import error_message

pytestmark = pytest.mark.asyncio


async def test_error_message() -> None:
    """Test that the error endpoint raises an HTTPException with correct status code and message."""
    with pytest.raises(HTTPException) as exc_info:
        await error_message()

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "You are not authorized to access this resource"

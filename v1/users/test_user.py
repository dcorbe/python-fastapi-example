"""Tests for user endpoints."""

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from main.app import Application

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_user() -> MagicMock:
    """Create a mock user."""
    user = MagicMock()
    user.id = UUID("550e8400-e29b-41d4-a716-446655440000")
    user.email = "test@example.com"
    user.email_verified = True
    user.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    user.last_login = datetime(2024, 1, 2, tzinfo=UTC)
    user.failed_login_attempts = 0
    user.locked_until = None
    user.password_hash = "not_included_in_response"
    return user


@pytest.fixture
def app() -> Application:
    """Create test FastAPI application."""
    app = Application()
    app.init()
    return app


@pytest.fixture
def client(
    app: Application, mock_user: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Create test client with mocked authentication."""

    async def mock_get_current_user() -> MagicMock:
        return mock_user

    monkeypatch.setattr(
        "auth.token.get_current_user",
        mock_get_current_user,
    )
    return TestClient(app)


def test_get_current_user(client: TestClient, mock_user: MagicMock) -> None:
    """Test /me endpoint returns current user without password hash."""
    response = client.get("/v1/users/me")
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["id"] == str(mock_user.id)
    assert user_data["email"] == mock_user.email
    assert user_data["email_verified"] == mock_user.email_verified
    assert "password_hash" not in user_data
    assert user_data["failed_login_attempts"] == mock_user.failed_login_attempts
    assert user_data["locked_until"] is None

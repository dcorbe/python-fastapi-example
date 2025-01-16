"""Unit tests for auth login functionality."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import AuthConfig
from auth.service import AuthService
from user.model import User

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db() -> AsyncMock:
    """Create a mock database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def auth_service() -> AuthService:
    """Create AuthService instance for testing."""
    config = AuthConfig(
        jwt_secret_key="test_secret",
        jwt_algorithm="HS256",
        access_token_expire_minutes=30,
        max_login_attempts=5,
        lockout_minutes=15,
    )
    return AuthService(config)


async def test_authenticate_user_success(
    mock_db: AsyncMock, auth_service: AuthService
) -> None:
    """Test successful user authentication."""
    # Setup mock user
    mock_user = MagicMock(spec=User)
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    mock_user.password_hash = auth_service.hash_password("testpassword")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute.return_value = mock_result

    user = await auth_service.authenticate_user(
        "test@example.com", "testpassword", mock_db
    )

    assert user is not None
    assert user.email == "test@example.com"


async def test_authenticate_user_invalid_password(
    mock_db: AsyncMock, auth_service: AuthService
) -> None:
    """Test authentication with invalid password."""
    # Setup mock user
    mock_user = MagicMock(spec=User)
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    mock_user.password_hash = auth_service.hash_password("testpassword")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate_user(
            "test@example.com", "wrongpassword", mock_db
        )

    assert exc_info.value.status_code == 401


async def test_authenticate_user_not_found(
    mock_db: AsyncMock, auth_service: AuthService
) -> None:
    """Test authentication with non-existent user."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate_user(
            "nonexistent@example.com", "testpassword", mock_db
        )

    assert exc_info.value.status_code == 401

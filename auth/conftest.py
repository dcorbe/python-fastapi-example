"""Test fixtures for auth module."""

from datetime import UTC, datetime
from typing import Any, Union
from unittest.mock import AsyncMock, MagicMock

import pytest

from v1.users.models import User

from .config import RedisConfig
from .models import AuthConfig
from .redis import AsyncRedis, RedisService


class MockRedis(AsyncRedis):
    """Mock Redis client."""

    def __init__(self) -> None:
        """Initialize storage."""
        self._storage: dict[str, str] = {}
        self.connection_pool = MagicMock()
        self.connection_pool.connection_kwargs = {"db": 0}

    async def setex(self, key: str, ttl: int, value: str) -> bool:
        """Mock setex that stores tokens."""
        self._storage[key] = value
        return True

    async def exists(self, key: str) -> int:
        """Mock exists that checks stored tokens."""
        return 1 if key in self._storage else 0

    async def get(self, key: str) -> Union[str, None]:
        """Mock get that returns stored tokens."""
        return self._storage.get(key)

    async def aclose(self) -> None:
        """Mock close."""
        pass


@pytest.fixture
def mock_db() -> AsyncMock:
    """Create a mock database session."""

    async def execute_mock(*args: Any, **kwargs: Any) -> AsyncMock:
        result = AsyncMock()

        # Configure the mock to return test_user for user lookups
        test_user = User(
            id=1,
            email="test@example.com",
            password_hash="some_hash",
            created_at=datetime.now(UTC),
            last_login=None,
        )
        result.scalar_one_or_none.return_value = test_user
        return result

    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.execute = AsyncMock(side_effect=execute_mock)
    return db


@pytest.fixture
def auth_config() -> AuthConfig:
    """Create test auth config."""
    return AuthConfig(
        jwt_secret_key="test_secret",
        jwt_algorithm="HS256",
        access_token_expire_minutes=30,
        max_login_attempts=3,
        lockout_minutes=15,
    )


@pytest.fixture
def mock_redis() -> MockRedis:
    """Create a mock Redis service."""
    return MockRedis()


@pytest.fixture
def redis_service(mock_redis: MockRedis) -> RedisService:
    """Create Redis service with mock."""
    service = RedisService(RedisConfig())
    service.redis = mock_redis
    return service


@pytest.fixture
def test_user() -> User:
    """Create a test user."""
    return User(
        id=1,
        email="test@example.com",
        password_hash="some_hash",
        created_at=datetime.now(UTC),
        last_login=None,
    )

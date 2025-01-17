"""Test authentication endpoints."""

from datetime import UTC, datetime, timedelta
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from v1.users.models import User

from .config import RedisConfig
from .dependencies import set_auth_service, set_redis_service
from .models import AuthConfig
from .redis import AsyncRedis, RedisService
from .routes import AuthRouter
from .service import AuthService


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

    async def get(self, key: str) -> str | None:
        """Mock get that returns stored tokens."""
        return self._storage.get(key)

    async def aclose(self) -> None:
        """Mock close."""
        pass


pytestmark = pytest.mark.asyncio


@pytest.fixture
def app(auth_service: AuthService, redis_service: RedisService) -> FastAPI:
    """Create test FastAPI application."""
    app = FastAPI()
    # Set services in dependencies
    set_auth_service(auth_service)
    set_redis_service(redis_service)
    # Add routes
    auth_router = AuthRouter(auth_service)
    app.include_router(auth_router.router)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


async def test_logout_endpoint_success(
    client: TestClient,
    auth_service: AuthService,
    redis_service: RedisService,
    test_user: User,
) -> None:
    """Test successful logout."""
    # Create a valid token
    token = auth_service.create_access_token({"sub": test_user.email})
    cleaned_token = redis_service._clean_token(token)

    # Configure mock Redis
    assert isinstance(redis_service.redis, MockRedis)  # Type check for mypy
    redis_service.redis._storage = {}

    # Test logout endpoint
    response = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "Successfully logged out"}

    # Verify token was blacklisted
    key = redis_service._get_blacklist_key(cleaned_token)
    assert await redis_service.redis.exists(key) == 1
    assert await redis_service.redis.get(key) == cleaned_token


async def test_logout_endpoint_no_token(client: TestClient) -> None:
    """Test logout without token."""
    response = client.post("/auth/logout")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


async def test_logout_endpoint_invalid_token(client: TestClient) -> None:
    """Test logout with invalid token."""
    response = client.post(
        "/auth/logout", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


async def test_logout_endpoint_expired_token(
    client: TestClient,
    auth_service: AuthService,
) -> None:
    """Test logout with expired token."""
    # Create an expired token
    expired_time = datetime.now(UTC) - timedelta(minutes=1)
    token = jwt.encode(
        {"sub": "test@example.com", "exp": expired_time.timestamp()},
        auth_service.config.jwt_secret_key,
        algorithm=auth_service.config.jwt_algorithm,
    )

    response = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]


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
def test_user() -> User:
    """Create a test user."""
    return User(
        email="test@example.com",
        password_hash="some_hash",  # The actual hash doesn't matter as we're mocking verify_password
        created_at=datetime.now(UTC),
        last_login=None,
    )


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
def auth_service(
    auth_config: AuthConfig, redis_service: RedisService
) -> Generator[AuthService, None, None]:
    """Create test auth service with mocked password verification."""
    with patch.object(AuthService, "verify_password", return_value=True) as mock:
        service = AuthService(auth_config, redis_service)
        mock.side_effect = lambda password, hash: password == "password123"
        yield service


async def test_authentication_success(
    auth_service: AuthService,
    mock_db: AsyncMock,
    test_user: User,
) -> None:
    """Test successful authentication."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_db.execute.return_value = mock_result

    user = await auth_service.authenticate_user(test_user.email, "password123", mock_db)

    assert user.email == test_user.email
    assert user.last_login is not None
    await mock_db.commit()


async def test_authentication_failure_invalid_password(
    auth_service: AuthService,
    mock_db: AsyncMock,
    test_user: User,
) -> None:
    """Test failed authentication with wrong password."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate_user(test_user.email, "wrong_password", mock_db)
    assert exc_info.value.status_code == 401
    assert "Incorrect username or password" in exc_info.value.detail


async def test_authentication_failure_invalid_user(
    auth_service: AuthService,
    mock_db: AsyncMock,
) -> None:
    """Test failed authentication with non-existent user."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate_user(
            "nonexistent@example.com", "password123", mock_db
        )
    assert exc_info.value.status_code == 401
    assert "Incorrect username or password" in exc_info.value.detail


async def test_blacklist_token_success(
    auth_service: AuthService,
    redis_service: RedisService,
) -> None:
    """Test successful token blacklisting."""
    # Create a token that expires in 5 minutes
    token = auth_service.create_access_token({"sub": "test@example.com"})
    cleaned_token = redis_service._clean_token(token)

    # Configure mock Redis
    assert isinstance(redis_service.redis, MockRedis)  # Type check for mypy
    redis_service.redis._storage = {}

    # Blacklist the token
    await auth_service.blacklist_token(token)

    # Verify token was blacklisted
    key = redis_service._get_blacklist_key(cleaned_token)
    assert await redis_service.redis.exists(key) == 1
    assert await redis_service.redis.get(key) == cleaned_token


async def test_blacklist_expired_token(
    auth_service: AuthService,
    redis_service: RedisService,
) -> None:
    """Test handling of expired token during blacklisting."""
    # Create token that's already expired
    expired_time = datetime.now(UTC) - timedelta(minutes=1)
    token = jwt.encode(
        {"sub": "test@example.com", "exp": expired_time.timestamp()},
        auth_service.config.jwt_secret_key,
        algorithm=auth_service.config.jwt_algorithm,
    )

    # Attempt to blacklist expired token
    await auth_service.blacklist_token(token)

    # Verify Redis was not called
    assert isinstance(redis_service.redis, MockRedis)  # Type check for mypy
    assert not redis_service.redis._storage


async def test_blacklist_invalid_token(
    auth_service: AuthService,
    redis_service: RedisService,
) -> None:
    """Test handling of invalid token during blacklisting."""
    # Attempt to blacklist invalid token
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.blacklist_token("invalid_token")
    assert exc_info.value.status_code == 401
    assert "Invalid token format" in exc_info.value.detail

    # Verify Redis was not called
    assert isinstance(redis_service.redis, MockRedis)  # Type check for mypy
    assert not redis_service.redis._storage


async def test_decode_blacklisted_token(
    auth_service: AuthService,
    redis_service: RedisService,
) -> None:
    """Test that blacklisted tokens are rejected."""
    # Create a token
    token = auth_service.create_access_token({"sub": "test@example.com"})
    cleaned_token = redis_service._clean_token(token)

    # Configure mock Redis to simulate blacklisted token
    assert isinstance(redis_service.redis, MockRedis)  # Type check for mypy
    key = redis_service._get_blacklist_key(cleaned_token)
    redis_service.redis._storage = {key: cleaned_token}

    # Attempt to decode blacklisted token
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.decode_token(token)
    assert exc_info.value.status_code == 401
    assert "Token has been invalidated" in exc_info.value.detail


async def test_lockout_after_max_attempts(
    auth_service: AuthService,
    mock_db: AsyncMock,
    test_user: User,
) -> None:
    """Test account lockout after maximum failed attempts."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_db.execute.return_value = mock_result

    # Attempt authentication multiple times with wrong password
    for _ in range(auth_service.config.max_login_attempts):
        with pytest.raises(HTTPException):
            await auth_service.authenticate_user(
                test_user.email, "wrong_password", mock_db
            )

    # Next attempt should result in lockout
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate_user(test_user.email, "password123", mock_db)
    assert exc_info.value.status_code == 401
    assert "Account is locked" in exc_info.value.detail

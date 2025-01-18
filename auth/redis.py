"""Redis service for token blacklisting."""

import hashlib
from datetime import timedelta
from typing import Any, Protocol, Union, runtime_checkable

import redis.asyncio as redis
from fastapi import HTTPException, status

from config.logging import redis_log

from .config import RedisConfig


@runtime_checkable
class AsyncRedis(Protocol):
    """Protocol for Redis async methods."""

    connection_pool: Any

    async def setex(self, key: str, ttl: int, value: str) -> bool: ...
    async def exists(self, key: str) -> int: ...
    async def get(self, key: str) -> Union[str, None]: ...
    async def aclose(self) -> None: ...


class RedisService:
    """Service for managing Redis operations."""

    def __init__(self, config: RedisConfig) -> None:
        """Initialize Redis connection."""
        try:
            redis_log(
                f"Connecting to Redis at {config.host}:{config.port} using database {config.db}"
            )
            self.redis: AsyncRedis = redis.Redis(  # type: ignore
                host=config.host,
                port=config.port,
                db=config.db,  # Use configured database
                password=config.password,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            redis_log("Redis client initialized")
        except Exception as e:
            redis_log(f"Failed to initialize Redis connection: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize Redis connection",
            )

    async def test_connection(self) -> None:
        """Test Redis connection by setting and getting a test key."""
        try:
            redis_log("\n=== Testing Redis Connection ===")
            test_key = "test:connection"
            test_value = "1"
            db = self.redis.connection_pool.connection_kwargs["db"]
            redis_log(f"1. Setting test key: {test_key} in database {db}")

            await self.redis.setex(test_key, 60, test_value)
            redis_log("2. Key set successfully")

            result = await self.redis.get(test_key)
            redis_log(f"3. Retrieved value: {result}")

            if result != test_value:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Redis test failed: value mismatch",
                )

            redis_log("4. Test successful")
            redis_log("=== Redis Connection Test Complete ===\n")
        except Exception as e:
            redis_log(f"Redis connection test failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Redis connection test failed: {str(e)}",
            )

    def _clean_token(self, token: str) -> str:
        """Clean token by removing Bearer prefix and whitespace."""
        if token.startswith("Bearer "):
            token = token[7:]
        return token.strip()

    def _get_blacklist_key(self, token: str) -> str:
        """Generate a consistent Redis key for a token."""
        # Clean token first
        cleaned_token = self._clean_token(token)

        # Use a prefix to isolate blacklist keys and a hash for the token
        token_hash = hashlib.sha256(cleaned_token.encode()).hexdigest()
        return f"auth:blacklist:{token_hash}"

    async def _ensure_connection(self) -> None:
        """Ensure Redis connection is working."""
        try:
            redis_log("\n=== Ensuring Redis Connection ===")
            db = self.redis.connection_pool.connection_kwargs["db"]
            redis_log(f"1. Testing connection to database {db}...")
            await self.redis.exists("test")
            redis_log("2. Connection OK")
            redis_log("=== Connection Check Complete ===\n")
        except Exception as e:
            redis_log(f"Redis connection error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Redis connection error: {str(e)}",
            )

    async def add_to_blacklist(self, token: str, expire_in: timedelta) -> None:
        """Add a token to the blacklist with expiration."""
        try:
            redis_log("\n=== Adding Token to Blacklist ===")
            redis_log(f"1. Original token: {token}")

            # Clean token and generate key
            cleaned_token = self._clean_token(token)
            redis_log(f"2. Cleaned token: {cleaned_token}")

            key = self._get_blacklist_key(
                cleaned_token
            )  # Use cleaned token for key generation
            redis_log(f"3. Using key: {key}")

            # Set the key with expiration
            await self.redis.setex(
                key,
                int(expire_in.total_seconds()),
                cleaned_token,  # Store cleaned token for verification
            )

            # Verify the key was set and value matches
            stored_token = await self.redis.get(key)
            redis_log(f"4. Stored token: {stored_token}")

            if not stored_token or stored_token != cleaned_token:
                redis_log("ERROR: Failed to verify blacklist key!")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to verify blacklisted token",
                )

            redis_log("5. Token verified in blacklist")
            redis_log("6. Token successfully blacklisted")
            redis_log("=== Blacklisting Complete ===\n")
        except HTTPException:
            raise
        except Exception as e:
            redis_log(f"Error blacklisting token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to blacklist token: {str(e)}",
            )

    async def is_blacklisted(self, token: str) -> bool:  # explicitly returning bool
        """Check if a token is blacklisted."""
        try:
            redis_log("\n=== Checking Token Blacklist ===")
            redis_log(f"1. Original token: {token}")

            # Clean token and generate key
            cleaned_token = self._clean_token(token)
            redis_log(f"2. Cleaned token: {cleaned_token}")

            key = self._get_blacklist_key(
                cleaned_token
            )  # Use cleaned token for key generation
            redis_log(f"3. Using key: {key}")

            # Get stored token
            stored_token = await self.redis.get(key)
            redis_log(f"4. Stored token: {stored_token}")

            is_blacklisted = bool(stored_token and stored_token == cleaned_token)
            redis_log(f"5. Is blacklisted? {is_blacklisted}")
            redis_log("=== Blacklist Check Complete ===\n")
            return is_blacklisted
        except Exception as e:
            redis_log(f"Error checking blacklist: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def close(self) -> None:
        """Close Redis connection."""
        await self.redis.aclose()  # Using aclose() instead of close()

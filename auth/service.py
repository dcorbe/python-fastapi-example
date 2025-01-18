"""Authentication service."""

from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Union

import jwt
from fastapi import HTTPException, status
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.logging import logger

from .models import AuthConfig, LoginAttempt, TokenData
from .password import hash_password, verify_password
from .redis import RedisService


class AuthService:
    """Service for handling authentication and token management."""

    def __init__(self, config: AuthConfig, redis_service: RedisService) -> None:
        self.config = config
        self.redis_service = redis_service
        self._login_attempts: Dict[str, LoginAttempt] = {}

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            return verify_password(plain_password, hashed_password)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_426_UPGRADE_REQUIRED,
                detail="Account requires password reset",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return hash_password(password)

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a new JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(
            minutes=self.config.access_token_expire_minutes
        )
        to_encode.update({"exp": expire})

        return jwt.encode(
            to_encode, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm
        )

    def _clean_token(self, token: str) -> str:
        """Remove Bearer prefix and any whitespace."""
        from config import get_settings

        settings = get_settings()

        if settings.AUTH_DEBUG:
            logger.debug("=== Cleaning Token ===")
            logger.debug("1. Original token: %s", token)

        # Remove 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
            if settings.AUTH_DEBUG:
                logger.debug("2. Removed Bearer prefix")

        # Remove any whitespace
        token = token.strip()
        if settings.AUTH_DEBUG:
            logger.debug("3. Final cleaned token: %s", token)
            logger.debug("=== Token Cleaning Complete ===")
        return token

    async def _check_blacklist(self, token: str) -> None:
        """Check if a token is blacklisted."""
        try:
            if await self.redis_service.is_blacklisted(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been invalidated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except HTTPException as e:
            if e.status_code == status.HTTP_401_UNAUTHORIZED:
                raise
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def decode_token(self, token: str, check_blacklist: bool = True) -> TokenData:
        """Decode and validate a JWT token."""
        try:
            cleaned_token = self._clean_token(token)

            # First try to decode the token to catch any JWT-related errors
            payload = jwt.decode(
                cleaned_token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
            )

            # Then check blacklist if required
            if check_blacklist:
                await self._check_blacklist(cleaned_token)

            return TokenData(**payload)

        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def _get_token_ttl(self, token: str) -> Union[timedelta, None]:
        """Get the time-to-live for a token."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
            )
            exp = datetime.fromtimestamp(payload["exp"], UTC)
            ttl = exp - datetime.now(UTC)
            if ttl.total_seconds() <= 0:
                return None  # Expired token
            return ttl
        except ExpiredSignatureError:
            return None  # Expired token
        except PyJWTError:
            raise HTTPException(  # Invalid token format
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def blacklist_token(self, token: str) -> None:
        """Add a token to the blacklist."""
        try:
            cleaned_token = self._clean_token(token)

            # Get token TTL (will raise HTTPException for invalid tokens)
            ttl = self._get_token_ttl(cleaned_token)
            if not ttl:
                return  # Token is expired

            # Check if already blacklisted
            if await self.redis_service.is_blacklisted(cleaned_token):
                return

            # Add to blacklist
            await self.redis_service.add_to_blacklist(cleaned_token, ttl)

        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def authenticate_user(
        self, email: str, password: str, session: AsyncSession
    ) -> Any:
        """Authenticate a user."""
        # Import here to avoid circular import
        from v1.users.models import User

        # Check for account lockout
        if self._is_account_locked(email):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is locked. Please try again later",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user
        stmt = select(User).where(User.email.ilike(email))
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            self._record_failed_attempt(email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not self.verify_password(password, user.password_hash):
            self._record_failed_attempt(email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Clear failed attempts on success
        self._clear_failed_attempts(email)

        # Update last login
        user.last_login = datetime.now(UTC)
        await session.commit()

        return user

    def _is_account_locked(self, email: str) -> bool:
        """Check if an account is locked."""
        attempt = self._login_attempts.get(email)
        if not attempt:
            return False

        if attempt.locked_until and datetime.now(UTC) < attempt.locked_until:
            return True

        return False

    def _record_failed_attempt(self, email: str) -> None:
        """Record a failed login attempt."""
        attempt = self._login_attempts.get(email, LoginAttempt(email=email))
        attempt.attempts += 1
        attempt.last_attempt = datetime.now(UTC)

        if attempt.attempts >= self.config.max_login_attempts:
            attempt.locked_until = datetime.now(UTC) + timedelta(
                minutes=self.config.lockout_minutes
            )

        self._login_attempts[email] = attempt

    def _clear_failed_attempts(self, email: str) -> None:
        """Clear failed login attempts for a user."""
        if email in self._login_attempts:
            del self._login_attempts[email]

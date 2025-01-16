"""Authentication service."""

from datetime import datetime, timedelta, UTC
from typing import Dict, Any
import jwt
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from user.model import User
from .models import AuthConfig, TokenData, LoginAttempt
from .password import hash_password, verify_password


class AuthService:
    """Service for handling authentication and token management."""

    def __init__(self, config: AuthConfig):
        self.config = config
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

    def decode_token(self, token: str) -> TokenData:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
            )
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

    async def authenticate_user(
        self, email: str, password: str, session: AsyncSession
    ) -> User:
        """Authenticate a user."""
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

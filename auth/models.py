"""Authentication models."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    """Configuration for authentication system"""

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    max_login_attempts: int = 5
    lockout_minutes: int = 15


class Token(BaseModel):
    """OAuth2 token response"""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """JWT token payload"""

    sub: str | None = None
    exp: datetime | None = None


class LoginAttempt(BaseModel):
    """Track login attempts and lockouts"""

    email: str
    attempts: int = 0
    locked_until: datetime | None = None
    last_attempt: datetime = Field(default_factory=lambda: datetime.now(UTC))

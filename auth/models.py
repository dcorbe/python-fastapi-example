"""Authentication models."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class AuthConfig(BaseModel):
    """Configuration for authentication system"""

    jwt_secret_key: str = Field(...)
    jwt_algorithm: str = Field(...)
    access_token_expire_minutes: int = Field(...)
    max_login_attempts: int = Field(...)
    lockout_minutes: int = Field(...)

    @classmethod
    def from_env(cls) -> "AuthConfig":
        from config import get_settings

        settings = get_settings()

        if not settings.JWT_SECRET:
            raise ValueError("JWT_SECRET environment variable must be set")

        return cls(
            jwt_secret_key=settings.JWT_SECRET,
            jwt_algorithm=settings.JWT_ALGORITHM,
            access_token_expire_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
            max_login_attempts=settings.MAX_LOGIN_ATTEMPTS,
            lockout_minutes=settings.LOCKOUT_MINUTES,
        )


class Token(BaseModel):
    """OAuth2 token response"""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model."""

    sub: str | None = None
    exp: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class LoginAttempt(BaseModel):
    """Track login attempts and lockouts"""

    email: str
    attempts: int = 0
    locked_until: datetime | None = None
    last_attempt: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BlacklistedToken(BaseModel):
    """Represents a blacklisted token"""

    token: str
    blacklisted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

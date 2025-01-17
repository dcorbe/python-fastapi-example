from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database Configuration
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1  # Use a separate database for token blacklisting
    REDIS_PASSWORD: str | None = None

    # SMTP Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""
    TO_EMAILS: str = ""
    ERROR_RATE_LIMIT_PERIOD: int = Field(default=300, gt=0)
    ERROR_RATE_LIMIT_COUNT: int = Field(default=10, gt=0)

    # Auth Configuration
    MAX_LOGIN_ATTEMPTS: int = Field(default=5, gt=0)
    LOCKOUT_MINUTES: int = Field(default=15, gt=0)

    # JWT Configuration
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)

    # Logging Configuration
    SQL_LOGGING: bool = Field(default=False, description="Enable SQL query logging")
    DEBUG_CRASH_REPORTER: bool = Field(
        default=False, description="Enable debug logging for crash reporter"
    )
    DEBUG_REDIS: bool = Field(default=False, description="Enable Redis debug logging")
    DEBUG_JWT: bool = Field(default=False, description="Enable JWT debug logging")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    def get_from_email(self) -> str:
        return self.FROM_EMAIL or self.SMTP_USERNAME

    def get_email_list(self) -> List[str]:
        return [email.strip() for email in self.TO_EMAILS.split(",") if email.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

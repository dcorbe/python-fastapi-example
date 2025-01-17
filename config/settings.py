import json
import logging
from functools import lru_cache
from typing import List

from email_validator import EmailNotValidError, validate_email
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def parse_json_list(value: str) -> List[str] | None:
    """Parse a JSON string into a list of strings."""
    if not (value.startswith("[") and value.endswith("]")):
        return None
    try:
        result = json.loads(value)
        if isinstance(result, list):
            return result
        logger.warning("JSON value is not a list")
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON", exc_info=True)
    return None


class Settings(BaseSettings):
    # Database Configuration
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_URL: str
    DB_SQL_LOGGING: bool = Field(default=False, description="Enable SQL query logging")

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1  # Use a separate database for token blacklisting
    REDIS_PASSWORD: str | None = None
    REDIS_DEBUG: bool = Field(default=False, description="Enable Redis debug logging")

    # Authentication Configuration
    AUTH_SECRET: str
    AUTH_ALGORITHM: str = "HS256"
    AUTH_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)
    AUTH_MAX_LOGIN_ATTEMPTS: int = Field(default=5, gt=0)
    AUTH_LOCKOUT_MINUTES: int = Field(default=15, gt=0)
    AUTH_DEBUG: bool = Field(default=False, description="Enable JWT debug logging")

    # Email Configuration
    EMAIL_HOST: str = Field(default="smtp.gmail.com")
    EMAIL_PORT: int = Field(
        default=465, description="Must be either 465 (SSL) or 587 (STARTTLS)"
    )
    EMAIL_USERNAME: str = Field(default="")
    EMAIL_PASSWORD: str = Field(default="")
    EMAIL_FROM: str = Field(default="")
    EMAIL_TO: str = Field(default="")

    @field_validator("EMAIL_PORT")
    def validate_email_port(cls, v: int) -> int:
        if v not in [465, 587]:
            raise ValueError("EMAIL_PORT must be either 465 (SSL) or 587 (STARTTLS)")
        return v

    @field_validator("EMAIL_USERNAME")
    def validate_email_username(cls, v: str) -> str:
        if not v:
            raise ValueError("EMAIL_USERNAME cannot be empty")
        return v

    @field_validator("EMAIL_PASSWORD")
    def validate_email_password(cls, v: str) -> str:
        if not v:
            raise ValueError("EMAIL_PASSWORD cannot be empty")
        return v

    @field_validator("EMAIL_FROM")
    def validate_email_from(cls, v: str) -> str:
        if not v:
            raise ValueError("EMAIL_FROM cannot be empty")
        try:
            email_info = validate_email(v, check_deliverability=False)
            return email_info.normalized
        except EmailNotValidError:
            raise ValueError(f"Invalid email address: {v}")

    @field_validator("EMAIL_TO")
    def validate_email_to(cls, v: str) -> str:
        if not v:
            raise ValueError("EMAIL_TO cannot be empty")
        emails = [email.strip() for email in v.split(",") if email.strip()]
        if not emails:
            raise ValueError("EMAIL_TO must contain at least one recipient")
        try:
            validated_emails = []
            for email in emails:
                email_info = validate_email(email, check_deliverability=False)
                validated_emails.append(email_info.normalized)
            return ",".join(validated_emails)
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email address in EMAIL_TO: {str(e)}")

    # Error Configuration
    ERROR_DEBUG: bool = Field(
        default=False, description="Enable debug logging for crash reporter"
    )
    ERROR_RATE_LIMIT_PERIOD: int = Field(default=300, gt=0)
    ERROR_RATE_LIMIT_COUNT: int = Field(default=10, gt=0)

    # FastAPI Configuration
    API_TITLE: str = "BSS Backend API"
    API_DESCRIPTION: str = "Bridge Security Solutions Backend API"
    API_VERSION: str = "0.1.0"

    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        description="List of allowed CORS origins. Use * for all origins (development only) or comma-separated URLs",
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    CORS_ALLOW_METHODS: List[str] = Field(default=["*"])
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"])

    @field_validator("CORS_ORIGINS", mode="before")
    def validate_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, list):
            return v
        if not v or v == "*" or not isinstance(v, str):
            return ["*"]

        # Try parsing as JSON first
        if v.startswith("["):
            json_result = parse_json_list(v)
            if json_result is not None:
                return json_result

        # Fall back to comma-separated format
        origins = [origin.strip() for origin in v.split(",") if origin.strip()]
        return origins if origins else ["*"]

    @field_validator("CORS_ALLOW_METHODS", mode="before")
    def validate_cors_methods(cls, v: str | List[str]) -> List[str]:
        default_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"]
        if isinstance(v, list):
            return v
        if not v or v == "*" or not isinstance(v, str):
            return default_methods

        # Try parsing as JSON first
        if v.startswith("["):
            json_result = parse_json_list(v)
            if json_result is not None:
                return [m.strip().upper() for m in json_result if m.strip()]

        # Fall back to comma-separated format
        methods = [method.strip().upper() for method in v.split(",") if method.strip()]
        return methods if methods else default_methods

    @field_validator("CORS_ALLOW_HEADERS", mode="before")
    def validate_cors_headers(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, list):
            return v
        if not v or v == "*" or not isinstance(v, str):
            return ["*"]

        # Try parsing as JSON first
        if v.startswith("["):
            json_result = parse_json_list(v)
            if json_result is not None:
                return [h.strip() for h in json_result if h.strip()]

        # Fall back to comma-separated format
        headers = [header.strip() for header in v.split(",") if header.strip()]
        return headers if headers else ["*"]

    # Logging Configuration
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Logging format string",
    )
    LOG_DATE_FORMAT: str = Field(
        default="%Y-%m-%d %H:%M:%S", description="Logging date format string"
    )

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Authentication configuration."""

import os

from pydantic import BaseModel, Field

from config.logging import jwt_log, redis_log


class JWTConfig(BaseModel):
    """Centralized JWT configuration"""

    secret_key: str = Field(...)
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    @classmethod
    def from_env(cls) -> "JWTConfig":
        secret_key = os.getenv("JWT_SECRET", "")
        if not secret_key:
            raise ValueError("JWT_SECRET environment variable must be set")

        return cls(
            secret_key=secret_key,
            algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(
                os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
            ),
        )


class RedisConfig(BaseModel):
    """Redis configuration"""

    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    db: int = Field(default=0)
    password: str | None = Field(default=None)

    @classmethod
    def from_env(cls) -> "RedisConfig":
        from config import get_settings

        settings = get_settings()

        config = cls(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
        )
        redis_log(
            f"Redis config initialized: host={config.host}, port={config.port}, db={config.db}"
        )
        return config


class AuthConfig(BaseModel):
    """Authentication configuration"""

    jwt_secret_key: str = Field(...)
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    max_login_attempts: int = Field(default=5)
    lockout_minutes: int = Field(default=15)


# Global instance - initialized at startup
jwt_config: JWTConfig | None = None
redis_config: RedisConfig | None = None


def get_jwt_config() -> JWTConfig:
    if jwt_config is None:
        raise RuntimeError(
            "JWT config not initialized. Call initialize_jwt_config() first."
        )
    return jwt_config


def get_redis_config() -> RedisConfig:
    if redis_config is None:
        raise RuntimeError(
            "Redis config not initialized. Call initialize_redis_config() first."
        )
    return redis_config


def initialize_jwt_config() -> None:
    global jwt_config
    jwt_config = JWTConfig.from_env()
    jwt_log(
        f"JWT config initialized: algorithm={jwt_config.algorithm}, expire_minutes={jwt_config.access_token_expire_minutes}"
    )


def initialize_redis_config() -> None:
    global redis_config
    redis_config = RedisConfig.from_env()

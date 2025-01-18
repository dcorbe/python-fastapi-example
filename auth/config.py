"""Authentication configuration."""

from typing import Union

from pydantic import BaseModel, Field

from config.logging import jwt_log, redis_log


class JWTConfig(BaseModel):
    """Centralized JWT configuration"""

    secret_key: str = Field(...)
    algorithm: str = Field(...)
    access_token_expire_minutes: int = Field(...)

    @classmethod
    def from_env(cls) -> "JWTConfig":
        from config import get_settings

        settings = get_settings()

        if not settings.AUTH_SECRET:
            raise ValueError("AUTH_SECRET environment variable must be set")

        return cls(
            secret_key=settings.AUTH_SECRET,
            algorithm=settings.AUTH_ALGORITHM,
            access_token_expire_minutes=settings.AUTH_TOKEN_EXPIRE_MINUTES,
        )


class RedisConfig(BaseModel):
    """Redis configuration"""

    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    db: int = Field(default=0)
    password: Union[str, None] = Field(default=None)

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


# Global instance - initialized at startup
jwt_config: Union[JWTConfig, None] = None
redis_config: Union[RedisConfig, None] = None


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

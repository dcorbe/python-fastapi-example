"""Authentication module."""

from fastapi import FastAPI

from .config import get_redis_config, initialize_jwt_config, initialize_redis_config
from .dependencies import (
    get_current_active_user,
    get_current_user,
    oauth2_scheme,
    set_auth_service,
    set_redis_service,
    verify_token,
)
from .models import AuthConfig
from .redis import RedisService
from .routes import AuthRouter
from .service import AuthService


async def setup_auth(app: FastAPI, auth_config: AuthConfig) -> AuthService:
    """Initialize authentication service."""
    redis_config = get_redis_config()
    redis_service = RedisService(redis_config)
    set_redis_service(redis_service)

    auth_service = AuthService(auth_config, redis_service)
    set_auth_service(auth_service)
    return auth_service


def create_auth_router(auth_service: AuthService) -> AuthRouter:
    """Create authentication router."""
    return AuthRouter(auth_service)


__all__ = [
    "AuthConfig",
    "AuthService",
    "AuthRouter",
    "RedisService",
    "get_current_active_user",
    "get_current_user",
    "get_redis_config",
    "initialize_jwt_config",
    "initialize_redis_config",
    "oauth2_scheme",
    "set_auth_service",
    "set_redis_service",
    "verify_token",
    "setup_auth",
    "create_auth_router",
]

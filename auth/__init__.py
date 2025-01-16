from fastapi import FastAPI

from .dependencies import get_current_user, set_auth_service
from .models import AuthConfig, Token, TokenData
from .routes import AuthRouter
from .service import AuthService


def setup_auth(app: FastAPI, config: AuthConfig) -> AuthService:
    """Initialize authentication system"""
    auth_service = AuthService(config)

    # Set the global auth service for dependencies
    set_auth_service(auth_service)

    # Set up the router
    auth_router = AuthRouter(auth_service)
    app.include_router(auth_router.router)

    return auth_service


__all__ = [
    "setup_auth",
    "AuthConfig",
    "Token",
    "TokenData",
    "AuthService",
    "get_current_user",
]

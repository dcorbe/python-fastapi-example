"""Authentication routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from database_manager import get_db
from user import User

from .dependencies import get_current_user
from .models import Token
from .service import AuthService


class AuthRouter:
    """Router for authentication endpoints."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.router = APIRouter(
            prefix="/auth",
            tags=["authentication"],
            responses={401: {"description": "Invalid credentials"}},
        )
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.router.post(
            "/login",
            response_model=Token,
            status_code=status.HTTP_200_OK,
            summary="Authenticate user",
            description="Authenticate using username/password to receive a JWT token",
            responses={
                200: {
                    "description": "Successfully authenticated",
                    "content": {
                        "application/json": {
                            "example": {
                                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                "token_type": "bearer",
                            }
                        }
                    },
                }
            },
            operation_id="loginUser",
        )
        async def login(
            form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
            db: AsyncSession = Depends(get_db),
        ) -> Token:
            """Login endpoint."""
            user = await self.auth_service.authenticate_user(
                form_data.username, form_data.password, db
            )

            access_token = self.auth_service.create_access_token({"sub": user.email})

            return Token(access_token=access_token, token_type="bearer")

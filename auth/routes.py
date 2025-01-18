"""Authentication routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from config.logging import logger
from database import get_session
from v1.users.models import User

from .dependencies import get_current_user, oauth2_scheme
from .models import Token
from .service import AuthService


class AuthRouter:
    """Router for authentication endpoints."""

    def __init__(self, auth_service: AuthService) -> None:
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
            db: AsyncSession = Depends(get_session),
        ) -> Token:
            """Login endpoint."""
            user = await self.auth_service.authenticate_user(
                form_data.username, form_data.password, db
            )

            access_token = self.auth_service.create_access_token({"sub": user.email})

            return Token(access_token=access_token, token_type="bearer")

        @self.router.post(
            "/logout",
            status_code=status.HTTP_200_OK,
            summary="Logout user",
            description="Invalidate the current access token",
            operation_id="logoutUser",
            responses={
                200: {"description": "Successfully logged out"},
                401: {"description": "Invalid or expired token"},
            },
        )
        async def logout_user(
            token: Annotated[str, Depends(oauth2_scheme)],  # Get raw token first
            current_user: Annotated[User, Depends(get_current_user)],  # Then get user
        ) -> dict[str, str]:
            """Logout endpoint."""
            try:
                logger.debug("=== Logout Process Start ===")
                logger.debug("1. Processing logout for user: %s", current_user.email)

                # Blacklist the raw token
                await self.auth_service.blacklist_token(token)
                logger.debug("2. Token blacklisted successfully")
                logger.debug("=== Logout Process Complete ===")

                return {"message": "Successfully logged out"}
            except HTTPException as e:
                # Re-raise HTTPException with original status code and details
                raise e
            except Exception as e:
                logger.error("Error during logout: %s", str(e))
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

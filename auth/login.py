"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session

from .dependencies import get_auth_service
from .models import Token
from .service import AuthService

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    session: AsyncSession = Depends(get_session),
) -> Token:
    """Login endpoint."""

    user = await auth_service.authenticate_user(
        form_data.username, form_data.password, session
    )
    access_token = auth_service.create_access_token({"sub": user.email})
    return Token(access_token=access_token, token_type="bearer")

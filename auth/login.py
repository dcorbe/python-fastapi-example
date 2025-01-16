from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.exc import UnknownHashError
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database_manager import get_db
from user import User
from user.operations import UserUpdate, update_user

from .password import verify_password
from .token import Token, create_access_token

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_db),
) -> Token:
    u = await User.get_by_email(session, form_data.username)
    settings = get_settings()

    if u is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if u.is_locked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is locked. Please try again later",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        if not verify_password(form_data.password, u.password_hash):
            # Increment failed login attempts
            failed_attempts = u.failed_login_attempts + 1
            update_data = UserUpdate(failed_login_attempts=failed_attempts)

            # If too many failed attempts, lock the account
            if failed_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                locked_until = datetime.now(UTC) + timedelta(
                    minutes=settings.LOCKOUT_MINUTES
                )
                update_data.locked_until = locked_until

            await update_user(session, u, update_data)

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except UnknownHashError:
        # This indicates the password hash is in an invalid format
        raise HTTPException(
            status_code=status.HTTP_426_UPGRADE_REQUIRED,
            detail="Account requires password reset",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reset failed attempts on successful login
    await update_user(
        session, u, UserUpdate(failed_login_attempts=0, last_login=datetime.now(UTC))
    )

    access_token = create_access_token({"sub": u.email})
    return Token(access_token=access_token, token_type="bearer")

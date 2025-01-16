from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.exc import UnknownHashError
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from user import User
from user.operations import update_user
from user.schemas import UserUpdate
from database_manager import get_db
from .token import Token, create_access_token

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: AsyncSession = Depends(get_db)
) -> Token:
    u = await User.get_by_email(db, form_data.username)
    
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
            if u.failed_login_attempts >= 5:  # Consider making this configurable
                u.locked_until = datetime.now() + timedelta(minutes=15)
            
            await update_user(db, u, UserUpdate(
                failed_login_attempts=u.failed_login_attempts,
                locked_until=u.locked_until
            ))
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except UnknownHashError:
        raise HTTPException(
            status_code=status.HTTP_426_UPGRADE_REQUIRED,
            detail="Account requires password reset",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reset failed attempts on successful login
    u.failed_login_attempts = 0
    u.last_login = datetime.now()
    await update_user(db, u, UserUpdate(
        failed_login_attempts=u.failed_login_attempts,
        last_login=u.last_login
    ))

    access_token = create_access_token({"sub": u.email})
    return Token(access_token=access_token, token_type="bearer")

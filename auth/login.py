from typing import Annotated
from datetime import datetime, timedelta
from passlib.exc import UnknownHashError
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm

from database import Database
from user import User
from database_manager import get_db

from .token import Token, create_access_token
from .password import verify_password


router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Database = Depends(get_db)
) -> Token:
    u = await User.get_by_email(form_data.username, db)
    
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
            u.failed_login_attempts += 1
            
            # If too many failed attempts, lock the account
            if u.failed_login_attempts >= 5:  # Consider making this configurable
                u.locked_until = datetime.now() + timedelta(minutes=15)
            
            await u.save(db)
            
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
    u.failed_login_attempts = 0
    u.last_login = datetime.now()
    await u.save(db)

    access_token = create_access_token({"sub": u.email})
    return Token(access_token=access_token, token_type="bearer")

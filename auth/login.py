from typing import Annotated
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm

from database import Database
from user import User
from database_manager import get_db

from .token import Token, create_access_token


router = APIRouter()  # Get this from parent module

@router.post("/login", response_model=Token)
async def login(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Database = Depends(get_db)
) -> Token:
    u = await User.get_by_email(form_data.username, db)

    # TODO: We need to implement password hashing
    if form_data.password != u.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": u.email})
    return Token(access_token=access_token, token_type="bearer")

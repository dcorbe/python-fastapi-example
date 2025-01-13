from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Annotated

import jwt

from database import Database
from user import User
from database_manager import get_db
from .config import get_jwt_config

# Security scheme for token handling
security = HTTPBearer()

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

def create_access_token(data: dict) -> str:
    config = get_jwt_config()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.secret_key, algorithm=config.algorithm)

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(security)],
    db: Database = Depends(get_db)
) -> User:
    config = get_jwt_config()
    try:
        payload = jwt.decode(
            credentials.credentials, 
            config.secret_key, 
            algorithms=[config.algorithm]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(username=username)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await User.get_by_email(token_data.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

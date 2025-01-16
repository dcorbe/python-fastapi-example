"""JWT token handling utilities."""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db

from .config import get_jwt_config

# Security scheme for token handling
security = HTTPBearer()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


def create_access_token(data: dict) -> str:
    """Create a new JWT access token."""
    config = get_jwt_config()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=config.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.secret_key, algorithm=config.algorithm)


async def get_user_by_email(db: AsyncSession, email: str) -> Any:
    """Get a user by their email address."""
    # Import here to avoid circular import
    from v1.users.models import User

    stmt = select(User).where(func.lower(User.email) == email.lower())
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(security)],
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Validate JWT token and return current user."""
    config = get_jwt_config()
    try:
        payload = jwt.decode(
            credentials.credentials, config.secret_key, algorithms=[config.algorithm]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await get_user_by_email(db, username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

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

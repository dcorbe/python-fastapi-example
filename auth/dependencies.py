"""Authentication dependencies."""

from typing import Annotated, Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session

from .models import TokenData
from .redis import RedisService
from .service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=True)

# Will be set by setup_auth
_auth_service: Optional[AuthService] = None
_redis_service: Optional[RedisService] = None


def get_redis_service() -> RedisService:
    """Get the initialized Redis service."""
    if _redis_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Redis service not initialized",
        )
    return _redis_service


def set_redis_service(service: RedisService) -> None:
    """Set the Redis service (called by setup_auth)."""
    global _redis_service
    _redis_service = service


def get_auth_service() -> AuthService:
    """Get the initialized auth service."""
    if _auth_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not initialized",
        )
    return _auth_service


def set_auth_service(service: AuthService) -> None:
    """Set the auth service (called by setup_auth)."""
    global _auth_service
    _auth_service = service


async def verify_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenData:
    """Verify token is valid and not blacklisted."""
    try:
        print("\n=== Token Verification Start ===")
        print(f"1. Received token: {token}")

        # Validate and decode token (includes blacklist check)
        token_data = await auth_service.decode_token(token)
        print("2. Token validated successfully")
        print("=== Token Verification Complete ===\n")
        return token_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error verifying token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token_data: Annotated[TokenData, Depends(verify_token)],
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Get current user after token verification."""
    try:
        # Import here to avoid circular import
        from v1.users.models import User

        # Token is already verified and decoded
        if not token_data.sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        stmt = select(User).where(User.email.ilike(token_data.sub))
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: Annotated[Any, Depends(get_current_user)]
) -> Any:
    """Get current active user."""
    return current_user

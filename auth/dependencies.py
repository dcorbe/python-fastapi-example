"""Authentication dependencies."""
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database_manager import get_db
from database.models import User
from .service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Will be set by setup_auth
_auth_service: Optional[AuthService] = None

def get_auth_service() -> AuthService:
    """Get the initialized auth service."""
    if _auth_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not initialized"
        )
    return _auth_service

def set_auth_service(service: AuthService) -> None:
    """Set the auth service (called by setup_auth)."""
    global _auth_service
    _auth_service = service

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    session: AsyncSession = Depends(get_db)
) -> User:
    """Global dependency for getting the current user."""
    token_data = auth_service.decode_token(token)
    
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

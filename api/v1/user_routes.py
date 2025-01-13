from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID

from database import Database
from database_manager import get_db
from auth import get_current_user
from user import User

router = APIRouter()

class UserResponse(BaseModel):
    """Pydantic model for user response"""
    id: UUID
    email: EmailStr
    email_verified: bool
    created_at: datetime
    last_login: datetime | None
    
    class Config:
        from_attributes = True

@router.get("/user", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Database = Depends(get_db)
) -> UserResponse:
    """
    Get currently authenticated user information.
    
    Returns:
        UserResponse: The current user's public information
    """
    return UserResponse.model_validate(current_user)
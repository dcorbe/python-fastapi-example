"""User management API endpoints."""
from typing import Annotated
from fastapi import APIRouter, Depends

from auth.token import get_current_user
from user.schemas import UserResponse
from user import User

router = APIRouter(prefix="/user", tags=["users"])


@router.get("", response_model=UserResponse)
async def user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Echo back the currently authenticated user."""
    return current_user

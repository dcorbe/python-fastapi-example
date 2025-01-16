"""User details endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from auth.token import get_current_user

from .models import User
from .schemas import User as UserSchema

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserSchema,
    summary="Get current user details",
    description="Get details of the currently logged in user",
    operation_id="getCurrentUser",
)
async def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserSchema:
    """Get current user details."""
    return UserSchema.model_validate(current_user)

"""User management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from auth import get_current_active_user

from .models import User
from .schemas import User as UserSchema

router = APIRouter(prefix="/users")


@router.get(
    "/me",
    response_model=UserSchema,
    summary="Get current user",
    description="Get the currently authenticated user's details",
    operation_id="getCurrentUser",
    responses={
        200: {"description": "Successfully retrieved user details"},
        401: {"description": "Not authenticated"},
    },
)
async def get_current_user_route(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserSchema:
    """Get current user."""
    return UserSchema.model_validate(current_user)

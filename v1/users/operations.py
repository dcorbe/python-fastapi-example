"""User operations."""

from .models import User
from .schemas import User as UserSchema


async def get_current_user_details(user: User) -> UserSchema:
    """Convert user model to response schema."""
    return UserSchema.model_validate(user)

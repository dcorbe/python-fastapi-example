"""User management module."""

from .model import User
from .operations import (
    create_user,
    delete_user,
    get_all_users,
    get_user_by_email,
    get_user_by_id,
    update_user,
)
from .schemas import UserBase, UserCreate, UserResponse, UserUpdate

__all__ = [
    # Models
    "User",
    # Schemas
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    # Operations
    "get_user_by_email",
    "get_user_by_id",
    "get_all_users",
    "create_user",
    "update_user",
    "delete_user",
]

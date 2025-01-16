"""Pydantic schemas for user data validation."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserBase(BaseModel):
    """Base schema for User data."""

    email: EmailStr = Field(..., description="User's email address")
    email_verified: bool = Field(
        default=False, description="Whether the email has been verified"
    )


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password_hash: str = Field(..., description="Hashed password")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "email_verified": False,
                "password_hash": "hashed_password_here",
            }
        }
    )


class UserResponse(UserBase):
    """Schema for user data in API responses."""

    id: UUID = Field(..., description="User's unique identifier")
    created_at: datetime = Field(..., description="When the user was created")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    failed_login_attempts: int = Field(
        ..., description="Number of failed login attempts"
    )
    is_locked: bool = Field(..., description="Whether the account is currently locked")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "email_verified": True,
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-02T00:00:00Z",
                "failed_login_attempts": 0,
                "is_locked": False,
            }
        },
    )


class UserUpdate(BaseModel):
    """Schema for updating user data."""

    email: Optional[EmailStr] = Field(None, description="New email address")
    password_hash: Optional[str] = Field(None, description="New hashed password")
    email_verified: Optional[bool] = Field(
        None, description="Update email verification status"
    )
    failed_login_attempts: Optional[int] = Field(
        None, description="Update failed login attempts"
    )
    locked_until: Optional[datetime] = Field(
        None, description="Update account lock expiry"
    )
    last_login: Optional[datetime] = Field(
        None, description="Last successful login time"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {"email": "newuser@example.com", "email_verified": True}
        },
    )

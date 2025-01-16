"""User data schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class User(BaseModel):
    """Schema for user data in API responses."""

    id: UUID = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    email_verified: bool = Field(..., description="Whether the email has been verified")
    created_at: datetime = Field(..., description="When the user was created")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    failed_login_attempts: int = Field(
        ..., description="Number of failed login attempts"
    )
    locked_until: Optional[datetime] = Field(
        None, description="Account lock expiry time"
    )

    model_config = ConfigDict(from_attributes=True)

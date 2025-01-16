"""Example of an authenticated endpoint that returns a personalized greeting.

This module demonstrates a simple authenticated endpoint that returns a greeting
message along with the authenticated user's ID.
"""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, ConfigDict

from auth.token import get_current_user
from user import User


class Hello(BaseModel):
    """Response model for the hello endpoint."""
    message: str = Field(
        description="A greeting message for the authenticated user",
        examples=["This is a protected endpoint"]
    )
    user_id: UUID = Field(
        description="The UUID of the authenticated user",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    
    model_config = ConfigDict(from_attributes=True)


router = APIRouter(
    tags=["example"],
    responses={
        403: {"detail": "Not Authenticated"},
    }
)


@router.get(
    "/hello",
    response_model=Hello,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated greeting",
    description="Returns a greeting message and the authenticated user's ID. Requires authentication.",
    operation_id="helloRequest"
)
async def hello_world(
    current_user: Annotated[User, Depends(get_current_user)]
) -> Hello:
    """Return a greeting message for the authenticated user.
    
    Args:
        current_user: The authenticated user making the request
        
    Returns:
        Hello: A response containing a greeting message and the user's ID
    """
    return Hello(
        message="This is a protected endpoint",
        user_id=current_user.id
    )

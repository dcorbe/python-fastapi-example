"""User management API endpoints.

This module provides endpoints for managing user-related operations, including:
- Retrieving the current authenticated user's details
"""
from typing import Annotated
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict

from auth.token import get_current_user
from user.schemas import UserResponse
from user import User


router = APIRouter(
    prefix="/user",
    tags=["users"],
    responses={
        401: {"description": "Unauthorized - Authentication required"},
        403: {"description": "Forbidden - Insufficient permissions"},
        500: {"description": "Internal Server Error"}
    }
)


@router.get(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Retrieve details of the currently authenticated user.",
    responses={
        200: {
            "description": "Successfully retrieved user details",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "user@example.com",
                        "active": True,
                        "created_at": "2024-01-16T10:00:00Z"
                    }
                }
            }
        }
    },
    operation_id="getCurrentUser"
)
async def get_current_user_details(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Return the details of the currently authenticated user.
    
    Args:
        current_user: The authenticated user making the request (injected by FastAPI)
        
    Returns:
        User: The current user's details
        
    Raises:
        HTTPException: If the user is not authenticated
    """
    return current_user

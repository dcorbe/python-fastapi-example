"""Example of an authenticated endpoint."""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth.token import get_current_user
from user import User


class Hello(BaseModel):
    message: str
    user_id: UUID


router = APIRouter(tags=["example"])


@router.get("/hello", response_model=Hello)
async def hello_world(
    current_user: Annotated[User, Depends(get_current_user)]
) -> Hello:
    """
    Example of a protected endpoint that requires authentication.
    
    Returns:
        Hello: A message and the authenticated user's ID
    """
    return Hello(
        message="This is a protected endpoint",
        user_id=current_user.id
    )

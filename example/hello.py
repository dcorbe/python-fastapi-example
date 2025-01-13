"""
This module defines an endpoint for returning a hello world message to the currently logged-in user.
"""
# Global imports
from pydantic import BaseModel
from fastapi import Depends
from uuid import UUID

# Library imports
from auth.token import get_current_user
from user import User

# Local imports
from . import router


class Hello(BaseModel):
    message: str
    user_id: UUID


@router.get("/hello", response_model=Hello)
async def hello_world(current_user: User = Depends(get_current_user)) -> Hello:
    """
    An example of a protected endpoint that requires authentication.

    Args:
        current_user: The authenticated user (injected by FastAPI)

    Returns:
        Hello: A simple response containing a message and the user's ID

    Raises:
        HTTPException: If the user is not authenticated, no boilerplate required
    """
    return Hello(
        message="This is a protected endpoint",
        user_id=current_user.id
    )

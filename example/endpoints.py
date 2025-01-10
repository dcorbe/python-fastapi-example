from fastapi import Depends, HTTPException
from auth.token import get_current_user
from user import User
from . import router
from pydantic import BaseModel
from uuid import UUID


class ExampleResponse(BaseModel):
    message: str
    user_id: UUID


@router.get("/protected", response_model=ExampleResponse)
async def protected_endpoint(current_user: User = Depends(get_current_user)) -> ExampleResponse:
    """
    Example protected endpoint that requires authentication.
    
    Args:
        current_user: The authenticated user (injected by FastAPI)
        
    Returns:
        ExampleResponse: A simple response containing a message and the user's ID
        
    Raises:
        HTTPException: If the user is not authenticated
    """
    return ExampleResponse(
        message="This is a protected endpoint",
        user_id=current_user.id
    )
"""Example error handling endpoint demonstrating HTTP error responses."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Annotated


class ExampleResponse(BaseModel):
    """Response model for the error endpoint."""
    message: Annotated[str, Field(
        default="",
        description="Response message string",
        json_schema_extra={
            "example": "Success message that will never be returned"
        }
    )]


router = APIRouter(
    prefix="/error",
    tags=["example"],
    responses={
        403: {"detail": "Not authenticated"}
    }
)


@router.get(
    "",
    response_model=ExampleResponse,
    summary="Example error endpoint",
    description="This endpoint demonstrates error handling by always returning a 403 Forbidden error.",
)
async def error_message() -> ExampleResponse:
    """Demonstrate error handling by raising a 403 Forbidden error.
    
    This endpoint is designed to show how FastAPI handles error responses.
    It will always raise a 403 Forbidden error with a specific error message.
    
    Returns:
        ExampleResponse: Never actually returns - always raises an HTTPException
        
    Raises:
        HTTPException: 403 Forbidden error with a descriptive message
    """
    raise HTTPException(
        status_code=403,
        detail="You are not authorized to access this resource"
    )

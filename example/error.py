"""
This module defines an endpoint for returning an error message to the user.

The endpoint is defined using FastAPI and returns a JSON response with an error message
when accessed. The response model is defined using Pydantic.

Classes:
    ExampleResponse: Pydantic model for the error response.

Functions:
    error_message: Endpoint that raises an HTTPException with a 403 status code.
"""
from fastapi import HTTPException

from . import router
from pydantic import BaseModel


class ExampleResponse(BaseModel):
    message: str


@router.get("/error", response_model=ExampleResponse)
async def error_message() -> ExampleResponse:
    """
    This is how you return an error message to the user
    """
    raise HTTPException(status_code=403, detail="You are not authorized to access this resource")

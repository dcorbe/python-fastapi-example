"""Example error handling endpoint."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


class ExampleResponse(BaseModel):
    message: str


router = APIRouter(tags=["example"])


@router.get("/error", response_model=ExampleResponse)
async def error_message() -> ExampleResponse:
    """Example of how to return an error message to the user."""
    raise HTTPException(
        status_code=403,
        detail="You are not authorized to access this resource"
    )

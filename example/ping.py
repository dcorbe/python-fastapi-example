"""Ping endpoint for health checking and API verification."""
from fastapi import APIRouter, status
from pydantic import BaseModel, Field


class Ping(BaseModel):
    """Response model for ping endpoint."""
    ping: str = Field(
        default="pong",
        description="Response message indicating API health",
        examples=["pong"]
    )


router = APIRouter(tags=["example"])


@router.get(
    "/ping",
    response_model=Ping,
    status_code=status.HTTP_200_OK,
    summary="API Health Check",
    description="Simple ping endpoint that returns 'pong' to verify API availability",
)
async def ping_endpoint() -> Ping:
    """
    Perform a health check on the API.
    
    Returns:
        Ping: A response object containing 'pong' to indicate the API is healthy
    """
    return Ping(ping="pong")

"""Ping endpoint for health checking and API verification.

This module provides a simple health check endpoint that returns a "pong"
response, useful for monitoring and verifying API availability.
"""
from fastapi import APIRouter, status
from pydantic import BaseModel, Field, ConfigDict


class Ping(BaseModel):
    """Response model for ping endpoint."""
    ping: str = Field(
        default="pong",
        description="Response message indicating API health",
        examples=["pong"]
    )

    model_config = ConfigDict(from_attributes=True)


router = APIRouter(
    tags=["example"],
    responses={
        500: {"description": "Internal Server Error"}
    }
)


@router.get(
    "/ping",
    response_model=Ping,
    status_code=status.HTTP_200_OK,
    summary="API Health Check",
    description="Simple ping endpoint that returns 'pong' to verify API availability",
    responses={
        200: {
            "description": "API is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "ping": "pong"
                    }
                }
            }
        }
    },
    operation_id="pingHealth"
)
async def ping_endpoint() -> Ping:
    """Perform a health check on the API.
    
    Returns:
        Ping: A response object containing 'pong' to indicate the API is healthy
    """
    return Ping(ping="pong")

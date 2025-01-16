"""Ping endpoint for health checking and API verification.

This module provides a simple health check endpoint that returns a "pong"
response, useful for monitoring and verifying API availability.
The endpoint requires no authentication and is used to verify basic API connectivity.
"""
from fastapi import APIRouter, status
from pydantic import BaseModel, Field, ConfigDict


class Ping(BaseModel):
    """Response model for ping endpoint."""
    ping: str = Field(
        default="pong",
        description="Response message indicating API health. Always returns 'pong' when the API is healthy.",
        examples=["pong"]
    )
    status: str = Field(
        default="healthy",
        description="Status of the API health check",
        examples=["healthy"]
    )

    model_config = ConfigDict(from_attributes=True)


router = APIRouter(tags=["example"])


@router.get(
    "/ping",
    response_model=Ping,
    status_code=status.HTTP_200_OK,
    summary="API Health Check",
    description="""
    Simple ping endpoint that verifies API availability and basic functionality.
    This endpoint:
    - Requires no authentication
    - Returns a 200 status with 'pong' response when healthy
    - Can be used for load balancer health checks
    - Helps verify API deployment status
    """,
    responses={
        200: {
            "description": "API is healthy and responding normally",
            "content": {
                "application/json": {
                    "example": {
                        "ping": "pong",
                        "status": "healthy"
                    }
                }
            }
        }
    },
    operation_id="pingRequest"
)
async def ping_endpoint() -> Ping:
    """Perform a health check on the API.
    
    Returns:
        Ping: A response object containing 'pong' and status information
        indicating the API is healthy
        
    Note:
        This endpoint is designed to be lightweight and fast-responding.
        It does not check database connectivity or other external services.
    """
    return Ping(ping="pong", status="healthy")

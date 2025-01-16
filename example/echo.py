"""Echo endpoint for reflecting request details back to the client.

This module implements an endpoint that echoes back the complete request information,
including headers, method, URL, and body. It's useful for debugging and testing
how requests are received by the API.

All operations require authentication using JWT tokens.
"""

from typing import Annotated, Dict, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from auth.token import get_current_user
from user import User


class EchoResponse(BaseModel):
    """Schema for the echo response containing request details."""

    headers: Dict[str, str] = Field(
        description="HTTP headers from the original request",
        examples=[
            {
                "content-type": "application/json",
                "authorization": "Bearer eyJhbGc...",
                "accept": "application/json",
            }
        ],
    )
    method: str = Field(
        description="HTTP method used in the request", examples=["POST"]
    )
    url: str = Field(
        description="Complete URL of the request",
        examples=["http://localhost:8000/echo"],
    )
    body: Optional[str] = Field(
        default=None,
        description="Request body content, if any",
        examples=['{"message": "Hello, World!"}'],
    )

    model_config = ConfigDict(from_attributes=True)


router = APIRouter(tags=["example"], responses={403: {"detail": "Not authenticated"}})


@router.post(
    "/echo",
    response_model=EchoResponse,
    summary="Echo Request Details",
    description="Echo back the complete details of the HTTP request, including headers, method, URL, and body. Requires authentication.",
    responses={
        200: {
            "description": "Request details successfully echoed",
            "content": {
                "application/json": {
                    "example": {
                        "headers": {
                            "content-type": "application/json",
                            "authorization": "Bearer eyJhbGc...",
                            "accept": "application/json",
                        },
                        "method": "POST",
                        "url": "http://localhost:8000/echo",
                        "body": '{"message": "Hello, World!"}',
                    }
                }
            },
        }
    },
    operation_id="echoRequest",
)
async def echo(
    request: Request, user: Annotated[User, Depends(get_current_user)]
) -> JSONResponse:
    """Echo back the request information.

    Args:
        request: The incoming FastAPI request object containing all request details
        user: The authenticated user making the request

    Returns:
        JSONResponse containing the echoed request data including headers, method,
        URL, and body content
    """
    body = await request.body()

    return JSONResponse(
        content={
            "headers": dict(request.headers),
            "method": request.method,
            "url": str(request.url),
            "body": body.decode() if body else None,
        }
    )

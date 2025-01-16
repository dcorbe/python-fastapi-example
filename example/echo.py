"""
This module defines an endpoint for echoing back the request body and headers.

The endpoint is defined using FastAPI and returns a JSON response with the echoed request data
when accessed. The response includes the request headers, method, URL, and body.
"""
from typing import Annotated
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from auth.token import get_current_user
from user import User

router = APIRouter(
    tags=["example"],
    responses={401: {"description": "Unauthorized - Authentication required"}}
)

@router.post(
    "/echo",
    summary="Echo Request Details",
    description="Echo back the details of the HTTP request, including headers, method, URL, and body.",
    responses={
        200: {
            "description": "Request details successfully echoed",
            "content": {
                "application/json": {
                    "example": {
                        "headers": {
                            "content-type": "application/json",
                            "authorization": "Bearer ..."
                        },
                        "method": "POST",
                        "url": "http://localhost:8000/example/echo",
                        "body": '{"foo": "bar"}'
                    }
                }
            }
        }
    }
)
async def echo(request: Request, user: Annotated[User, Depends(get_current_user)]) -> JSONResponse:
    """
    Echo back the request body and headers.
    
    Args:
        request: The incoming request object
        user: The authenticated user (injected by FastAPI)
        
    Returns:
        JSONResponse containing the echoed request data

    Raises:
        HTTPException: If the user is not authenticated (automatically handled by the auth module)
    """
    body = await request.body()
    
    return JSONResponse(content={
        "headers": dict(request.headers),
        "method": request.method,
        "url": str(request.url),
        "body": body.decode() if body else None
    })

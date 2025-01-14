"""
This module defines an endpoint for echoing back the request body and headers.

The endpoint is defined using FastAPI and returns a JSON response with the echoed request data
when accessed. The response includes the request headers, method, URL, and body.

Functions:
    echo: Endpoint that echoes back the request data.
"""
from fastapi import Request, Depends
from fastapi.responses import JSONResponse

from auth.token import get_current_user
from user import User

from . import router


@router.post("/echo")
async def echo(request: Request, user: User = Depends(get_current_user)) -> JSONResponse:
    """
    Echo back the request body and headers.
    
    Args:
        request: The incoming request object
        user: The authenticated user (injected by FastAPI)
        
    Returns:
        JSONResponse containing the echoed request data

    Raises:
        HTTPException: If the user is not authenticated (automaitcally handled by the auth module)
    """
    body = await request.body()
    
    response_data = {
        "headers": dict(request.headers),
        "method": request.method,
        "url": str(request.url),
        "body": body.decode() if body else None
    }
    
    return JSONResponse(content=response_data)

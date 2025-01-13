"""
This module defines an endpoint for returning a ping response.

The endpoint is defined using FastAPI and returns a JSON response with a ping message
when accessed. The response model is defined using Pydantic.

Classes:
    Ping: Pydantic model for the ping response.

Functions:
    protected_endpoint: Endpoint that returns a ping message.
"""
from pydantic import BaseModel

from . import router


class Ping(BaseModel):
    ping: str


@router.get("/ping", response_model=Ping)
async def protected_endpoint() -> Ping:
    """
    This is an example of a bare, unprotected endpoint.

    Returns:
        Ping: A simple response containing a message and the user's ID

    Raises:
        HTTPException: If the user is not authenticated
    """
    return Ping(ping="pong")

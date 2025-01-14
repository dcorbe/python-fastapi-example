"""Ping endpoint."""
from fastapi import APIRouter
from pydantic import BaseModel


class Ping(BaseModel):
    ping: str


router = APIRouter(tags=["example"])


@router.get("/ping", response_model=Ping)
async def ping_endpoint() -> Ping:
    """Simple ping endpoint that returns 'pong'."""
    return Ping(ping="pong")

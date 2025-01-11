"""Example API endpoints module."""
from fastapi import APIRouter

router = APIRouter(prefix="/example", tags=["example"])

from . import endpoints

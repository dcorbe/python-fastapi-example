"""
This module initializes the FastAPI router for the example endpoints.
"""
from fastapi import APIRouter, Depends
from auth.token import get_current_user

router = APIRouter(prefix="/example", tags=["example"])

from . import hello
from . import ping

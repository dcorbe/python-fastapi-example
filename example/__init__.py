from fastapi import APIRouter, Depends
from auth.token import get_current_user

router = APIRouter(prefix="/example", tags=["example"])

from . import endpoints  # noqa

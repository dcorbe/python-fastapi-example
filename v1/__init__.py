"""API v1 routes."""

from fastapi import APIRouter

from .users import router as users_router

router = APIRouter(prefix="/v1")
router.include_router(users_router)

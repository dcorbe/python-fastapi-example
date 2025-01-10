from fastapi import APIRouter
from .user_routes import router as user_router

router = APIRouter(prefix="/v1")
router.include_router(user_router)

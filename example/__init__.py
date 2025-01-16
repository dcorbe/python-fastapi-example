"""Example endpoints."""

from fastapi import APIRouter

from .books import router as book_router
from .echo import router as echo_router
from .error import router as error_router
from .hello import router as hello_router
from .ping import router as ping_router

router = APIRouter(prefix="/example")
router.include_router(book_router)
router.include_router(echo_router)
router.include_router(error_router)
router.include_router(hello_router)
router.include_router(ping_router)

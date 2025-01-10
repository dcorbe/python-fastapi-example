from typing import Annotated
from fastapi import Depends, APIRouter

from user import User

from .token import Token, create_access_token, get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)
from .login import router as login_router
router.include_router(login_router)

@router.get("/protected")
async def protected_route(
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict[str, str]:
    return {"message": f"Hello {current_user.email}"}

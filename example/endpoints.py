from typing import Annotated
from fastapi import Depends
from auth.dependencies import get_current_user
from user import User

async def protected_endpoint(
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict[str, str]:
    return {"message": f"Hello, {current_user.email}!"}
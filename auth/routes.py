from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from database import Database
from database_manager import get_db
from user import User

from .models import Token
from .service import AuthService
from .dependencies import get_current_user

class AuthRouter:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.router = APIRouter(prefix="/auth", tags=["authentication"])
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.router.post("/login", response_model=Token)
        async def login(
            form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
            db: Database = Depends(get_db)
        ) -> Token:
            user = await self.auth_service.authenticate_user(
                form_data.username,
                form_data.password,
                db
            )
            
            access_token = self.auth_service.create_access_token(
                {"sub": user.email}
            )
            
            return Token(access_token=access_token, token_type="bearer")

        @self.router.get("/protected")
        async def protected_route(
            current_user: Annotated[User, Depends(get_current_user)]
        ) -> dict[str, str]:
            return {"message": f"Hello {current_user.email}"}
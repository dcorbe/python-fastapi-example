from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from fastapi import HTTPException, status
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from database import Database
from user import User
from .models import AuthConfig, TokenData, LoginAttempt

class AuthService:
    def __init__(self, config: AuthConfig):
        self.config = config
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self._login_attempts: Dict[str, LoginAttempt] = {}

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return self._pwd_context.verify(plain_password, hashed_password)
        except UnknownHashError:
            raise HTTPException(
                status_code=status.HTTP_426_UPGRADE_REQUIRED,
                detail="Account requires password reset",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def create_access_token(self, data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        
        return jwt.encode(
            to_encode,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm
        )

    def decode_token(self, token: str) -> TokenData:
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm]
            )
            return TokenData(**payload)
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def authenticate_user(
        self,
        email: str,
        password: str,
        db: Database
    ) -> User:
        # Check for account lockout
        if self._is_account_locked(email):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is locked. Please try again later",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user
        user = await User.get_by_email(email, db)
        if not user:
            self._record_failed_attempt(email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not self.verify_password(password, user.password_hash):
            self._record_failed_attempt(email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Clear failed attempts on success
        self._clear_failed_attempts(email)
        
        # Update last login
        user.last_login = datetime.utcnow()
        await user.save(db)
        
        return user

    def _is_account_locked(self, email: str) -> bool:
        attempt = self._login_attempts.get(email)
        if not attempt:
            return False
        
        if attempt.locked_until and datetime.utcnow() < attempt.locked_until:
            return True
        
        return False

    def _record_failed_attempt(self, email: str) -> None:
        attempt = self._login_attempts.get(email, LoginAttempt(email=email))
        attempt.attempts += 1
        attempt.last_attempt = datetime.utcnow()
        
        if attempt.attempts >= self.config.max_login_attempts:
            attempt.locked_until = datetime.utcnow() + timedelta(
                minutes=self.config.lockout_minutes
            )
        
        self._login_attempts[email] = attempt

    def _clear_failed_attempts(self, email: str) -> None:
        if email in self._login_attempts:
            del self._login_attempts[email]

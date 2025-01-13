from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class AuthConfig(BaseModel):
    """Configuration for authentication system"""
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    max_login_attempts: int = 5
    lockout_minutes: int = 15

class Token(BaseModel):
    """OAuth2 token response"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """JWT token payload"""
    sub: Optional[str] = None
    exp: Optional[datetime] = None

class LoginAttempt(BaseModel):
    """Track login attempts and lockouts"""
    email: str
    attempts: int = 0
    locked_until: Optional[datetime] = None
    last_attempt: datetime = Field(default_factory=datetime.utcnow)

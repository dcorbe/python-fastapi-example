"""User model definition."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base

class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False,
        index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, 
        default=0, 
        nullable=False
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User {self.email}>"

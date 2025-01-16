"""User database model definition."""

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Index, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database.models.base import Base


class User(Base):
    """User database model."""

    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email_lower", func.lower("email"), unique=True),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    @classmethod
    async def get_by_email(cls, db: AsyncSession, email: str) -> Optional["User"]:
        """Get a user by their email address."""
        query = select(cls).where(func.lower(cls.email) == email.lower())
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @property
    def is_locked(self) -> bool:
        """Check if the user account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.now(UTC) < self.locked_until

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User {self.email}>"

"""User management module."""
from datetime import datetime, UTC
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User as UserModel
from database.models.mixins import PydanticBase


class User(PydanticBase):
    """User model with validation."""

    id: Optional[UUID] = None
    email: EmailStr
    password_hash: str
    email_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_login: Optional[datetime] = None
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = None

    @property
    def is_locked(self) -> bool:
        """Check if the user account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.now(UTC) < self.locked_until

    def to_orm(self) -> UserModel:
        """Convert to SQLAlchemy model."""
        return UserModel(**self.model_dump(exclude={'id'} if self.id is None else {}))

    @classmethod
    async def get_by_email(
        cls, 
        session: AsyncSession, 
        email: str,
        case_insensitive: bool = True
    ) -> Optional['User']:
        """Get user by email."""
        stmt = select(UserModel)
        if case_insensitive:
            stmt = stmt.where(UserModel.email.ilike(email))
        else:
            stmt = stmt.where(UserModel.email == email)
        
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return cls.model_validate(user) if user else None

    @classmethod
    async def get_by_id(
        cls, 
        session: AsyncSession, 
        user_id: UUID
    ) -> Optional['User']:
        """Get user by ID."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return cls.model_validate(user) if user else None

    async def save(self, session: AsyncSession) -> None:
        """Save or update user."""
        orm_user = self.to_orm()
        if self.id is not None:
            orm_user.id = self.id
            merged = await session.merge(orm_user)
            self.model_validate(merged)
        else:
            session.add(orm_user)
            await session.flush()
            self.model_validate(orm_user)

    async def delete(self, session: AsyncSession) -> None:
        """Delete user."""
        if self.id is None:
            raise ValueError("Cannot delete user without ID")
        
        stmt = select(UserModel).where(UserModel.id == self.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            await session.delete(user)

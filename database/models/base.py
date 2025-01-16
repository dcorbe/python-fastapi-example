"""Base model configuration for SQLAlchemy."""

from datetime import datetime
from typing import Any, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

T = TypeVar("T", bound="Base")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    @classmethod
    async def get_by_id(cls: Type[T], session: AsyncSession, id: UUID) -> Optional[T]:
        """Fetch a record by its ID."""
        stmt = select(cls).where(cls.id == id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_field(
        cls: Type[T],
        session: AsyncSession,
        field: str,
        value: Any,
        case_insensitive: bool = False,
    ) -> Optional[T]:
        """Fetch a record by a specific field value."""
        column = getattr(cls, field)
        if case_insensitive and isinstance(value, str):
            stmt = select(cls).where(column.ilike(value))
        else:
            stmt = select(cls).where(column == value)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    id: Mapped[UUID] = mapped_column(
        primary_key=True, server_default="gen_random_uuid()"
    )
    created_at: Mapped[datetime] = mapped_column(server_default="CURRENT_TIMESTAMP")

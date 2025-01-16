"""Database session management."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from database import Database


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async with Database.session() as session:
        yield session

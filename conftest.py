"""Test configuration and fixtures."""

import os
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Set test environment variables
os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:password@localhost:5432/test_db"
os.environ["TESTING"] = "1"


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    from database import Database

    async with Database.session() as session:
        yield session
        # Rollback any changes
        await session.rollback()

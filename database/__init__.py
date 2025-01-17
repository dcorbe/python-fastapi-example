"""Database connection and session management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import get_database_url


class Database:
    """Database connection manager."""

    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    @classmethod
    def init(cls) -> None:
        """Initialize database connection."""
        sql_url = get_database_url()
        print(f"Using SQLAlchemy URL: {sql_url}")  # Will be masked by logs

        cls._engine = create_async_engine(
            sql_url,
            echo=False,  # Enable SQL logging
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )

        cls._session_factory = async_sessionmaker(
            cls._engine, class_=AsyncSession, expire_on_commit=False
        )

    @classmethod
    @asynccontextmanager
    async def session(cls) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        if cls._session_factory is None:
            cls.init()
            if cls._session_factory is None:
                raise RuntimeError("Failed to initialize database")

        assert cls._session_factory is not None  # For type checker
        async with cls._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @classmethod
    async def close(cls) -> None:
        """Close database connection."""
        if cls._engine is not None:
            await cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a database session."""
    async with Database.session() as session:
        yield session

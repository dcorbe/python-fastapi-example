"""Database connection and session management."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    """Database connection manager."""

    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    @staticmethod
    def _convert_database_url(url: str) -> str:
        """Convert standard postgres URL to asyncpg format."""
        parsed = urlparse(url)

        # Handle different prefix formats
        if parsed.scheme in ("postgresql", "postgres"):
            scheme = "postgresql+asyncpg"
        else:
            raise ValueError(f"Unsupported database scheme: {parsed.scheme}")

        # Reconstruct the URL with the new scheme
        return url.replace(f"{parsed.scheme}://", f"{scheme}://", 1)

    @classmethod
    def init(cls) -> None:
        """Initialize database connection."""
        url = os.getenv("DATABASE_URL")
        if url is None:
            raise ValueError("DATABASE_URL environment variable must be set")

        # Convert URL to asyncpg format
        try:
            sql_url = cls._convert_database_url(url)
            print(
                f"Using SQLAlchemy URL: {sql_url}"
            )  # Safe to print entire URL here as it will be masked by logs
        except ValueError as e:
            raise ValueError(f"Invalid database URL: {str(e)}")

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

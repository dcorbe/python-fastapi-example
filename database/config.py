"""Database configuration module."""

from __future__ import annotations

from config import get_settings


def get_database_url() -> str:
    """Get database URL from settings with proper driver."""
    settings = get_settings()
    url = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@localhost:5432/{settings.DB_NAME}"
    return url.replace("postgresql://", "postgresql+asyncpg://", 1)


def get_sync_database_url() -> str:
    """Get synchronous database URL for migrations."""
    settings = get_settings()
    return f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@localhost:5432/{settings.DB_NAME}"

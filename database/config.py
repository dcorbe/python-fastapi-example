"""Database configuration module."""

from __future__ import annotations

import os
from urllib.parse import urlparse


def get_database_url() -> str:
    """Get database URL from environment with proper driver."""
    url = os.getenv("DATABASE_URL")
    if url is None:
        raise ValueError("DATABASE_URL environment variable must be set")

    parsed = urlparse(url)

    if parsed.scheme in ("postgresql", "postgres"):
        scheme = "postgresql+asyncpg"
        return url.replace(f"{parsed.scheme}://", f"{scheme}://", 1)

    # Already has the correct scheme
    if parsed.scheme == "postgresql+asyncpg":
        return url

    raise ValueError(f"Unsupported database scheme: {parsed.scheme}")


def get_sync_database_url() -> str:
    """Get synchronous database URL for migrations."""
    url = os.getenv("DATABASE_URL")
    if url is None:
        raise ValueError("DATABASE_URL environment variable must be set")

    parsed = urlparse(url)

    # Convert to asyncpg URL first to ensure consistent handling
    if parsed.scheme in ("postgresql", "postgres"):
        url = url.replace(f"{parsed.scheme}://", "postgresql+asyncpg://", 1)
        parsed = urlparse(url)

    # Now convert asyncpg to sqlalchemy sync URL
    if parsed.scheme == "postgresql+asyncpg":
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)

    raise ValueError(f"Unsupported database scheme: {parsed.scheme}")

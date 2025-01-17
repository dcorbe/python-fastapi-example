"""Add a new user to the database."""

import argparse
import asyncio
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from auth.password import hash_password
from config import get_settings
from v1.users.models import User


async def main(email: str, password: str, force: bool = False) -> None:
    """Add a new user to the database."""
    settings = get_settings()

    # Construct database URL
    db_url = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@localhost:5432/{settings.DB_NAME}"
    engine: AsyncEngine = create_async_engine(db_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # Check if user exists (using direct ILIKE on email column)
        stmt = select(User.id, User.email).where(User.email.ilike(email))
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user is not None:
            if force:
                # Delete existing user
                await session.execute(delete(User).where(User.email.ilike(email)))
                await session.commit()
                print(f"Deleted existing user {email}")
            else:
                print(f"Error: User {email} already exists")
                print("Use --force to overwrite the existing user")
                return

        # Create user
        user = User(
            email=email,
            password_hash=hash_password(password),
            created_at=datetime.now(UTC),
            last_login=None,
        )
        session.add(user)
        await session.commit()
        print(f"User {email} created successfully")

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add a new user to the database")
    parser.add_argument("email", help="User's email address")
    parser.add_argument("password", help="User's password")
    parser.add_argument("--force", action="store_true", help="Overwrite existing user")

    args = parser.parse_args()
    asyncio.run(main(args.email, args.password, args.force))

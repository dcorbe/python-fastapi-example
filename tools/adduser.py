"""Add a new user to the database."""

import asyncio
import sys
from datetime import UTC, datetime
from typing import NoReturn

from sqlalchemy import select

from auth.config import RedisConfig
from auth.models import AuthConfig
from auth.redis import RedisService
from auth.service import AuthService
from config import get_settings
from database.session import async_session_factory
from v1.users.models import User


async def main(email: str, password: str) -> None:
    """Add a new user to the database."""
    settings = get_settings()

    # Initialize auth service
    auth_config = AuthConfig(
        jwt_secret_key=settings.JWT_SECRET,
        jwt_algorithm=settings.JWT_ALGORITHM,
        access_token_expire_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        max_login_attempts=settings.MAX_LOGIN_ATTEMPTS,
        lockout_minutes=settings.LOCKOUT_MINUTES,
    )

    redis_config = RedisConfig(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
    )

    redis_service = RedisService(redis_config)
    auth_service = AuthService(auth_config, redis_service)

    # Setup database
    async with async_session_factory() as session:
        # Check if user exists
        stmt = select(User).where(User.email.ilike(email))
        result = await session.execute(stmt)
        if result.scalar_one_or_none() is not None:
            print(f"User {email} already exists")
            return

        # Create user
        user = User(
            email=email,
            password_hash=auth_service.hash_password(password),
            created_at=datetime.now(UTC),
            last_login=None,
        )
        session.add(user)
        await session.commit()

        print(f"User {email} created successfully")

    await redis_service.close()


def show_usage() -> NoReturn:
    """Show usage information."""
    print("Usage: adduser.py <email> <password>")
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        show_usage()

    asyncio.run(main(sys.argv[1], sys.argv[2]))

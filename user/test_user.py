"""User management unit tests."""

from datetime import datetime, UTC, timedelta
from typing import AsyncGenerator
from uuid import UUID

import pytest
import pytest_asyncio
from pydantic import ValidationError
from sqlalchemy import text, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import Database
from config import get_settings
from .model import User
from .operations import (
    get_user_by_email,
    get_user_by_id,
    get_all_users,
    create_user,
    update_user,
    delete_user,
)
from .schemas import UserCreate, UserUpdate


@pytest_asyncio.fixture(autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """Setup test database."""
    Database.init()
    yield
    await Database.close()


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing."""
    async with Database.session() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(session: AsyncSession) -> User:
    """Create a test user."""
    user_data = UserCreate(
        email="test@example.com",
        password_hash="hashed_password_123",
        email_verified=False,
    )

    # Clear any existing test user
    await session.execute(
        text("DELETE FROM users WHERE email = :email"), {"email": user_data.email}
    )

    user = await create_user(session, user_data)
    return user


@pytest.mark.asyncio
async def test_create_user(session: AsyncSession) -> None:
    """Test user creation."""
    user_data = UserCreate(
        email="create_test@example.com",
        password_hash="hashed_password_123",
    )

    user = await create_user(session, user_data)
    assert user.id is not None
    assert user.email == user_data.email
    assert user.password_hash == user_data.password_hash
    assert user.email_verified is False
    assert user.created_at is not None
    assert user.failed_login_attempts == 0
    assert user.last_login is None
    assert user.locked_until is None


@pytest.mark.asyncio
async def test_get_user(session: AsyncSession, test_user: User) -> None:
    """Test user retrieval."""
    # Test get by email
    user = await get_user_by_email(session, test_user.email)
    assert user is not None
    assert user.id == test_user.id

    # Test get by ID
    user = await get_user_by_id(session, test_user.id)
    assert user is not None
    assert user.email == test_user.email

    # Test case-insensitive email lookup
    user = await get_user_by_email(
        session, test_user.email.upper(), case_insensitive=True
    )
    assert user is not None
    assert user.id == test_user.id


@pytest.mark.asyncio
async def test_update_user(session: AsyncSession, test_user: User) -> None:
    """Test user updates."""
    # Update email verification
    update_data = UserUpdate(email_verified=True)
    updated_user = await update_user(session, test_user, update_data)
    assert updated_user.email_verified is True

    # Update email
    new_email = "new@example.com"
    update_data = UserUpdate(email=new_email)
    updated_user = await update_user(session, updated_user, update_data)
    assert updated_user.email == new_email

    # Verify old email doesn't exist
    old_user = await get_user_by_email(session, "test@example.com")
    assert old_user is None


@pytest.mark.asyncio
async def test_delete_user(session: AsyncSession, test_user: User) -> None:
    """Test user deletion."""
    await delete_user(session, test_user)

    # Verify user is deleted
    deleted_user = await get_user_by_id(session, test_user.id)
    assert deleted_user is None


@pytest.mark.asyncio
async def test_get_all_users(session: AsyncSession) -> None:
    """Test retrieving multiple users."""
    # First, ensure we have a clean slate
    await session.execute(text("DELETE FROM users"))
    await session.commit()

    # Create multiple users with unique emails
    users_data = [
        UserCreate(email=f"test{i}@unique.example.com", password_hash=f"hash{i}")
        for i in range(3)
    ]

    # Create users one by one
    created_users = []
    for user_data in users_data:
        user = await create_user(session, user_data)
        created_users.append(user)

    # Test retrieving all users
    all_users = await get_all_users(session)
    assert len(all_users) == 3
    assert len({u.email for u in all_users}) == 3  # Verify emails are unique

    # Test pagination
    paged_users = await get_all_users(session, limit=2)
    assert len(paged_users) == 2


@pytest.mark.asyncio
async def test_user_constraints(session: AsyncSession) -> None:
    """Test database constraints and validation."""
    email = "constraint_test@example.com"
    # Clean up any existing test data
    await session.execute(
        text("DELETE FROM users WHERE email = :email"), {"email": email}
    )
    await session.commit()

    # Test duplicate email
    user_data = UserCreate(email=email, password_hash="hash1")
    await create_user(session, user_data)

    with pytest.raises(IntegrityError):
        await create_user(session, user_data)

    # Test invalid email format
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", password_hash="hash")


@pytest.mark.asyncio
async def test_user_locking(session: AsyncSession, test_user: User) -> None:
    """Test user locking functionality."""
    # Initially not locked
    assert not test_user.is_locked

    # Lock the user
    lock_time = datetime.now(UTC) + timedelta(minutes=30)
    update_data = UserUpdate(failed_login_attempts=3, locked_until=lock_time)
    locked_user = await update_user(session, test_user, update_data)

    # Verify lock
    assert locked_user.is_locked
    assert locked_user.failed_login_attempts == 3

    # Unlock the user
    update_data = UserUpdate(failed_login_attempts=0, locked_until=None)
    unlocked_user = await update_user(session, locked_user, update_data)

    # Verify unlock
    assert not unlocked_user.is_locked
    assert unlocked_user.failed_login_attempts == 0

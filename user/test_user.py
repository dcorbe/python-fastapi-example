"""User management unit tests."""
import os
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
from .model import User
from .operations import (
    get_user_by_email,
    get_user_by_id,
    get_all_users,
    create_user,
    update_user,
    delete_user,
)
from .schemas import UserCreate, UserUpdate, UserResponse


async def _clear_all_tables(session: AsyncSession) -> None:
    """Clear all test data from tables."""
    await session.execute(text("TRUNCATE TABLE users CASCADE"))
    await session.commit()


@pytest_asyncio.fixture(autouse=True)
async def setup_test_database() -> AsyncGenerator[None, None]:
    """Setup test database environment."""
    if "TEST_DATABASE_URL" not in os.environ:
        raise ValueError("TEST_DATABASE_URL environment variable must be set")
    
    # Store original DATABASE_URL if it exists
    original_db_url = os.environ.get("DATABASE_URL")
    
    try:
        # Use test database URL
        os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
        Database.init()
        
        # Clear test data before each test
        async with Database.session() as session:
            await _clear_all_tables(session)
        
        yield
        
    finally:
        # Clear all test data after each test
        try:
            async with Database.session() as session:
                await _clear_all_tables(session)
        except Exception:
            pass  # Ensure cleanup doesn't prevent other cleanup steps
        
        # Close all connections
        await Database.close()
        
        # Restore original DATABASE_URL if it existed
        if original_db_url is not None:
            os.environ["DATABASE_URL"] = original_db_url
        else:
            del os.environ["DATABASE_URL"]
        
        # Reset Database class state
        Database._engine = None
        Database._session_factory = None


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing."""
    async with Database.session() as session:
        yield session
        # Ensure transaction is rolled back even if test fails
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(session: AsyncSession) -> AsyncGenerator[User, None]:
    """Create a test user."""
    user_data = UserCreate(
        email="test@example.com",
        password_hash="hashed_password_123",
        email_verified=False
    )
    user = await create_user(session, user_data)
    yield user


@pytest.mark.asyncio
async def test_create_user(session: AsyncSession) -> None:
    """Test user creation."""
    user_data = UserCreate(
        email="test@example.com",
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
    user = await get_user_by_email(session, test_user.email.upper(), case_insensitive=True)
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
    # Create multiple users
    users_data = [
        UserCreate(email=f"user{i}@example.com", password_hash=f"hash{i}")
        for i in range(3)
    ]
    
    for user_data in users_data:
        await create_user(session, user_data)
    
    # Test retrieving all users
    all_users = await get_all_users(session)
    assert len(all_users) == 3
    
    # Test pagination
    paged_users = await get_all_users(session, limit=2)
    assert len(paged_users) == 2


@pytest.mark.asyncio
async def test_user_constraints(session: AsyncSession) -> None:
    """Test database constraints and validation."""
    # Test duplicate email
    user_data = UserCreate(
        email="test@example.com",
        password_hash="hash1"
    )
    await create_user(session, user_data)
    
    with pytest.raises(IntegrityError):
        await create_user(session, user_data)
    
    # Test invalid email format
    with pytest.raises(ValidationError):
        UserCreate(
            email="not-an-email",
            password_hash="hash"
        )


@pytest.mark.asyncio
async def test_user_locking(session: AsyncSession, test_user: User) -> None:
    """Test user locking functionality."""
    # Initially not locked
    assert not test_user.is_locked
    
    # Lock the user
    lock_time = datetime.now(UTC) + timedelta(minutes=30)
    update_data = UserUpdate(
        failed_login_attempts=3,
        locked_until=lock_time
    )
    locked_user = await update_user(session, test_user, update_data)
    
    # Verify lock
    assert locked_user.is_locked
    assert locked_user.failed_login_attempts == 3
    
    # Unlock the user
    update_data = UserUpdate(
        failed_login_attempts=0,
        locked_until=None
    )
    unlocked_user = await update_user(session, locked_user, update_data)
    
    # Verify unlock
    assert not unlocked_user.is_locked
    assert unlocked_user.failed_login_attempts == 0
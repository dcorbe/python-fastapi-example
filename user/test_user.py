"""User model unit tests."""
import os
from datetime import datetime, UTC
from typing import AsyncGenerator
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Database
from database.models import User


@pytest_asyncio.fixture(autouse=True)
async def setup_test_database() -> AsyncGenerator[None, None]:
    """Setup test database environment."""
    if "TEST_DATABASE_URL" not in os.environ:
        raise ValueError("TEST_DATABASE_URL environment variable must be set")
    
    # Use test database URL
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
    Database.init()
    
    # Clear test data before each test
    async with Database.session() as session:
        await session.execute(text("DELETE FROM users"))
        await session.commit()
    
    yield
    
    # Cleanup after tests
    await Database.close()


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing."""
    async with Database.session() as session:
        yield session


@pytest.mark.asyncio
async def test_user_crud(session: AsyncSession) -> None:
    """Test creating, reading, updating, and deleting a user."""
    # Create test user
    test_user = User(
        email="test@example.com",
        password_hash="hashed_password_123",
        email_verified=False
    )
    
    session.add(test_user)
    await session.commit()
    assert test_user.id is not None
    
    # Retrieve user
    stmt = select(User).where(User.email == "test@example.com")
    result = await session.execute(stmt)
    retrieved_user = result.scalar_one()
    assert retrieved_user is not None
    assert retrieved_user.email == test_user.email
    assert not retrieved_user.email_verified
    
    # Update user
    retrieved_user.email_verified = True
    await session.commit()
    
    # Verify update
    stmt = select(User).where(User.email == "test@example.com")
    result = await session.execute(stmt)
    updated_user = result.scalar_one()
    assert updated_user is not None
    assert updated_user.email_verified
    
    # Delete user
    await session.delete(updated_user)
    await session.commit()
    
    # Verify deletion
    stmt = select(User).where(User.email == "test@example.com")
    result = await session.execute(stmt)
    deleted_check = result.scalar_one_or_none()
    assert deleted_check is None


@pytest.mark.asyncio
async def test_user_email_case_insensitive(session: AsyncSession) -> None:
    """Test case-insensitive email lookup."""
    # Create test user with mixed case email
    test_user = User(
        email="Test.User@Example.com",
        password_hash="hashed_password_123",
        email_verified=False
    )
    session.add(test_user)
    await session.commit()
    
    # Try to retrieve with different case
    stmt = select(User).where(User.email.ilike("test.user@example.com"))
    result = await session.execute(stmt)
    retrieved_user = result.scalar_one()
    assert retrieved_user is not None
    assert retrieved_user.email == test_user.email


@pytest.mark.asyncio
async def test_user_constraints(session: AsyncSession) -> None:
    """Test database constraints on user model."""
    from sqlalchemy.exc import IntegrityError
    
    # Test email uniqueness
    user1 = User(
        email="same@example.com",
        password_hash="hash1"
    )
    session.add(user1)
    await session.commit()
    
    # Try to create user with duplicate email
    user2 = User(
        email="same@example.com",
        password_hash="hash2"
    )
    session.add(user2)
    with pytest.raises(IntegrityError) as exc_info:
        await session.commit()
    await session.rollback()
    
    # Test invalid email format
    invalid_user = User(
        email="not-an-email",
        password_hash="hash"
    )
    session.add(invalid_user)
    with pytest.raises(IntegrityError) as exc_info:
        await session.commit()
    await session.rollback()


@pytest.mark.asyncio
async def test_user_login_tracking(session: AsyncSession) -> None:
    """Test user login-related fields."""
    test_user = User(
        email="test@example.com",
        password_hash="hash"
    )
    session.add(test_user)
    await session.commit()
    
    # Update login attempts
    test_user.failed_login_attempts += 1
    await session.commit()
    
    # Verify update
    stmt = select(User).where(User.email == "test@example.com")
    result = await session.execute(stmt)
    retrieved_user = result.scalar_one()
    assert retrieved_user is not None
    assert retrieved_user.failed_login_attempts == 1
    
    # Test last login update
    now = datetime.now(UTC)
    retrieved_user.last_login = now
    retrieved_user.failed_login_attempts = 0
    await session.commit()
    
    # Verify updates
    stmt = select(User).where(User.email == "test@example.com")
    result = await session.execute(stmt)
    updated_user = result.scalar_one()
    assert updated_user is not None
    assert updated_user.failed_login_attempts == 0
    assert updated_user.last_login is not None
    # Compare only up to seconds since microseconds might differ
    assert updated_user.last_login.replace(microsecond=0) == now.replace(microsecond=0)

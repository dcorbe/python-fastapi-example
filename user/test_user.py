import os
import pytest
import pytest_asyncio
from user import User
from database import Database
from typing import AsyncGenerator

@pytest_asyncio.fixture
async def db() -> AsyncGenerator[Database, None]:
    if "TEST_DATABASE_URL" not in os.environ:
        raise ValueError("TEST_DATABASE_URL environment variable must be set")
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
    db = await Database.connect()
    yield db
    await db.close()

@pytest.mark.asyncio
async def test_user_crud(db: Database) -> None:
    test_user = User(
        email="test@example.com",
        password_hash="hashed_password_123",
        email_verified=False
    )
    await test_user.save(db)
    assert test_user.id is not None
    
    retrieved_user = await User.get_by_email("test@example.com", db)
    assert retrieved_user is not None
    assert retrieved_user.email == test_user.email
    
    await retrieved_user.delete(db)
    deleted_check = await User.get_by_email("test@example.com", db)
    assert deleted_check is None

@pytest.mark.asyncio
async def test_user_email_case_insensitive(db: Database) -> None:
    test_user = User(
        email="Test.User@Example.com",
        password_hash="hashed_password_123",
        email_verified=False
    )
    await test_user.save(db)
    retrieved_user = await User.get_by_email("test.user@example.com", db)
    assert retrieved_user is not None
    assert retrieved_user.email == test_user.email
    await test_user.delete(db)

@pytest.mark.asyncio
async def test_user_required_fields(db: Database) -> None:
    with pytest.raises(ValueError):
        invalid_user = User(password_hash="hashed_password_123")
        await invalid_user.save(db)
    with pytest.raises(ValueError):
        invalid_user = User(email="test@example.com")
        await invalid_user.save(db)

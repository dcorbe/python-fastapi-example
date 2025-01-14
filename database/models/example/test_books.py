"""Test suite for Book model."""
import os
from datetime import datetime
from typing import AsyncGenerator
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy import text, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from database import Database
from database.models.example.books import Book


async def _clear_database(session: AsyncSession) -> None:
    """Reset the database to a clean state."""
    await session.execute(text("DROP TABLE IF EXISTS books CASCADE"))
    await session.execute(text("""
        CREATE TABLE books (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title VARCHAR(100) NOT NULL,
            author VARCHAR(100) NOT NULL,
            description VARCHAR(500),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """))
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
            await _clear_database(session)
        
        yield
        
    finally:
        # Clear all test data after each test
        async with Database.session() as session:
            await _clear_database(session)
            
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


@pytest_asyncio.fixture
async def test_book(session: AsyncSession) -> AsyncGenerator[Book, None]:
    """Create a test book."""
    book = Book(
        title="Test Book",
        author="Test Author",
        description="Test Description"
    )
    session.add(book)
    await session.commit()
    await session.refresh(book)
    yield book


@pytest.mark.asyncio
async def test_create_book(session: AsyncSession) -> None:
    """Test book creation."""
    book = Book(
        title="The Great Test",
        author="Testing Author",
        description="A book about testing"
    )
    session.add(book)
    await session.commit()
    await session.refresh(book)

    assert isinstance(book.id, UUID)
    assert book.title == "The Great Test"
    assert book.author == "Testing Author"
    assert book.description == "A book about testing"
    assert isinstance(book.created_at, datetime)


@pytest.mark.asyncio
async def test_create_book_without_description(session: AsyncSession) -> None:
    """Test book creation without optional description."""
    book = Book(
        title="No Description",
        author="Minimalist Author"
    )
    session.add(book)
    await session.commit()
    await session.refresh(book)

    assert isinstance(book.id, UUID)
    assert book.title == "No Description"
    assert book.author == "Minimalist Author"
    assert book.description is None


@pytest.mark.asyncio
async def test_get_book_by_id(session: AsyncSession, test_book: Book) -> None:
    """Test retrieving a book by ID."""
    retrieved_book = await Book.get_by_id(session, test_book.id)
    assert retrieved_book is not None
    assert retrieved_book.id == test_book.id
    assert retrieved_book.title == test_book.title
    assert retrieved_book.author == test_book.author
    assert retrieved_book.description == test_book.description


@pytest.mark.asyncio
async def test_get_book_by_field(session: AsyncSession, test_book: Book) -> None:
    """Test retrieving a book by field value."""
    # Test case-sensitive search
    book = await Book.get_by_field(session, "title", test_book.title)
    assert book is not None
    assert book.id == test_book.id

    # Test case-insensitive search
    book = await Book.get_by_field(
        session, 
        "title", 
        test_book.title.upper(), 
        case_insensitive=True
    )
    assert book is not None
    assert book.id == test_book.id

    # Test non-existent value
    book = await Book.get_by_field(session, "title", "Non-existent Book")
    assert book is None


@pytest.mark.asyncio
async def test_update_book(session: AsyncSession, test_book: Book) -> None:
    """Test updating a book."""
    # Update the book
    test_book.title = "Updated Title"
    test_book.author = "Updated Author"
    test_book.description = "Updated Description"
    await session.commit()
    await session.refresh(test_book)

    # Verify updates
    assert test_book.title == "Updated Title"
    assert test_book.author == "Updated Author"
    assert test_book.description == "Updated Description"

    # Verify changes persist after re-fetching
    refetched_book = await Book.get_by_id(session, test_book.id)
    assert refetched_book is not None
    assert refetched_book.title == "Updated Title"
    assert refetched_book.author == "Updated Author"
    assert refetched_book.description == "Updated Description"


@pytest.mark.asyncio
async def test_delete_book(session: AsyncSession, test_book: Book) -> None:
    """Test book deletion."""
    await session.delete(test_book)
    await session.commit()

    # Verify deletion
    deleted_book = await Book.get_by_id(session, test_book.id)
    assert deleted_book is None


@pytest.mark.asyncio
async def test_get_multiple_books(session: AsyncSession) -> None:
    """Test retrieving multiple books."""
    # Create multiple books
    books_data = [
        ("Book 1", "Author 1", "Description 1"),
        ("Book 2", "Author 2", "Description 2"),
        ("Book 3", "Author 3", "Description 3")
    ]
    
    for title, author, description in books_data:
        book = Book(title=title, author=author, description=description)
        session.add(book)
    await session.commit()

    # Fetch all books
    stmt = select(Book)
    result = await session.execute(stmt)
    books = result.scalars().all()

    assert len(books) == 3
    assert len({book.title for book in books}) == 3  # Verify unique titles


@pytest.mark.asyncio
async def test_field_constraints(session: AsyncSession) -> None:
    """Test database field constraints."""
    # Test title length constraint
    long_title = "x" * 101  # Exceeds VARCHAR(100)
    book = Book(
        title=long_title,
        author="Test Author"
    )
    session.add(book)
    with pytest.raises((DBAPIError)):
        await session.commit()
    await session.rollback()

    # Test author length constraint
    long_author = "x" * 101  # Exceeds VARCHAR(100)
    book = Book(
        title="Test Title",
        author=long_author
    )
    session.add(book)
    with pytest.raises((DBAPIError)):
        await session.commit()
    await session.rollback()

    # Test description length constraint
    long_description = "x" * 501  # Exceeds VARCHAR(500)
    book = Book(
        title="Test Title",
        author="Test Author",
        description=long_description
    )
    session.add(book)
    with pytest.raises((DBAPIError)):
        await session.commit()
    await session.rollback()

"""Unit tests for the books API endpoints."""

import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.token import get_current_user
from database.models import Book
from example.books import (
    BookCreate,
    BookResponse,
    BookUpdate,
    create_book,
    delete_book,
    list_books,
    read_book,
    update_book,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db() -> AsyncMock:
    """Create a mock database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def mock_user() -> MagicMock:
    """Create a mock authenticated user."""
    return MagicMock()


@pytest.fixture
def sample_book() -> Book:
    """Create a sample book for testing."""
    return Book(
        id=uuid.uuid4(),
        title="Test Book",
        author="Test Author",
        description="Test Description",
        created_at=datetime.now(timezone.utc),
    )


async def test_create_book_success(mock_db: AsyncMock, mock_user: MagicMock) -> None:
    """Test successful book creation."""
    book_data = BookCreate(
        title="Test Book", author="Test Author", description="Test Description"
    )

    result = await create_book(mock_user, book_data, mock_db)

    assert mock_db.add.called
    await mock_db.commit()
    assert isinstance(result, Book)
    assert result.title == book_data.title
    assert result.author == book_data.author
    assert result.description == book_data.description


async def test_create_book_failure(mock_db: AsyncMock, mock_user: MagicMock) -> None:
    """Test book creation with database error."""
    book_data = BookCreate(
        title="Test Book", author="Test Author", description="Test Description"
    )
    mock_db.commit.side_effect = IntegrityError(
        statement=None, params=None, orig=Exception("Duplicate entry")
    )

    with pytest.raises(HTTPException) as exc_info:
        await create_book(mock_user, book_data, mock_db)

    assert exc_info.value.status_code == 400
    await mock_db.rollback()


async def test_read_book_success(
    mock_db: AsyncMock, mock_user: MagicMock, sample_book: Book
) -> None:
    """Test successful book retrieval."""
    book_id = sample_book.id
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_book
    mock_db.execute.return_value = mock_result

    result = await read_book(mock_user, book_id, mock_db)

    assert result == sample_book
    mock_db.execute.assert_called_once()


async def test_read_book_not_found(mock_db: AsyncMock, mock_user: MagicMock) -> None:
    """Test book retrieval when book doesn't exist."""
    book_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await read_book(mock_user, book_id, mock_db)

    assert exc_info.value.status_code == 404


async def test_list_books(
    mock_db: AsyncMock, mock_user: MagicMock, sample_book: Book
) -> None:
    """Test listing all books."""
    mock_result = MagicMock()
    all_result = [sample_book]
    mock_result.scalars.return_value.all.return_value = all_result
    mock_db.execute.return_value = mock_result

    result = await list_books(mock_user, mock_db)

    assert len(result) == 1
    assert result[0] == sample_book
    mock_db.execute.assert_called_once()


async def test_update_book_success(
    mock_db: AsyncMock, mock_user: MagicMock, sample_book: Book
) -> None:
    """Test successful book update."""
    book_id = sample_book.id
    update_data = BookUpdate(title="Updated Title")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_book
    mock_db.execute.return_value = mock_result

    result = await update_book(mock_user, book_id, update_data, mock_db)

    assert result.title == "Updated Title"
    await mock_db.commit()
    await mock_db.refresh()


async def test_update_book_not_found(mock_db: AsyncMock, mock_user: MagicMock) -> None:
    """Test updating non-existent book."""
    book_id = uuid.uuid4()
    update_data = BookUpdate(title="Updated Title")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await update_book(mock_user, book_id, update_data, mock_db)

    assert exc_info.value.status_code == 404


async def test_update_book_failure(
    mock_db: AsyncMock, mock_user: MagicMock, sample_book: Book
) -> None:
    """Test book update with database error."""
    book_id = sample_book.id
    update_data = BookUpdate(title="Updated Title")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_book
    mock_db.execute.return_value = mock_result
    mock_db.commit.side_effect = IntegrityError(
        statement=None, params=None, orig=Exception("Duplicate entry")
    )

    with pytest.raises(HTTPException) as exc_info:
        await update_book(mock_user, book_id, update_data, mock_db)

    assert exc_info.value.status_code == 400
    await mock_db.rollback()


async def test_delete_book_success(
    mock_db: AsyncMock, mock_user: MagicMock, sample_book: Book
) -> None:
    """Test successful book deletion."""
    book_id = sample_book.id
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_book
    mock_db.execute.return_value = mock_result

    await delete_book(mock_user, book_id, mock_db)

    await mock_db.delete(sample_book)
    await mock_db.commit()


async def test_delete_book_not_found(mock_db: AsyncMock, mock_user: MagicMock) -> None:
    """Test deleting non-existent book."""
    book_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await delete_book(mock_user, book_id, mock_db)

    assert exc_info.value.status_code == 404

"""Unit tests for the books API endpoints."""

import uuid
from datetime import UTC, datetime
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from database.models.example.books import Book as BookModel
from example.books import *  # noqa: F403

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
def sample_book_model() -> BookModel:
    """Create a sample book model for testing."""
    return BookModel(
        id=uuid.uuid4(),
        title="Test Book",
        author="Test Author",
        description="Test Description",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_book(sample_book_model: BookModel) -> "Book":  # noqa: F405
    """Create a sample book Pydantic model for testing."""
    return Book.model_validate(sample_book_model)  # noqa: F405


async def test_create_book_success(mock_db: AsyncMock, mock_user: MagicMock) -> None:
    """Test successful book creation."""
    book_data = BookCreate(  # noqa: F405
        title="Test Book", author="Test Author", description="Test Description"
    )

    # Create expected book model after creation
    created_at = datetime.now(UTC)
    book_id = uuid.uuid4()

    def add_book(book: BookModel) -> None:
        """Set ID and created_at when book is added."""
        book.id = book_id
        book.created_at = created_at

    mock_db.add.side_effect = add_book
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None

    result = await create_book(mock_user, book_data, mock_db)  # noqa: F405

    # Verify the result
    assert isinstance(result, Book)  # noqa: F405
    assert result.title == book_data.title
    assert result.author == book_data.author
    assert result.description == book_data.description
    assert result.id == book_id
    assert result.created_at == created_at

    # Verify the expected calls
    mock_db.add.assert_called_once_with(ANY)
    await mock_db.commit()
    await mock_db.refresh(ANY)


async def test_create_book_failure(mock_db: AsyncMock, mock_user: MagicMock) -> None:
    """Test book creation with database error."""
    book_data = BookCreate(  # noqa: F405
        title="Test Book", author="Test Author", description="Test Description"
    )
    mock_db.commit.side_effect = IntegrityError(
        statement=None, params=None, orig=Exception("Duplicate entry")
    )

    with pytest.raises(HTTPException) as exc_info:
        await create_book(mock_user, book_data, mock_db)  # noqa: F405

    assert exc_info.value.status_code == 400
    await mock_db.rollback()


async def test_read_book_success(
    mock_db: AsyncMock, mock_user: MagicMock, sample_book_model: BookModel
) -> None:
    """Test successful book retrieval."""
    book_id = sample_book_model.id
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_book_model
    mock_db.execute.return_value = mock_result

    result = await read_book(mock_user, book_id, mock_db)  # noqa: F405

    assert isinstance(result, Book)  # noqa: F405
    assert result.title == sample_book_model.title
    assert result.author == sample_book_model.author
    mock_db.execute.assert_called_once()


async def test_read_book_not_found(mock_db: AsyncMock, mock_user: MagicMock) -> None:
    """Test book retrieval when book doesn't exist."""
    book_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await read_book(mock_user, book_id, mock_db)  # noqa: F405

    assert exc_info.value.status_code == 404


async def test_list_books(
    mock_db: AsyncMock, mock_user: MagicMock, sample_book_model: BookModel
) -> None:
    """Test listing all books."""
    mock_result = MagicMock()
    all_result = [sample_book_model]
    mock_result.scalars.return_value.all.return_value = all_result
    mock_db.execute.return_value = mock_result

    result = await list_books(mock_user, mock_db)  # noqa: F405

    assert len(result) == 1
    assert isinstance(result[0], Book)  # noqa: F405
    assert result[0].title == sample_book_model.title
    assert result[0].author == sample_book_model.author
    mock_db.execute.assert_called_once()


async def test_update_book_success(
    mock_db: AsyncMock, mock_user: MagicMock, sample_book_model: BookModel
) -> None:
    """Test successful book update."""
    book_id = sample_book_model.id
    update_data = BookUpdate(title="Updated Title")  # noqa: F405
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_book_model
    mock_db.execute.return_value = mock_result

    result = await update_book(mock_user, book_id, update_data, mock_db)  # noqa: F405

    assert isinstance(result, Book)  # noqa: F405
    assert result.title == update_data.title
    await mock_db.commit()
    await mock_db.refresh()


async def test_update_book_not_found(mock_db: AsyncMock, mock_user: MagicMock) -> None:
    """Test updating non-existent book."""
    book_id = uuid.uuid4()
    update_data = BookUpdate(title="Updated Title")  # noqa: F405
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await update_book(mock_user, book_id, update_data, mock_db)  # noqa: F405

    assert exc_info.value.status_code == 404


async def test_update_book_failure(
    mock_db: AsyncMock, mock_user: MagicMock, sample_book_model: BookModel
) -> None:
    """Test book update with database error."""
    book_id = sample_book_model.id
    update_data = BookUpdate(title="Updated Title")  # noqa: F405
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_book_model
    mock_db.execute.return_value = mock_result
    mock_db.commit.side_effect = IntegrityError(
        statement=None, params=None, orig=Exception("Duplicate entry")
    )

    with pytest.raises(HTTPException) as exc_info:
        await update_book(mock_user, book_id, update_data, mock_db)  # noqa: F405

    assert exc_info.value.status_code == 400
    await mock_db.rollback()


async def test_delete_book_success(
    mock_db: AsyncMock, mock_user: MagicMock, sample_book_model: BookModel
) -> None:
    """Test successful book deletion."""
    book_id = sample_book_model.id
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_book_model
    mock_db.execute.return_value = mock_result

    await delete_book(mock_user, book_id, mock_db)  # noqa: F405

    await mock_db.delete(sample_book_model)
    await mock_db.commit()


async def test_delete_book_not_found(mock_db: AsyncMock, mock_user: MagicMock) -> None:
    """Test deleting non-existent book."""
    book_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await delete_book(mock_user, book_id, mock_db)  # noqa: F405

    assert exc_info.value.status_code == 404

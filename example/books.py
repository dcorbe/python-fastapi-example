"""Example of database queries and async route handlers."""

from datetime import UTC, datetime
from typing import Annotated, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.token import get_current_user
from database import get_db
from database.models.example.books import Book as BookModel
from v1.users.models import User


# Schema definitions
class BookBase(BaseModel):
    """Base book schema."""

    title: str
    author: str
    description: str | None = None


class BookCreate(BookBase):
    """Schema for creating a new book."""

    pass


class BookUpdate(BaseModel):
    """Schema for updating a book."""

    title: str | None = None
    author: str | None = None
    description: str | None = None


class Book(BookBase):
    """Book response schema."""

    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # Updated for Pydantic v2


# Router and endpoints
router = APIRouter(prefix="/books")


@router.post(
    "",
    response_model=Book,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book",
    description="Create a new book in the database",
    operation_id="createBook",
    responses={
        201: {
            "description": "Successfully created book",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "title": "Sample Book",
                        "author": "John Doe",
                        "description": "A great book about things",
                        "created_at": "2024-01-16T10:00:00Z",
                    }
                }
            },
        },
        400: {"description": "Invalid book data"},
    },
)
async def create_book(
    current_user: Annotated[User, Depends(get_current_user)],
    book_data: BookCreate,
    db: AsyncSession = Depends(get_db),
) -> Book:
    """Create a new book."""
    try:
        now = datetime.now(UTC)
        book = BookModel(
            id=uuid4(),
            title=book_data.title,
            author=book_data.author,
            description=book_data.description,
            created_at=now,
        )
        db.add(book)
        await db.commit()
        await db.refresh(book)
        return Book.model_validate(book)  # Convert to Pydantic model
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.orig),
        ) from e


@router.get(
    "",
    response_model=List[Book],
    summary="Get all books",
    description="Get a list of all books in the database",
    operation_id="getAllBooks",
    responses={
        200: {
            "description": "Successfully retrieved all books",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "title": "Sample Book",
                            "author": "John Doe",
                            "description": "A great book about things",
                            "created_at": "2024-01-16T10:00:00Z",
                        }
                    ]
                }
            },
        }
    },
)
async def list_books(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> List[Book]:
    """Get all books."""
    stmt = select(BookModel)
    result = await db.execute(stmt)
    books = list(result.scalars().all())
    return [Book.model_validate(book) for book in books]  # Convert to Pydantic models


@router.get(
    "/{book_id}",
    response_model=Book,
    summary="Get book by ID",
    description="Get a specific book by its ID",
    operation_id="getBookById",
    responses={
        200: {
            "description": "Successfully retrieved the book",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "title": "Sample Book",
                        "author": "John Doe",
                        "description": "A great book about things",
                        "created_at": "2024-01-16T10:00:00Z",
                    }
                }
            },
        },
        404: {"description": "Book not found"},
    },
)
async def read_book(
    current_user: Annotated[User, Depends(get_current_user)],
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Book:
    """Get a book by its ID."""
    stmt = select(BookModel).where(BookModel.id == book_id)
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    return Book.model_validate(book)  # Convert to Pydantic model


@router.patch(
    "/{book_id}",
    response_model=Book,
    summary="Update book",
    description="Update a book's details",
    operation_id="updateBook",
    responses={
        200: {
            "description": "Successfully updated the book",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "title": "Updated Book",
                        "author": "John Doe",
                        "description": "An updated book about things",
                        "created_at": "2024-01-16T10:00:00Z",
                    }
                }
            },
        },
        404: {"description": "Book not found"},
        400: {"description": "Invalid update data"},
    },
)
async def update_book(
    current_user: Annotated[User, Depends(get_current_user)],
    book_id: UUID,
    update_data: BookUpdate,
    db: AsyncSession = Depends(get_db),
) -> Book:
    """Update a book's details."""
    stmt = select(BookModel).where(BookModel.id == book_id)
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(book, key, value)

    try:
        await db.commit()
        await db.refresh(book)
        return Book.model_validate(book)  # Convert to Pydantic model
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.orig),
        ) from e


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete book",
    description="Delete a book from the database",
    operation_id="deleteBook",
    responses={
        204: {"description": "Successfully deleted the book"},
        404: {"description": "Book not found"},
    },
)
async def delete_book(
    current_user: Annotated[User, Depends(get_current_user)],
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a book."""
    stmt = select(BookModel).where(BookModel.id == book_id)
    result = await db.execute(stmt)
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    await db.delete(book)
    await db.commit()

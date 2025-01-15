"""Books API providing CRUD operations for managing a book collection.

This module implements a RESTful API for managing books, including:
- Creating new books
- Retrieving individual books or listing all books
- Updating existing books
- Deleting books

All operations require authentication using JWT tokens.
"""
from typing import List, Optional, Annotated
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.token import get_current_user
from database.models import Book
from database_manager import get_db
from user import User


class BookBase(BaseModel):
    """Base schema with common optional fields for both create and update operations."""
    title: Optional[str] = Field(
        default=None,
        description="The title of the book",
        examples=["The Great Gatsby"]
    )
    author: Optional[str] = Field(
        default=None,
        description="The author of the book",
        examples=["F. Scott Fitzgerald"]
    )
    description: Optional[str] = Field(
        default=None,
        description="A brief description or summary of the book",
        examples=["A story of the fabulously wealthy Jay Gatsby and his love for the beautiful Daisy Buchanan."]
    )


class BookCreate(BaseModel):
    """Schema for creating a new book with required fields."""
    title: str = Field(
        description="The title of the book",
        min_length=1,
        max_length=200,
        examples=["The Great Gatsby"]
    )
    author: str = Field(
        description="The author of the book",
        min_length=1,
        max_length=100,
        examples=["F. Scott Fitzgerald"]
    )
    description: Optional[str] = Field(
        default=None,
        description="A brief description or summary of the book",
        max_length=1000,
        examples=["A story of the fabulously wealthy Jay Gatsby and his love for the beautiful Daisy Buchanan."]
    )


class BookUpdate(BookBase):
    """Schema for updating an existing book. All fields are optional to support partial updates."""
    pass


class BookResponse(BaseModel):
    """Schema for book responses in all API operations."""
    id: UUID = Field(description="Unique identifier for the book")
    title: str = Field(description="The title of the book")
    author: str = Field(description="The author of the book")
    description: Optional[str] = Field(description="A brief description or summary of the book")
    created_at: datetime = Field(description="Timestamp when the book was created")
    
    model_config = ConfigDict(from_attributes=True)


router = APIRouter(
    prefix="/books",
    tags=["books"],
    responses={
        401: {"description": "Unauthorized - Authentication required"},
        403: {"description": "Forbidden - Insufficient permissions"},
        500: {"description": "Internal Server Error"}
    }
)


@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book",
    description="Create a new book with the provided details. Requires authentication.",
    responses={
        201: {"description": "Book created successfully"},
        400: {"description": "Invalid request (e.g., duplicate book or invalid data)"}
    },
    operation_id="createBook"
)
async def create_book(
    current_user: Annotated[User, Depends(get_current_user)],
    book: BookCreate,
    db: AsyncSession = Depends(get_db),
) -> Book:
    """Create a new book in the database.
    
    Args:
        current_user: The authenticated user making the request
        book: The book data to create
        db: Database session
        
    Returns:
        The created book
        
    Raises:
        HTTPException: If book creation fails (e.g., due to duplicate title)
    """
    db_book = Book(**book.model_dump())
    try:
        db.add(db_book)
        await db.commit()
        await db.refresh(db_book)
        return db_book
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book creation failed - book may already exist"
        )


@router.get(
    "/{book_id}",
    response_model=BookResponse,
    summary="Get a specific book",
    description="Retrieve a book by its ID. Requires authentication.",
    responses={
        200: {"description": "Book found and returned"},
        404: {"description": "Book not found"}
    },
    operation_id="getBook"
)
async def read_book(
    current_user: Annotated[User, Depends(get_current_user)],
    book_id: UUID = Path(..., description="The UUID of the book to retrieve"),
    db: AsyncSession = Depends(get_db),
) -> Book:
    """Retrieve a specific book by ID.
    
    Args:
        current_user: The authenticated user making the request
        book_id: The UUID of the book to retrieve
        db: Database session
        
    Returns:
        The requested book
        
    Raises:
        HTTPException: If the book is not found
    """
    query = select(Book).where(Book.id == book_id)
    result = await db.execute(query)
    if book := result.scalar_one_or_none():
        return book
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Book with ID {book_id} not found"
    )


@router.get(
    "",
    response_model=List[BookResponse],
    summary="List all books",
    description="Retrieve a list of all books. Requires authentication.",
    operation_id="listBooks"
)
async def list_books(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> List[Book]:
    """Retrieve all books from the database.
    
    Args:
        current_user: The authenticated user making the request
        db: Database session
        
    Returns:
        List of all books
    """
    query = select(Book)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.put(
    "/{book_id}",
    response_model=BookResponse,
    summary="Update a book",
    description="Update an existing book's details. Requires authentication. Only provided fields will be updated.",
    responses={
        200: {"description": "Book updated successfully"},
        400: {"description": "Invalid update data"},
        404: {"description": "Book not found"}
    },
    operation_id="updateBook"
)
async def update_book(
    current_user: Annotated[User, Depends(get_current_user)],
    book_id: UUID = Path(..., description="The UUID of the book to update"),
    book_update: BookUpdate = Body(..., description="The book data to update"),
    db: AsyncSession = Depends(get_db),
) -> Book:
    """Update a specific book's details.
    
    Args:
        current_user: The authenticated user making the request
        book_id: The UUID of the book to update
        book_update: The book data to update (partial updates supported)
        db: Database session
        
    Returns:
        The updated book
        
    Raises:
        HTTPException: If the book is not found or if the update fails
    """
    query = select(Book).where(Book.id == book_id)
    result = await db.execute(query)
    if db_book := result.scalar_one_or_none():
        # Only update non-None values
        update_data = book_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_book, key, value)
        try:
            await db.commit()
            await db.refresh(db_book)
            return db_book
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book update failed - invalid data or duplicate title"
            )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Book with ID {book_id} not found"
    )


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book",
    description="Delete a specific book. Requires authentication.",
    responses={
        204: {"description": "Book deleted successfully"},
        404: {"description": "Book not found"}
    },
    operation_id="deleteBook"
)
async def delete_book(
    current_user: Annotated[User, Depends(get_current_user)],
    book_id: UUID = Path(..., description="The UUID of the book to delete"),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a specific book.
    
    Args:
        current_user: The authenticated user making the request
        book_id: The UUID of the book to delete
        db: Database session
        
    Raises:
        HTTPException: If the book is not found
    """
    query = select(Book).where(Book.id == book_id)
    result = await db.execute(query)
    if db_book := result.scalar_one_or_none():
        await db.delete(db_book)
        await db.commit()
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
"""Example of a simple CRUD service using FastAPI and SQLAlchemy."""
from typing import List, Optional, Annotated
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.token import get_current_user
from database.models import Book
from database_manager import get_db
from user import User


class BookBase(BaseModel):
    """Base schema with common optional fields for both create and update."""
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None


class BookCreate(BaseModel):
    """Schema for creating a new book with required fields."""
    title: str
    author: str
    description: Optional[str] = None


class BookUpdate(BookBase):
    """Schema for updating an existing book. All fields are optional."""
    pass


class BookResponse(BaseModel):
    """Schema for book responses in all API operations."""
    id: UUID
    title: str
    author: str
    description: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


router = APIRouter(tags=["example"])


@router.post("/books", response_model=BookResponse, status_code=201)
async def create_book(
    current_user: Annotated[User, Depends(get_current_user)],
    book: BookCreate,
    db: AsyncSession = Depends(get_db),
) -> Book:
    """Create a new book."""
    db_book = Book(**book.model_dump())
    try:
        db.add(db_book)
        await db.commit()
        await db.refresh(db_book)
        return db_book
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Book creation failed")


@router.get("/books/{book_id}", response_model=BookResponse)
async def read_book(
    current_user: Annotated[User, Depends(get_current_user)],
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Book:
    """Get a book by ID."""
    query = select(Book).where(Book.id == book_id)
    result = await db.execute(query)
    if book := result.scalar_one_or_none():
        return book
    raise HTTPException(status_code=404, detail="Book not found")


@router.get("/books", response_model=List[BookResponse])
async def list_books(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> List[Book]:
    """List all books."""
    query = select(Book)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(
    current_user: Annotated[User, Depends(get_current_user)],
    book_id: UUID,
    book_update: BookUpdate,
    db: AsyncSession = Depends(get_db),
) -> Book:
    """Update a book."""
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
            raise HTTPException(status_code=400, detail="Book update failed")
    raise HTTPException(status_code=404, detail="Book not found")


@router.delete("/books/{book_id}", status_code=204)
async def delete_book(
    current_user: Annotated[User, Depends(get_current_user)],
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a book."""
    query = select(Book).where(Book.id == book_id)
    result = await db.execute(query)
    if db_book := result.scalar_one_or_none():
        await db.delete(db_book)
        await db.commit()
    else:
        raise HTTPException(status_code=404, detail="Book not found")

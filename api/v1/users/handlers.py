"""User management API endpoints."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database_manager import get_db
from user import (
    User,
    UserCreate,
    UserRead,
    UserUpdate,
    get_user_by_email,
    get_user_by_id,
    create_user,
    update_user,
    delete_user,
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post("/", response_model=UserRead, status_code=201)
async def create_new_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Create a new user."""
    # Check if user already exists
    if await get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    return await create_user(db, user_data)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get a user by ID."""
    if user := await get_user_by_id(db, user_id):
        return user
    raise HTTPException(status_code=404, detail="User not found")


@router.get("/", response_model=List[UserRead])
async def list_users(
    db: AsyncSession = Depends(get_db),
) -> List[User]:
    """List all users."""
    query = User.__table__.select()
    result = await db.execute(query)
    return list(result.scalars().all())


@router.patch("/{user_id}", response_model=UserRead)
async def update_user_info(
    user_id: UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Update a user."""
    # First get the existing user
    if not (user := await get_user_by_id(db, user_id)):
        raise HTTPException(status_code=404, detail="User not found")

    # If email is being updated, check it's not already taken
    if user_data.email and user_data.email != user.email:
        if await get_user_by_email(db, user_data.email):
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
    
    return await update_user(db, user, user_data)


@router.delete("/{user_id}", status_code=204)
async def delete_user_account(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a user."""
    if not (user := await get_user_by_id(db, user_id)):
        raise HTTPException(status_code=404, detail="User not found")
    
    await delete_user(db, user)
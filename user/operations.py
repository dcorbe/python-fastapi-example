"""Database operations for user management."""
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .model import User
from .schemas import UserCreate, UserUpdate


async def email_exists(db: AsyncSession, email: str) -> bool:
    """
    Check if an email already exists (case-insensitive).
    
    Args:
        db: Database session
        email: Email to check
    
    Returns:
        True if email exists, False otherwise
    """
    stmt = select(User).where(func.lower(User.email) == func.lower(email))
    result = await db.execute(stmt)
    return result.first() is not None


async def get_user_by_email(
    db: AsyncSession,
    email: str,
    case_insensitive: bool = True,
) -> Optional[User]:
    """
    Get user by email.
    
    Args:
        db: Database session
        email: Email address to search for
        case_insensitive: Whether to perform case-insensitive search
    
    Returns:
        User if found, None otherwise
    """
    stmt = select(User)
    if case_insensitive:
        stmt = stmt.where(func.lower(User.email) == func.lower(email))
    else:
        stmt = stmt.where(User.email == email)
    
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(
    db: AsyncSession,
    user_id: UUID,
) -> Optional[User]:
    """
    Get user by ID.
    
    Args:
        db: Database session
        user_id: User's UUID
    
    Returns:
        User if found, None otherwise
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_all_users(
    db: AsyncSession,
    *,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[User]:
    """
    Get all users with optional pagination.
    
    Args:
        db: Database session
        limit: Maximum number of users to return
        offset: Number of users to skip
    
    Returns:
        List of users
    """
    stmt = select(User)
    if limit is not None:
        stmt = stmt.limit(limit)
    if offset is not None:
        stmt = stmt.offset(offset)
    
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_user(
    db: AsyncSession,
    user: UserCreate,
) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        user: User creation data
    
    Returns:
        Created user
    
    Raises:
        IntegrityError: If user with same email already exists
    """
    if await email_exists(db, user.email):
        raise IntegrityError(
            "User with this email already exists",
            params={"email": user.email},
            orig=Exception("Email already exists")
        )
    
    db_user = User(**user.model_dump())
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except IntegrityError as e:
        await db.rollback()
        raise IntegrityError(
            "User with this email already exists",
            params=e.params,
            orig=e if e.orig is None else e.orig
        ) from e


async def update_user(
    db: AsyncSession,
    db_user: User,
    user_update: UserUpdate,
) -> User:
    """
    Update user data.
    
    Args:
        db: Database session
        db_user: Existing user to update
        user_update: Update data
    
    Returns:
        Updated user
    
    Raises:
        IntegrityError: If updating email to one that already exists
    """
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Check email uniqueness if email is being updated
    if "email" in update_data and update_data["email"] != db_user.email:
        if await email_exists(db, update_data["email"]):
            raise IntegrityError(
                "Email address already taken",
                params={"email": update_data["email"]},
                orig=Exception("Email already taken")
            )
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    try:
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except IntegrityError as e:
        await db.rollback()
        raise IntegrityError(
            "Email address already taken",
            params=e.params,
            orig=e if e.orig is None else e.orig
        ) from e


async def delete_user(
    db: AsyncSession,
    user: User,
) -> None:
    """
    Delete user.
    
    Args:
        db: Database session
        user: User to delete
    
    Raises:
        IntegrityError: If user cannot be deleted due to foreign key constraints
    """
    try:
        await db.delete(user)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise IntegrityError(
            "Cannot delete user due to existing references",
            params=e.params,
            orig=e if e.orig is None else e.orig
        ) from e

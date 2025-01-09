"""User management module for the BSS library.

This module provides the User model and related database operations. It handles user
creation, retrieval, and updates while managing attributes like email, password hashes,
and account status.

The User class implements:
    - Basic user attributes including email and password hash
    - Account status tracking (verified, locked)
    - Database operations
    - Login attempt tracking
"""
from datetime import datetime
from typing import Optional, Any, TypeVar, Sequence
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from database import Database
from psycopg.sql import SQL
from psycopg import AsyncCursor, AsyncConnection

T = TypeVar('T')

class User(BaseModel):
    """
    User model representing entries in the users table.
    Maps to the PostgreSQL users table schema.
    """
    id: Optional[UUID] = None
    email: Optional[EmailStr] = None
    password_hash: Optional[str] = None
    email_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = None

    @property
    def is_locked(self) -> bool:
        """Check if the user account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.now() < self.locked_until

    def _validate_required_fields(self) -> None:
        """Validate that required fields are set."""
        if self.email is None or self.password_hash is None:
            raise ValueError("Email and password hash must be set")
        # Type narrowing - after this check, we know these fields are not None
        assert self.email is not None
        assert self.password_hash is not None

    @staticmethod
    def _get_cursor(db: Database) -> AsyncCursor[Any]:
        """Get and validate database cursor."""
        if db.cur is None:
            raise ValueError("Database cursor not initialized")
        return db.cur

    @staticmethod
    def _get_connection(db: Database) -> AsyncConnection[Any]:
        """Get and validate database connection."""
        if db.conn is None:
            raise ValueError("Database connection not initialized")
        return db.conn

    @staticmethod
    def _row_to_dict(row: Sequence[Any], cursor: AsyncCursor[Any]) -> dict[str, Any]:
        """Convert a database row to a dictionary using column names."""
        if cursor.description is None:
            raise ValueError("No column descriptions available")
        columns = [desc.name for desc in cursor.description]
        return dict(zip(columns, row))

    @classmethod
    async def get_by_email(cls, email: str, db: Database) -> Optional['User']:
        """
        Retrieve a user by email address.

        Args:
            email: The email address to look up
            db: Database connection instance

        Returns:
            User instance if found, None otherwise
        """
        cursor = cls._get_cursor(db)
        await cursor.execute(
            SQL("SELECT * FROM users WHERE LOWER(email) = LOWER(%s)"),
            (email,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None

        return cls.model_validate(cls._row_to_dict(row, cursor))

    @classmethod
    async def get_by_uuid(cls, uuid: UUID, db: Database) -> Optional['User']:
        """
        Retrieve a user by UUID.

        Args:
            uuid: The UUID to look up
            db: Database connection instance

        Returns:
            User instance if found, None otherwise
        """
        cursor = cls._get_cursor(db)
        await cursor.execute(
            SQL("SELECT * FROM users WHERE id = %s"),
            (uuid,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None

        return cls.model_validate(cls._row_to_dict(row, cursor))

    async def save(self, db: Database) -> None:
        """
        Save or update the user in the database.

        Args:
            db: Database connection instance

        Raises:
            ValueError: If database cursor is not initialized or required fields are missing
        """
        cursor = self._get_cursor(db)
        connection = self._get_connection(db)
        self._validate_required_fields()

        if self.id:
            # Update existing user
            query = SQL("""
                UPDATE users 
                SET email = %s, 
                    password_hash = %s, 
                    email_verified = %s,
                    last_login = %s, 
                    failed_login_attempts = %s, 
                    locked_until = %s
                WHERE id = %s
                RETURNING *
            """)
            # After _validate_required_fields(), we know email and password_hash are not None
            update_params: tuple[str, str, bool, Optional[datetime], int, Optional[datetime], UUID] = (
                str(self.email),
                str(self.password_hash),  # explicitly cast to str since we validated it's not None
                self.email_verified,
                self.last_login,
                self.failed_login_attempts,
                self.locked_until,
                self.id
            )
            await cursor.execute(query, update_params)
        else:
            # Insert new user
            query = SQL("""
                INSERT INTO users (
                    email, 
                    password_hash, 
                    email_verified
                ) VALUES (%s, %s, %s)
                RETURNING *
            """)
            insert_params = (
                str(self.email),
                str(self.password_hash),  # explicitly cast to str since we validated it's not None
                self.email_verified
            )
            await cursor.execute(query, insert_params)

        result = await cursor.fetchone()
        await connection.commit()
        
        if result is not None:
            updated_data = self._row_to_dict(result, cursor)
            for key, value in updated_data.items():
                setattr(self, key, value)

    async def delete(self, db: Database) -> None:
        """
        Delete the user from the database.

        Args:
            db: Database connection instance

        Raises:
            ValueError: If database cursor is not initialized or user has no ID
        """
        cursor = self._get_cursor(db)
        connection = self._get_connection(db)

        if self.id:
            delete_query = SQL("DELETE FROM users WHERE id = %s")
            await cursor.execute(delete_query, (self.id,))
            await connection.commit()
            self.id = None
        else:
            raise ValueError("User must have an ID to delete")

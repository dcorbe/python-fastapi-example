"""User management module for the BSS library.

This module provides the User model and related database operations. It handles user
creation, retrieval, and updates while managing attributes like email, password hashes,
and account status.
"""
from datetime import datetime
from uuid import UUID
from pydantic import EmailStr, Field
from database.model import DatabaseModel
from database import Database
from psycopg.sql import SQL, Identifier

class User(DatabaseModel):
    """
    User model representing entries in the users table.
    Maps to the PostgreSQL users table schema.
    """
    table_name = "users"  # Class-level configuration for DatabaseModel

    # Model fields
    id: UUID | None = None
    email: EmailStr | None = None
    password_hash: str | None = None
    email_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: datetime | None = None
    failed_login_attempts: int = Field(default=0)
    locked_until: datetime | None = None

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

    def set_password(self, password: str) -> None:
        """
        Set a new password for the user.
        
        This method will be used in conjunction with the password hashing utility
        in the backend. The actual hashing is done in the backend to keep the
        hashing implementation details separate from the model.
        
        Args:
            password: The plain text password to set
            
        Note:
            This method only sets the hash - you must call save() to persist changes.
        """
        if not password:
            raise ValueError("Password cannot be empty")
        self.password_hash = password  # Will be hashed by backend before setting

    @classmethod
    async def get_by_email(cls, email: str, db: Database) -> 'User | None':
        """
        Retrieve a user by email address.

        Args:
            email: The email address to look up
            db: Database connection instance

        Returns:
            User instance if found, None otherwise
        """
        return await cls._fetch_by_field(db, "email", email, case_insensitive=True)

    @classmethod
    async def get_by_uuid(cls, uuid: UUID, db: Database) -> 'User | None':
        """
        Retrieve a user by UUID.

        Args:
            uuid: The UUID to look up
            db: Database connection instance

        Returns:
            User instance if found, None otherwise
        """
        return await cls._fetch_by_field(db, "id", uuid)

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
                UPDATE {}
                SET email = %s, 
                    password_hash = %s, 
                    email_verified = %s,
                    last_login = %s, 
                    failed_login_attempts = %s, 
                    locked_until = %s
                WHERE id = %s
                RETURNING *
            """).format(Identifier(self.table_name))
            
            # After _validate_required_fields(), we know email and password_hash are not None
            update_params: tuple[str, str, bool, datetime | None, int, datetime | None, UUID] = (
                str(self.email),
                str(self.password_hash),
                self.email_verified,
                self.last_login,
                self.failed_login_attempts,
                self.locked_until,
                self.id
            )
            result = await self._execute_query(db, query, update_params)
        else:
            # Insert new user
            query = SQL("""
                INSERT INTO {} (
                    email, 
                    password_hash, 
                    email_verified
                ) VALUES (%s, %s, %s)
                RETURNING *
            """).format(Identifier(self.table_name))
            
            insert_params = (
                str(self.email),
                str(self.password_hash),
                self.email_verified
            )
            result = await self._execute_query(db, query, insert_params)

        await connection.commit()
        
        if result is not None:
            for key, value in result.items():
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
            delete_query = SQL("DELETE FROM {} WHERE id = %s").format(
                Identifier(self.table_name)
            )
            await cursor.execute(delete_query, (self.id,))
            await connection.commit()
            self.id = None
        else:
            raise ValueError("User must have an ID to delete")

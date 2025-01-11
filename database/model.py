"""Base database model functionality.

This module provides the base class for database models, implementing common
database operations and utility functions used across different model types.
"""
from typing import Any, TypeVar, Optional, Sequence, ClassVar
from pydantic import BaseModel
from psycopg.sql import SQL, Identifier, Composed
from psycopg import AsyncCursor, AsyncConnection
from . import Database

T = TypeVar('T', bound='DatabaseModel')

class DatabaseModel(BaseModel):
    """
    Base class for database models providing common database operations.
    """
    # Class-level configuration
    table_name: ClassVar[str]  # Must be defined by subclasses
    
    @classmethod
    def _get_cursor(cls, db: Database) -> AsyncCursor[Any]:
        """Get and validate database cursor."""
        if db.cur is None:
            raise ValueError("Database cursor not initialized")
        return db.cur

    @classmethod
    def _get_connection(cls, db: Database) -> AsyncConnection[Any]:
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

    def _validate_required_fields(self) -> None:
        """
        Validate that required fields are set.
        Should be implemented by subclasses to define their required fields.
        """
        raise NotImplementedError("Subclasses must implement _validate_required_fields")

    @classmethod
    async def _execute_query(
        cls,
        db: Database,
        query: SQL | Composed,  # Updated type to allow Composed SQL
        params: tuple[Any, ...],
        fetch_one: bool = True
    ) -> Optional[dict[str, Any]]:
        """Execute a query and optionally return the first result as a dictionary."""
        cursor = cls._get_cursor(db)
        await cursor.execute(query, params)
        
        if fetch_one:
            row = await cursor.fetchone()
            if row is None:
                return None
            return cls._row_to_dict(row, cursor)
        return None

    @classmethod
    async def _fetch_by_field(
        cls: type[T],
        db: Database,
        field: str,
        value: Any,
        case_insensitive: bool = False
    ) -> Optional[T]:
        """Generic method to fetch a record by a specific field."""
        cursor = cls._get_cursor(db)
        
        if case_insensitive and isinstance(value, str):
            query = SQL("SELECT * FROM {} WHERE LOWER({}) = LOWER(%s)").format(
                Identifier(cls.table_name),
                Identifier(field)
            )
        else:
            query = SQL("SELECT * FROM {} WHERE {} = %s").format(
                Identifier(cls.table_name),
                Identifier(field)
            )
            
        result = await cls._execute_query(db, query, (value,))
        if result is None:
            return None
            
        return cls.model_validate(result)

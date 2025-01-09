"""This module manages database connectivity and operations."""
import psycopg
import os
from typing import Self, Type, Optional, Any

class Database:
    """
    Initializes the Database class by establishing an asynchronous connection to the PostgreSQL database
    using the `DATABASE_URL` environment variable for the connection parameters. It also creates an asynchronous cursor
    for executing database operations.

    Environment Variables:
    - DATABASE_URL: The URL of the PostgreSQL database.

    Raises:
    - ValueError: If the `DATABASE_URL` environment variable is not set.
    - psycopg.OperationalError: If there is an issue connecting to the database.
    """
    conn: psycopg.AsyncConnection[Any] | None = None
    cur: psycopg.AsyncCursor[Any] | None = None

    def __init__(self) -> None:
        self.conn = None
        self.cur = None

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[object]
    ) -> None:
        await self.close()

    @classmethod
    async def connect(cls) -> Self:
        """
        Connects to the PostgreSQL database using the provided URL and initializes the cursor.

        This method establishes an asynchronous connection to the PostgreSQL database using the
        `DATABASE_URL` environment variable. It also initializes an asynchronous cursor for
        executing database operations.

        Raises:
        - ValueError: If the `DATABASE_URL` environment variable is not set.
        - psycopg.OperationalError: If there is an issue connecting to the database.
        """
        self = cls()
        url = os.getenv("DATABASE_URL")
        if url is None:
            raise ValueError("DATABASE_URL environment variable must be set")

        self.conn = await psycopg.AsyncConnection.connect(url)
        self.cur = self.conn.cursor()
        return self


    async def close(self) -> None:
        """
        Closes the database connection and cursor.

        This method ensures that both the asynchronous cursor and connection to the PostgreSQL database
        are properly closed. It checks if the cursor and connection are initialized and closes them if they are.

        Raises:
        - psycopg.OperationalError: If there is an issue closing the database connection or cursor.
        """
        if hasattr(self, "cur") and self.cur is not None:
            await self.cur.close()
        if hasattr(self, "conn") and self.conn is not None:
            await self.conn.close()



"""Test script for database functionality."""
import asyncio
import os
from datetime import datetime, UTC
from typing import Any

from database import Database
from database.models import User
from sqlalchemy import text

async def test_connection() -> bool:
    """Test basic database connectivity."""
    try:
        Database.init()
        async with Database.session() as session:
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()  # scalar() is not async
            print(f"Database connection test: {'SUCCESS' if value == 1 else 'FAILED'}")
            return True
    except Exception as e:
        print(f"Connection test failed: {str(e)}")
        return False

async def test_database() -> None:
    """Test database operations."""
    # Print current DATABASE_URL (with password masked)
    db_url = os.getenv("DATABASE_URL", "")
    if "://" in db_url:
        # Mask password in URL for safe printing
        parts = db_url.split("@")
        if len(parts) > 1:
            auth = parts[0].split(":")
            if len(auth) > 1:
                masked_url = f"{auth[0]}:****@{parts[1]}"
                print(f"Using database URL: {masked_url}")
    
    # First test connection
    if not await test_connection():
        return
    
    try:
        async with Database.session() as session:
            # Create a test user
            test_user = User(
                email="test@example.com",
                password_hash="hashed_password_123",
                email_verified=False
            )
            
            session.add(test_user)
            await session.commit()
            
            print(f"Created user with ID: {test_user.id}")
            
            # Fetch user by email
            stmt = text("SELECT * FROM users WHERE email = :email")
            result = await session.execute(stmt, {"email": "test@example.com"})
            user_record = result.one_or_none()
            
            if user_record:
                print(f"Found user: {user_record.email}")
                print(f"Created at: {user_record.created_at}")
            else:
                print("User not found")
            
            # Clean up - delete test user
            await session.delete(test_user)
            await session.commit()
            print("Test user deleted")
            
    except Exception as e:
        print(f"Error during database operations: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        raise
    finally:
        await Database.close()

if __name__ == "__main__":
    # Run the test
    try:
        asyncio.run(test_database())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")

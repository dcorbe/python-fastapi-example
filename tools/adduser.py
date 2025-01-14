"""Add a user to the database."""
import asyncio
from database import Database
from database.models import User
from auth.service import AuthService, AuthConfig

async def create_user(email: str, password: str) -> None:
    # Initialize auth service
    auth_config = AuthConfig(
        jwt_secret_key="bloobityblabbitybloo!",  # This isn't used for user creation but has to be set to something
        jwt_algorithm="HS256",
        access_token_expire_minutes=30,
        max_login_attempts=5,
        lockout_minutes=15
    )
    auth_service = AuthService(auth_config)
    
    # Hash the password
    password_hash = auth_service.hash_password(password)
    
    # Create user
    user = User(
        email=email,
        password_hash=password_hash,
        email_verified=False
    )
    
    async with Database.session() as session:
        session.add(user)
        await session.commit()
        print(f"Created user: {user.email}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <email> <password>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    asyncio.run(create_user(email, password))

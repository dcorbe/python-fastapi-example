"""Password hashing and verification utilities."""
from typing import Any
from passlib.context import CryptContext

# Create password context with bcrypt scheme
pwd_context: CryptContext = CryptContext(
    schemes=["bcrypt"],
    default="bcrypt",
    bcrypt__default_rounds=12  # Recommended rounds for bcrypt
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string
    """
    result: str = pwd_context.hash(password)
    return result


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hash to verify against

    Returns:
        True if password matches hash, False otherwise
    """
    result: bool = pwd_context.verify(plain_password, hashed_password)
    return result
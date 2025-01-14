"""SQLAlchemy model mixins and utilities."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import DeclarativeBase


class SQLModelBase(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


class PydanticBase(BaseModel):
    """Base Pydantic model with SQLAlchemy config."""
    
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True
    )


class TimestampMixin:
    """Mixin to add created_at and updated_at columns."""
    
    created_at: datetime
    updated_at: Optional[datetime] = None


class UUIDMixin:
    """Mixin to add UUID primary key."""
    
    id: UUID


def to_dict(instance: Any) -> Dict[str, Any]:
    """Convert SQLAlchemy model instance to dictionary."""
    return {
        column.name: getattr(instance, column.name)
        for column in instance.__table__.columns
    }

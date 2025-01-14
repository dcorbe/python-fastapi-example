"""Book model for example purposes."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class Book(Base):
    """Book database model."""
    __tablename__ = "books"

    title: Mapped[str] = mapped_column(String(100))
    author: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default="CURRENT_TIMESTAMP")
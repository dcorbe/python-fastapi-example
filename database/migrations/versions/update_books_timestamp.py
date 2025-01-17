"""Update books created_at to include timezone

Revision ID: 2024_01_16_1
Revises: 864e61d97e73
Create Date: 2025-01-16 18:14:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2024_01_16_1"
down_revision: str = "864e61d97e73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database to include timezone in books created_at."""
    # Step 1: Drop the existing default
    op.alter_column(
        "books",
        "created_at",
        server_default=None,
        existing_type=sa.DateTime(),
        existing_nullable=False,
    )

    # Step 2: Convert to timestamptz
    op.execute(
        "ALTER TABLE books ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC'"
    )

    # Step 3: Add back the default with timezone
    op.alter_column(
        "books",
        "created_at",
        server_default=sa.text("CURRENT_TIMESTAMP"),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade database to remove timezone from books created_at."""
    # Step 1: Drop the existing default
    op.alter_column(
        "books",
        "created_at",
        server_default=None,
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )

    # Step 2: Convert back to timestamp
    op.execute(
        "ALTER TABLE books ALTER COLUMN created_at TYPE timestamp USING created_at AT TIME ZONE 'UTC'"
    )

    # Step 3: Add back the original default
    op.alter_column(
        "books",
        "created_at",
        server_default=sa.text("CURRENT_TIMESTAMP"),
        existing_type=sa.DateTime(),
        existing_nullable=False,
    )

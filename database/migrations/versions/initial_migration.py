"""initial migration

Revision ID: initial_migration
Revises: 
Create Date: 2024-01-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'initial_migration'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This is a stamp migration - the schema already exists
    pass


def downgrade() -> None:
    # We don't want to drop anything in the downgrade since this is just a stamp
    pass

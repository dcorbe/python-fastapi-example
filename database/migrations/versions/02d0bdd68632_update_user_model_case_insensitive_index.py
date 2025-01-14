"""update user model case insensitive index

Revision ID: 02d0bdd68632
Revises: initial_migration
Create Date: 2025-01-14 06:19:40.833711

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '02d0bdd68632'
down_revision: Union[str, None] = 'initial_migration'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Clean up old sqlx migrations table
    op.drop_table('_sqlx_migrations')
    
    # Update email indices
    op.drop_index('idx_users_email', table_name='users')
    op.drop_constraint('users_email_key', 'users', type_='unique')
    op.create_index('ix_users_email_lower', 'users', [sa.text('lower(email)')], unique=True)


def downgrade() -> None:
    # Restore original email indices
    op.drop_index('ix_users_email_lower', table_name='users')
    op.create_unique_constraint('users_email_key', 'users', ['email'])
    op.create_index('idx_users_email', 'users', ['email'], unique=False)
    
    # Recreate sqlx migrations table
    op.create_table('_sqlx_migrations',
        sa.Column('version', sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column('description', sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column('installed_on', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
        sa.Column('success', sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column('checksum', postgresql.BYTEA(), autoincrement=False, nullable=False),
        sa.Column('execution_time', sa.BIGINT(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint('version', name='_sqlx_migrations_pkey')
    )
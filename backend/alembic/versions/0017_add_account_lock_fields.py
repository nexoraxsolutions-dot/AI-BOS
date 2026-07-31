"""Add account lock fields to users table

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = '0017'
down_revision: Union[str, None] = '0016'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add account lock fields to users table
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('lock_reason', sa.String(), nullable=True))
    
    # Create index on locked_until for efficient queries
    op.create_index('ix_users_locked_until', 'users', ['locked_until'])


def downgrade() -> None:
    # Remove index
    op.drop_index('ix_users_locked_until', table_name='users')
    
    # Remove columns
    op.drop_column('users', 'lock_reason')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
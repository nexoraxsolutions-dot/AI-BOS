"""Create password history table

Revision ID: 0020
Revises: 0019
Create Date: 2026-07-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0020'
down_revision: Union[str, None] = '0019'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create password_history table
    op.create_table(
        'password_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_password_history_id'), 'password_history', ['id'], unique=False)
    op.create_index(op.f('ix_password_history_user_id'), 'password_history', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop password_history table
    op.drop_index(op.f('ix_password_history_user_id'), table_name='password_history')
    op.drop_index(op.f('ix_password_history_id'), table_name='password_history')
    op.drop_table('password_history')
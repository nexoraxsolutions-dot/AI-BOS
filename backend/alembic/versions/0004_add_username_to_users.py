"""add username field to users

Revision ID: 0004_add_username_to_users
Revises: 0003_create_environment_variables
Create Date: 2026-07-22 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0004_add_username_to_users'
down_revision = '0003_create_environment_variables'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column('username', sa.String(length=50), nullable=True),
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_column('users', 'username')
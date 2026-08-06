"""add created_at and updated_at columns to users and companies

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-22 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    now = datetime.utcnow()

    # Add timestamps to companies
    op.add_column(
        'companies',
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.add_column(
        'companies',
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    # Add timestamps to users
    op.add_column(
        'users',
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.add_column(
        'users',
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )


def downgrade():
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'created_at')
    op.drop_column('companies', 'updated_at')
    op.drop_column('companies', 'created_at')
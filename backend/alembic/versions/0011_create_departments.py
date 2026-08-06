"""create_departments

Revision ID: 0011
Revises: 0010
Create Date: 2025-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text

# revision identifiers, used by Alembic.
revision: str = '0011'
down_revision: Union[str, None] = '0010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create departments table
    op.create_table(
        'departments',
        Column('id', Integer, primary_key=True, index=True),
        Column('name', String(100), nullable=False, index=True),
        Column('description', Text, nullable=True),
        Column('company_id', Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True),
        Column('manager_id', Integer, ForeignKey('users.id'), nullable=True),
        Column('budget', String(50), nullable=True),
        Column('location', String(255), nullable=True),
        Column('is_active', Boolean, default=True),
        Column('created_at', DateTime, default=sa.func.now()),
        Column('updated_at', DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    # Drop departments table
    op.drop_table('departments')
"""Add enhanced company fields

Revision ID: 0005
Revises: 0004_add_username_to_users
Create Date: 2026-07-23 19:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '0005'
down_revision: Union[str, None] = '0004_add_username_to_users'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('companies', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('companies', sa.Column('address', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('phone', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('email', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('website', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('logo_url', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('tax_id', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('industry', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('employee_count', sa.Integer(), nullable=True))
    op.add_column('companies', sa.Column('subscription_plan', sa.String(), server_default='free', nullable=True))
    op.add_column('companies', sa.Column('subscription_status', sa.String(), server_default='active', nullable=True))
    op.add_column('companies', sa.Column('subscription_expires_at', sa.DateTime(), nullable=True))
    op.add_column('companies', sa.Column('settings', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('companies', 'settings')
    op.drop_column('companies', 'subscription_expires_at')
    op.drop_column('companies', 'subscription_status')
    op.drop_column('companies', 'subscription_plan')
    op.drop_column('companies', 'employee_count')
    op.drop_column('companies', 'industry')
    op.drop_column('companies', 'tax_id')
    op.drop_column('companies', 'logo_url')
    op.drop_column('companies', 'website')
    op.drop_column('companies', 'email')
    op.drop_column('companies', 'phone')
    op.drop_column('companies', 'address')
    op.drop_column('companies', 'description')
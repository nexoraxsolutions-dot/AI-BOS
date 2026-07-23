"""create users and companies tables

Revision ID: 0001_create_users_companies
Revises: 
Create Date: 2026-07-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_create_users_companies'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('domain', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=True),
    )


def downgrade():
    op.drop_table('users')
    op.drop_table('companies')

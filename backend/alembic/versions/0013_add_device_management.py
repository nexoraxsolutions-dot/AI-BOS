"""Add device management fields to tokens table

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-29
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tokens", sa.Column("device_name", sa.String(255), nullable=True))
    op.add_column("tokens", sa.Column("device_type", sa.String(50), nullable=True))
    op.add_column("tokens", sa.Column("last_used_at", sa.DateTime(), nullable=True))
    op.add_column("tokens", sa.Column("is_current", sa.Boolean(), server_default=sa.text("false"), nullable=False))


def downgrade() -> None:
    op.drop_column("tokens", "is_current")
    op.drop_column("tokens", "last_used_at")
    op.drop_column("tokens", "device_type")
    op.drop_column("tokens", "device_name")

"""Add two-factor authentication support

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-29

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 2FA columns to users table
    op.add_column("users", sa.Column("is_2fa_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("users", sa.Column("otp_secret", sa.String(), nullable=True))

    # Create backup codes table
    op.create_table(
        "two_factor_backup_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("code_hash", sa.String(), nullable=False),
        sa.Column("is_used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_two_factor_backup_codes_id"), "two_factor_backup_codes", ["id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_two_factor_backup_codes_id"), table_name="two_factor_backup_codes")
    op.drop_table("two_factor_backup_codes")
    op.drop_column("users", "otp_secret")
    op.drop_column("users", "is_2fa_enabled")
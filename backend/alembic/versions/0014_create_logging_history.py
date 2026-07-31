"""Create log_entries table for logging history

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "log_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("logger_name", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("module", sa.String(length=255), nullable=True),
        sa.Column("func_name", sa.String(length=255), nullable=True),
        sa.Column("line_no", sa.Integer(), nullable=True),
        sa.Column("pathname", sa.String(length=500), nullable=True),
        sa.Column("thread_name", sa.String(length=255), nullable=True),
        sa.Column("process", sa.String(length=50), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_log_entries_id"), "log_entries", ["id"], unique=False)
    op.create_index(op.f("ix_log_entries_level"), "log_entries", ["level"], unique=False)
    op.create_index(op.f("ix_log_entries_logger_name"), "log_entries", ["logger_name"], unique=False)
    op.create_index(op.f("ix_log_entries_timestamp"), "log_entries", ["timestamp"], unique=False)
    op.create_index(op.f("ix_log_entries_user_id"), "log_entries", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_log_entries_user_id"), table_name="log_entries")
    op.drop_index(op.f("ix_log_entries_timestamp"), table_name="log_entries")
    op.drop_index(op.f("ix_log_entries_logger_name"), table_name="log_entries")
    op.drop_index(op.f("ix_log_entries_level"), table_name="log_entries")
    op.drop_index(op.f("ix_log_entries_id"), table_name="log_entries")
    op.drop_table("log_entries")

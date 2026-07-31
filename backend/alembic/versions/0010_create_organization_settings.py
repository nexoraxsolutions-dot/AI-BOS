"""Create organization_settings table

Revision ID: 0010
Revises: 0009_create_password_reset_tokens
Create Date: 2026-07-29 11:14:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0010'
down_revision: Union[str, None] = '0009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create organization_settings table
    op.create_table(
        'organization_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('timezone', sa.String(), server_default='UTC', nullable=True),
        sa.Column('date_format', sa.String(), server_default='YYYY-MM-DD', nullable=True),
        sa.Column('time_format', sa.String(), server_default='24h', nullable=True),
        sa.Column('language', sa.String(), server_default='en', nullable=True),
        sa.Column('currency', sa.String(), server_default='USD', nullable=True),
        sa.Column('password_min_length', sa.Integer(), server_default='8', nullable=True),
        sa.Column('password_require_uppercase', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('password_require_lowercase', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('password_require_numbers', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('password_require_special_chars', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('password_expiry_days', sa.Integer(), server_default='90', nullable=True),
        sa.Column('session_timeout_minutes', sa.Integer(), server_default='60', nullable=True),
        sa.Column('enforce_2fa', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('max_login_attempts', sa.Integer(), server_default='5', nullable=True),
        sa.Column('email_notifications_enabled', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('notify_on_user_creation', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('notify_on_user_deletion', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('notify_on_password_reset', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('notify_on_security_alerts', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('notify_on_subscription_changes', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('primary_color', sa.String(), server_default='#06b6d4', nullable=True),
        sa.Column('logo_url', sa.String(), nullable=True),
        sa.Column('custom_css', sa.Text(), nullable=True),
        sa.Column('enable_user_registration', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('enable_api_access', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('enable_audit_logs', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('enable_data_export', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('custom_settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_settings_id'), 'organization_settings', ['id'], unique=False)
    op.create_index(op.f('ix_organization_settings_company_id'), 'organization_settings', ['company_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_organization_settings_company_id'), table_name='organization_settings')
    op.drop_index(op.f('ix_organization_settings_id'), table_name='organization_settings')
    op.drop_table('organization_settings')
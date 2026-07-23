"""Add company_id to environment_variables

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    # Add company_id column
    op.add_column(
        'environment_variables',
        sa.Column('company_id', sa.Integer(), nullable=True),
    )
    
    # Create index on company_id
    op.create_index(
        'ix_environment_variables_company_id',
        'environment_variables',
        ['company_id'],
    )
    
    # Drop the unique constraint on key (now key is unique per company, not globally)
    op.drop_index('ix_environment_variables_key', table_name='environment_variables')
    op.create_index(
        'ix_environment_variables_key',
        'environment_variables',
        ['key'],
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_environment_variables_company_id',
        'environment_variables',
        'companies',
        ['company_id'],
        ['id'],
    )


def downgrade():
    # Drop foreign key
    op.drop_constraint(
        'fk_environment_variables_company_id',
        'environment_variables',
        type_='foreignkey',
    )
    
    # Drop index on key and recreate unique
    op.drop_index('ix_environment_variables_key', table_name='environment_variables')
    op.create_index(
        'ix_environment_variables_key',
        'environment_variables',
        ['key'],
        unique=True,
    )
    
    # Drop company_id index and column
    op.drop_index('ix_environment_variables_company_id', table_name='environment_variables')
    op.drop_column('environment_variables', 'company_id')
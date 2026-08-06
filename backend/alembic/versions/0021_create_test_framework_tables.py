"""create_test_framework_tables

revision = '0021'
down_revision = '0020'
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0021'
down_revision = '0020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create test_suites table
    op.create_table(
        'test_suites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_automated', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_test_suites_name', 'test_suites', ['name'], unique=False)
    op.create_index('ix_test_suites_company_id', 'test_suites', ['company_id'], unique=False)
    op.create_index('ix_test_suites_created_by_id', 'test_suites', ['created_by_id'], unique=False)
    op.create_index('ix_test_suites_is_active', 'test_suites', ['is_active'], unique=False)
    op.create_index('ix_test_suites_is_automated', 'test_suites', ['is_automated'], unique=False)

    # Create test_cases table
    op.create_table(
        'test_cases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_suite_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='test_priority'), server_default='MEDIUM', nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'PASSED', 'FAILED', 'SKIPPED', 'ERROR', name='test_status'), server_default='PENDING', nullable=False),
        sa.Column('order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('test_type', sa.String(50), nullable=False),
        sa.Column('endpoint', sa.String(500), nullable=True),
        sa.Column('method', sa.String(10), nullable=True),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.Column('expected_status', sa.Integer(), nullable=True),
        sa.Column('expected_response', sa.Text(), nullable=True),
        sa.Column('tags', sa.String(500), nullable=True),
        sa.Column('timeout', sa.Integer(), server_default='30', nullable=False),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('last_run_status', sa.Enum('PENDING', 'RUNNING', 'PASSED', 'FAILED', 'SKIPPED', 'ERROR', name='test_status'), nullable=True),
        sa.Column('last_run_duration', sa.Float(), nullable=True),
        sa.Column('success_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('failure_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['test_suite_id'], ['test_suites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_test_cases_name', 'test_cases', ['name'], unique=False)
    op.create_index('ix_test_cases_test_suite_id', 'test_cases', ['test_suite_id'], unique=False)
    op.create_index('ix_test_cases_priority', 'test_cases', ['priority'], unique=False)
    op.create_index('ix_test_cases_status', 'test_cases', ['status'], unique=False)
    op.create_index('ix_test_cases_test_type', 'test_cases', ['test_type'], unique=False)
    op.create_index('ix_test_cases_is_active', 'test_cases', ['is_active'], unique=False)

    # Create test_runs table
    op.create_table(
        'test_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_suite_id', sa.Integer(), nullable=False),
        sa.Column('triggered_by_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'PASSED', 'FAILED', 'SKIPPED', 'ERROR', name='test_status'), server_default='RUNNING', nullable=False),
        sa.Column('started_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('total_tests', sa.Integer(), server_default='0', nullable=False),
        sa.Column('passed_tests', sa.Integer(), server_default='0', nullable=False),
        sa.Column('failed_tests', sa.Integer(), server_default='0', nullable=False),
        sa.Column('skipped_tests', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_tests', sa.Integer(), server_default='0', nullable=False),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('environment', sa.String(50), server_default='development', nullable=False),
        sa.Column('branch', sa.String(255), nullable=True),
        sa.Column('commit_hash', sa.String(255), nullable=True),
        sa.Column('triggered_by', sa.String(50), server_default='manual', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_traceback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['test_suite_id'], ['test_suites.id'], ),
        sa.ForeignKeyConstraint(['triggered_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_test_runs_test_suite_id', 'test_runs', ['test_suite_id'], unique=False)
    op.create_index('ix_test_runs_triggered_by_id', 'test_runs', ['triggered_by_id'], unique=False)
    op.create_index('ix_test_runs_status', 'test_runs', ['status'], unique=False)
    op.create_index('ix_test_runs_started_at', 'test_runs', ['started_at'], unique=False)
    op.create_index('ix_test_runs_environment', 'test_runs', ['environment'], unique=False)

    # Create test_results table
    op.create_table(
        'test_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_run_id', sa.Integer(), nullable=False),
        sa.Column('test_case_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'PASSED', 'FAILED', 'SKIPPED', 'ERROR', name='test_status'), nullable=False),
        sa.Column('started_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('output', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_traceback', sa.Text(), nullable=True),
        sa.Column('request_url', sa.String(500), nullable=True),
        sa.Column('request_method', sa.String(10), nullable=True),
        sa.Column('request_headers', sa.Text(), nullable=True),
        sa.Column('request_body', sa.Text(), nullable=True),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('response_headers', sa.Text(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('retry_attempt', sa.Integer(), server_default='0', nullable=False),
        sa.Column('environment', sa.String(50), server_default='development', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['test_run_id'], ['test_runs.id'], ),
        sa.ForeignKeyConstraint(['test_case_id'], ['test_cases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_test_results_test_run_id', 'test_results', ['test_run_id'], unique=False)
    op.create_index('ix_test_results_test_case_id', 'test_results', ['test_case_id'], unique=False)
    op.create_index('ix_test_results_status', 'test_results', ['status'], unique=False)
    op.create_index('ix_results_created_at', 'test_results', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_results_created_at', table_name='test_results')
    op.drop_index('ix_test_results_status', table_name='test_results')
    op.drop_index('ix_test_results_test_case_id', table_name='test_results')
    op.drop_index('ix_test_results_test_run_id', table_name='test_results')
    op.drop_table('test_results')

    op.drop_index('ix_test_runs_environment', table_name='test_runs')
    op.drop_index('ix_test_runs_started_at', table_name='test_runs')
    op.drop_index('ix_test_runs_status', table_name='test_runs')
    op.drop_index('ix_test_runs_triggered_by_id', table_name='test_runs')
    op.drop_index('ix_test_runs_test_suite_id', table_name='test_runs')
    op.drop_table('test_runs')

    op.drop_index('ix_test_cases_is_active', table_name='test_cases')
    op.drop_index('ix_test_cases_test_type', table_name='test_cases')
    op.drop_index('ix_test_cases_status', table_name='test_cases')
    op.drop_index('ix_test_cases_priority', table_name='test_cases')
    op.drop_index('ix_test_cases_test_suite_id', table_name='test_cases')
    op.drop_index('ix_test_cases_name', table_name='test_cases')
    op.drop_table('test_cases')

    op.drop_index('ix_test_suites_is_automated', table_name='test_suites')
    op.drop_index('ix_test_suites_is_active', table_name='test_suites')
    op.drop_index('ix_test_suites_created_by_id', table_name='test_suites')
    op.drop_index('ix_test_suites_company_id', table_name='test_suites')
    op.drop_index('ix_test_suites_name', table_name='test_suites')
    op.drop_table('test_suites')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS test_status')
    op.execute('DROP TYPE IF EXISTS test_priority')
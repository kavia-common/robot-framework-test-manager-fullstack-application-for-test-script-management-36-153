"""Remove authentication tables and user foreign keys

Revision ID: 002_remove_auth_tables
Revises: 001_initial_schema
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_remove_auth_tables'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Remove authentication-related tables and make user foreign keys nullable."""
    
    # Drop foreign key constraints from tables that reference users
    op.drop_constraint('test_scripts_created_by_fkey', 'test_scripts', type_='foreignkey')
    op.drop_constraint('test_cases_created_by_fkey', 'test_cases', type_='foreignkey')
    op.drop_constraint('run_history_executed_by_fkey', 'run_history', type_='foreignkey')
    op.drop_constraint('audit_logs_user_id_fkey', 'audit_logs', type_='foreignkey')
    
    # Alter columns to be nullable
    op.alter_column('test_scripts', 'created_by',
                    existing_type=sa.String(),
                    nullable=True)
    
    op.alter_column('test_cases', 'created_by',
                    existing_type=sa.String(),
                    nullable=True)
    
    op.alter_column('run_history', 'executed_by',
                    existing_type=sa.String(),
                    nullable=True)
    
    op.alter_column('audit_logs', 'user_id',
                    existing_type=sa.String(),
                    nullable=True)
    
    # Drop authentication tables
    op.drop_table('user_roles')
    op.drop_table('roles')
    op.drop_table('users')


def downgrade():
    """Restore authentication tables and user foreign keys."""
    
    # Recreate users table
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Recreate roles table
    op.create_table('roles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.Enum('ADMIN', 'TESTER', 'VIEWER', name='userroleenum'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Recreate user_roles table
    op.create_table('user_roles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('role_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Restore foreign key constraints
    op.alter_column('test_scripts', 'created_by',
                    existing_type=sa.String(),
                    nullable=False)
    op.create_foreign_key('test_scripts_created_by_fkey', 'test_scripts', 'users', ['created_by'], ['id'])
    
    op.alter_column('test_cases', 'created_by',
                    existing_type=sa.String(),
                    nullable=False)
    op.create_foreign_key('test_cases_created_by_fkey', 'test_cases', 'users', ['created_by'], ['id'])
    
    op.alter_column('run_history', 'executed_by',
                    existing_type=sa.String(),
                    nullable=False)
    op.create_foreign_key('run_history_executed_by_fkey', 'run_history', 'users', ['executed_by'], ['id'])
    
    op.create_foreign_key('audit_logs_user_id_fkey', 'audit_logs', 'users', ['user_id'], ['id'])

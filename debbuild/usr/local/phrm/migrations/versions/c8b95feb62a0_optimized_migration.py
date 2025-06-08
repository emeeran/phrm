"""Optimized migration with unnecessary drops removed

Revision ID: c8b95feb62a0_optimized
Revises: c8b95feb62a0
Create Date: 2025-06-04 16:45:22.123456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8b95feb62a0_optimized'
down_revision = 'c8b95feb62a0'
branch_labels = None
depends_on = None


def upgrade():
    # Only keep the essential operations for the current schema
    # We removed all the unnecessary drop operations for tables that don't exist anymore
    
    # Add user reset password fields
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reset_password_token', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('reset_password_expires', sa.DateTime(), nullable=True))
        batch_op.create_index(batch_op.f('ix_user_reset_password_token'), ['reset_password_token'], unique=True)
    
    # Add last login tracking
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_login', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('login_count', sa.Integer(), nullable=True, default=0))
    
    # Add user preferences column
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('preferences', sa.JSON(), nullable=True))


def downgrade():
    # Remove the fields added in upgrade
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('preferences')
        batch_op.drop_column('login_count')
        batch_op.drop_column('last_login')
        batch_op.drop_index(batch_op.f('ix_user_reset_password_token'))
        batch_op.drop_column('reset_password_expires')
        batch_op.drop_column('reset_password_token')

"""Database optimization with additional indexes

Revision ID: db_optimization_001
Revises: c8b95feb62a0_optimized
Create Date: 2024-12-04 20:30:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'db_optimization_001'
down_revision = 'c8b95feb62a0_optimized'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add performance-optimized indexes"""

    # User table optimizations
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Composite index for login tracking
        batch_op.create_index('idx_users_last_login_active', ['last_login', 'is_active'], unique=False)
        # Performance index for admin checks
        batch_op.create_index('idx_users_admin_active', ['is_admin', 'is_active'], unique=False)

    # Health records optimizations
    with op.batch_alter_table('health_records', schema=None) as batch_op:
        # Composite indexes for common queries
        batch_op.create_index('idx_health_records_user_date', ['user_id', 'date'], unique=False)
        batch_op.create_index('idx_health_records_family_date', ['family_member_id', 'date'], unique=False)
        batch_op.create_index('idx_health_records_type_date', ['record_type', 'date'], unique=False)
        # Text search optimization
        batch_op.create_index('idx_health_records_title', ['title'], unique=False)

    # Family members optimizations
    with op.batch_alter_table('family_members', schema=None) as batch_op:
        # Name search optimization
        batch_op.create_index('idx_family_members_name', ['first_name', 'last_name'], unique=False)
        # Relationship filtering
        batch_op.create_index('idx_family_members_relationship', ['relationship'], unique=False)

    # Documents optimizations
    with op.batch_alter_table('documents', schema=None) as batch_op:
        # File type filtering
        batch_op.create_index('idx_documents_file_type', ['file_type'], unique=False)
        # Size optimization for queries
        batch_op.create_index('idx_documents_size', ['file_size'], unique=False)

    # AI summaries optimizations
    with op.batch_alter_table('ai_summaries', schema=None) as batch_op:
        # Type filtering
        batch_op.create_index('idx_ai_summaries_type', ['summary_type'], unique=False)
        # Date-based queries
        batch_op.create_index('idx_ai_summaries_created', ['created_at'], unique=False)

def downgrade() -> None:
    """Remove performance indexes"""

    # Remove AI summaries indexes
    with op.batch_alter_table('ai_summaries', schema=None) as batch_op:
        batch_op.drop_index('idx_ai_summaries_type')
        batch_op.drop_index('idx_ai_summaries_created')

    # Remove documents indexes
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.drop_index('idx_documents_file_type')
        batch_op.drop_index('idx_documents_size')

    # Remove family members indexes
    with op.batch_alter_table('family_members', schema=None) as batch_op:
        batch_op.drop_index('idx_family_members_name')
        batch_op.drop_index('idx_family_members_relationship')

    # Remove health records indexes
    with op.batch_alter_table('health_records', schema=None) as batch_op:
        batch_op.drop_index('idx_health_records_user_date')
        batch_op.drop_index('idx_health_records_family_date')
        batch_op.drop_index('idx_health_records_type_date')
        batch_op.drop_index('idx_health_records_title')

    # Remove user indexes
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('idx_users_last_login_active')
        batch_op.drop_index('idx_users_admin_active')

"""Add current medications table for family members

Revision ID: a89f60fbac28
Revises: b824cd4a4c1d
Create Date: 2025-06-15 14:50:40.938933

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a89f60fbac28"
down_revision = "b824cd4a4c1d"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "current_medications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("family_member_id", sa.Integer(), nullable=False),
        sa.Column("medicine", sa.String(length=200), nullable=False),
        sa.Column("strength", sa.String(length=100), nullable=True),
        sa.Column("morning", sa.String(length=50), nullable=True),
        sa.Column("noon", sa.String(length=50), nullable=True),
        sa.Column("evening", sa.String(length=50), nullable=True),
        sa.Column("bedtime", sa.String(length=50), nullable=True),
        sa.Column("duration", sa.String(length=150), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["family_member_id"],
            ["family_members.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("current_medications")
    # ### end Alembic commands ###

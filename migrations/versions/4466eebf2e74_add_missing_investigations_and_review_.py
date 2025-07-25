"""Add missing investigations and review_followup fields to health records

Revision ID: 4466eebf2e74
Revises: enhance_health_records_001
Create Date: 2025-06-14 20:15:22.708788

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4466eebf2e74"
down_revision = "enhance_health_records_001"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("documents", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("content_type", sa.String(length=100), nullable=True)
        )
        batch_op.alter_column(
            "file_path",
            existing_type=sa.VARCHAR(length=500),
            type_=sa.String(length=512),
            existing_nullable=False,
        )
        batch_op.alter_column("file_size", existing_type=sa.INTEGER(), nullable=True)
        batch_op.drop_column("file_type")
        batch_op.drop_column("vectorized")
        batch_op.drop_column("extracted_text")

    with op.batch_alter_table("health_records", schema=None) as batch_op:
        batch_op.alter_column(
            "appointment_type",
            existing_type=sa.VARCHAR(length=100),
            type_=sa.String(length=50),
            existing_nullable=True,
        )
        batch_op.drop_column("prognosis")
        batch_op.drop_column("pain_scale")
        batch_op.drop_column("current_symptoms")
        batch_op.drop_column("medication_changes")
        batch_op.drop_column("condition_status")
        batch_op.drop_column("insurance_claim")
        batch_op.drop_column("visit_duration")
        batch_op.drop_column("description")
        batch_op.drop_column("vital_signs")
        batch_op.drop_column("functional_status")
        batch_op.drop_column("medical_urgency")
        batch_op.drop_column("title")
        batch_op.drop_column("treatment_plan")
        batch_op.drop_column("record_type")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("health_records", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("record_type", sa.VARCHAR(length=50), nullable=True)
        )
        batch_op.add_column(sa.Column("treatment_plan", sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column("title", sa.VARCHAR(length=200), nullable=True))
        batch_op.add_column(
            sa.Column("medical_urgency", sa.VARCHAR(length=20), nullable=True)
        )
        batch_op.add_column(sa.Column("functional_status", sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column("vital_signs", sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column("description", sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column("visit_duration", sa.INTEGER(), nullable=True))
        batch_op.add_column(
            sa.Column("insurance_claim", sa.VARCHAR(length=100), nullable=True)
        )
        batch_op.add_column(
            sa.Column("condition_status", sa.VARCHAR(length=50), nullable=True)
        )
        batch_op.add_column(sa.Column("medication_changes", sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column("current_symptoms", sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column("pain_scale", sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column("prognosis", sa.TEXT(), nullable=True))
        batch_op.alter_column(
            "appointment_type",
            existing_type=sa.String(length=50),
            type_=sa.VARCHAR(length=100),
            existing_nullable=True,
        )

    with op.batch_alter_table("documents", schema=None) as batch_op:
        batch_op.add_column(sa.Column("extracted_text", sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column("vectorized", sa.BOOLEAN(), nullable=True))
        batch_op.add_column(
            sa.Column("file_type", sa.VARCHAR(length=50), nullable=False)
        )
        batch_op.alter_column("file_size", existing_type=sa.INTEGER(), nullable=False)
        batch_op.alter_column(
            "file_path",
            existing_type=sa.String(length=512),
            type_=sa.VARCHAR(length=500),
            existing_nullable=False,
        )
        batch_op.drop_column("content_type")

    # ### end Alembic commands ###

"""Add enhanced health record fields

Revision ID: enhance_health_records_001
Revises: medical_conditions_001
Create Date: 2025-06-14 12:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "enhance_health_records_001"
down_revision = "medical_conditions_001"
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to health_records table
    with op.batch_alter_table("health_records", schema=None) as batch_op:
        # Enhanced doctor visit tracking fields
        batch_op.add_column(
            sa.Column("appointment_type", sa.String(length=100), nullable=True)
        )
        batch_op.add_column(
            sa.Column("doctor_specialty", sa.String(length=100), nullable=True)
        )
        batch_op.add_column(
            sa.Column("clinic_hospital", sa.String(length=200), nullable=True)
        )
        batch_op.add_column(sa.Column("visit_duration", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("insurance_claim", sa.String(length=100), nullable=True)
        )
        batch_op.add_column(sa.Column("cost", sa.Float(), nullable=True))

        # Medical condition tracking
        batch_op.add_column(sa.Column("current_symptoms", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("vital_signs", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("medical_urgency", sa.String(length=20), nullable=True)
        )

        # Treatment and prognosis tracking
        batch_op.add_column(sa.Column("treatment_plan", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("medication_changes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("prognosis", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("next_appointment", sa.DateTime(), nullable=True))

        # Condition progression tracking
        batch_op.add_column(
            sa.Column("condition_status", sa.String(length=50), nullable=True)
        )
        batch_op.add_column(sa.Column("pain_scale", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("functional_status", sa.Text(), nullable=True))

        # Link to ongoing medical conditions
        batch_op.add_column(
            sa.Column("related_condition_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_health_records_related_condition",
            "medical_conditions",
            ["related_condition_id"],
            ["id"],
        )


def downgrade():
    # Remove columns in reverse order
    with op.batch_alter_table("health_records", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_health_records_related_condition", type_="foreignkey"
        )
        batch_op.drop_column("related_condition_id")
        batch_op.drop_column("functional_status")
        batch_op.drop_column("pain_scale")
        batch_op.drop_column("condition_status")
        batch_op.drop_column("next_appointment")
        batch_op.drop_column("prognosis")
        batch_op.drop_column("medication_changes")
        batch_op.drop_column("treatment_plan")
        batch_op.drop_column("medical_urgency")
        batch_op.drop_column("vital_signs")
        batch_op.drop_column("current_symptoms")
        batch_op.drop_column("cost")
        batch_op.drop_column("insurance_claim")
        batch_op.drop_column("visit_duration")
        batch_op.drop_column("clinic_hospital")
        batch_op.drop_column("doctor_specialty")
        batch_op.drop_column("appointment_type")

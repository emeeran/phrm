"""Add medical condition tables

Revision ID: medical_conditions_001
Revises:
Create Date: 2025-06-14 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "medical_conditions_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create medical_conditions table
    op.create_table(
        "medical_conditions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("family_member_id", sa.Integer(), nullable=True),
        sa.Column("condition_name", sa.String(length=200), nullable=False),
        sa.Column("condition_category", sa.String(length=100), nullable=True),
        sa.Column("icd_code", sa.String(length=20), nullable=True),
        sa.Column("diagnosed_date", sa.DateTime(), nullable=True),
        sa.Column("diagnosing_doctor", sa.String(length=200), nullable=True),
        sa.Column("current_status", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("last_updated", sa.DateTime(), nullable=True),
        sa.Column("current_treatments", sa.Text(), nullable=True),
        sa.Column("treatment_goals", sa.Text(), nullable=True),
        sa.Column("treatment_effectiveness", sa.String(length=50), nullable=True),
        sa.Column("prognosis", sa.Text(), nullable=True),
        sa.Column("monitoring_plan", sa.Text(), nullable=True),
        sa.Column("next_review_date", sa.DateTime(), nullable=True),
        sa.Column("quality_of_life_impact", sa.String(length=20), nullable=True),
        sa.Column("functional_limitations", sa.Text(), nullable=True),
        sa.Column("work_impact", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("external_resources", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["family_member_id"],
            ["family_members.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for medical_conditions
    op.create_index(
        "idx_medical_conditions_user", "medical_conditions", ["user_id"], unique=False
    )
    op.create_index(
        "idx_medical_conditions_family_member",
        "medical_conditions",
        ["family_member_id"],
        unique=False,
    )
    op.create_index(
        "idx_medical_conditions_status",
        "medical_conditions",
        ["current_status"],
        unique=False,
    )

    # Create condition_progress_notes table
    op.create_table(
        "condition_progress_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("condition_id", sa.Integer(), nullable=False),
        sa.Column("note_date", sa.DateTime(), nullable=False),
        sa.Column("progress_status", sa.String(length=50), nullable=False),
        sa.Column("symptoms_changes", sa.Text(), nullable=True),
        sa.Column("treatment_changes", sa.Text(), nullable=True),
        sa.Column("pain_level", sa.Integer(), nullable=True),
        sa.Column("functional_score", sa.Integer(), nullable=True),
        sa.Column("vital_measurements", sa.Text(), nullable=True),
        sa.Column("clinical_observations", sa.Text(), nullable=True),
        sa.Column("doctor_notes", sa.Text(), nullable=True),
        sa.Column("patient_reported_outcomes", sa.Text(), nullable=True),
        sa.Column("recorded_by", sa.String(length=100), nullable=True),
        sa.Column("health_record_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["condition_id"],
            ["medical_conditions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["health_record_id"],
            ["health_records.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index for condition_progress_notes
    op.create_index(
        "idx_condition_progress_condition_date",
        "condition_progress_notes",
        ["condition_id", "note_date"],
        unique=False,
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_index(
        "idx_condition_progress_condition_date", table_name="condition_progress_notes"
    )
    op.drop_table("condition_progress_notes")

    op.drop_index("idx_medical_conditions_status", table_name="medical_conditions")
    op.drop_index(
        "idx_medical_conditions_family_member", table_name="medical_conditions"
    )
    op.drop_index("idx_medical_conditions_user", table_name="medical_conditions")
    op.drop_table("medical_conditions")

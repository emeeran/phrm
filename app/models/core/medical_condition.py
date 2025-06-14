"""
Medical Condition Tracking Model

Specialized model for tracking ongoing medical conditions, their progression,
and treatment outcomes over time.
"""

from datetime import datetime

from sqlalchemy import Index

from .base import db


class MedicalCondition(db.Model):
    """Model for tracking ongoing medical conditions"""

    __tablename__ = "medical_conditions"

    id = db.Column(db.Integer, primary_key=True)

    # Ownership
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    family_member_id = db.Column(
        db.Integer, db.ForeignKey("family_members.id"), nullable=True
    )

    # Condition Details
    condition_name = db.Column(db.String(200), nullable=False)
    condition_category = db.Column(
        db.String(100), nullable=True
    )  # chronic, acute, genetic, etc.
    icd_code = db.Column(db.String(20), nullable=True)  # ICD-10 code if known
    diagnosed_date = db.Column(db.DateTime, nullable=True)
    diagnosing_doctor = db.Column(db.String(200), nullable=True)

    # Current Status
    current_status = db.Column(
        db.String(50), nullable=False, default="active"
    )  # active, resolved, managed, monitoring
    severity = db.Column(db.String(20), nullable=True)  # mild, moderate, severe
    last_updated = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Treatment Information
    current_treatments = db.Column(
        db.Text, nullable=True
    )  # Current medications and treatments
    treatment_goals = db.Column(db.Text, nullable=True)  # Goals of treatment
    treatment_effectiveness = db.Column(
        db.String(50), nullable=True
    )  # excellent, good, poor, unknown

    # Prognosis and Monitoring
    prognosis = db.Column(db.Text, nullable=True)  # Long-term outlook
    monitoring_plan = db.Column(db.Text, nullable=True)  # How condition is monitored
    next_review_date = db.Column(db.DateTime, nullable=True)

    # Impact Assessment
    quality_of_life_impact = db.Column(
        db.String(20), nullable=True
    )  # minimal, moderate, significant, severe
    functional_limitations = db.Column(db.Text, nullable=True)
    work_impact = db.Column(
        db.String(50), nullable=True
    )  # none, minimal, moderate, significant

    # Notes and Additional Info
    notes = db.Column(db.Text, nullable=True)
    external_resources = db.Column(
        db.Text, nullable=True
    )  # Links to patient education materials

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    health_records = db.relationship(
        "HealthRecord",
        backref="related_condition",
        foreign_keys="HealthRecord.related_condition_id",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<MedicalCondition {self.condition_name}>"

    def get_condition_summary(self) -> dict:
        """Get a summary of the condition for AI analysis"""
        return {
            "condition_name": self.condition_name,
            "category": self.condition_category,
            "status": self.current_status,
            "severity": self.severity,
            "diagnosed_date": (
                self.diagnosed_date.isoformat() if self.diagnosed_date else None
            ),
            "prognosis": self.prognosis,
            "current_treatments": self.current_treatments,
            "quality_of_life_impact": self.quality_of_life_impact,
            "functional_limitations": self.functional_limitations,
        }


class ConditionProgressNote(db.Model):
    """Model for tracking condition progression over time"""

    __tablename__ = "condition_progress_notes"

    id = db.Column(db.Integer, primary_key=True)
    condition_id = db.Column(
        db.Integer, db.ForeignKey("medical_conditions.id"), nullable=False
    )

    # Progress Details
    note_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    progress_status = db.Column(
        db.String(50), nullable=False
    )  # improving, stable, worsening, complication
    symptoms_changes = db.Column(db.Text, nullable=True)
    treatment_changes = db.Column(db.Text, nullable=True)

    # Measurements and Assessments
    pain_level = db.Column(db.Integer, nullable=True)  # 1-10 scale
    functional_score = db.Column(
        db.Integer, nullable=True
    )  # Custom functional assessment
    vital_measurements = db.Column(db.Text, nullable=True)  # JSON of vital signs

    # Clinical Notes
    clinical_observations = db.Column(db.Text, nullable=True)
    doctor_notes = db.Column(db.Text, nullable=True)
    patient_reported_outcomes = db.Column(db.Text, nullable=True)

    # Administrative
    recorded_by = db.Column(db.String(100), nullable=True)  # doctor, patient, caregiver
    health_record_id = db.Column(
        db.Integer, db.ForeignKey("health_records.id"), nullable=True
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    condition = db.relationship("MedicalCondition", backref="progress_notes")

    def __repr__(self) -> str:
        return f"<ConditionProgressNote {self.note_date} - {self.progress_status}>"


# Add indexes for performance
Index("idx_medical_conditions_user", MedicalCondition.user_id)
Index("idx_medical_conditions_family_member", MedicalCondition.family_member_id)
Index("idx_medical_conditions_status", MedicalCondition.current_status)
Index(
    "idx_condition_progress_condition_date",
    ConditionProgressNote.condition_id,
    ConditionProgressNote.note_date.desc(),
)

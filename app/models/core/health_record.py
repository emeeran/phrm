"""
Health record and document models for the Personal Health Record Manager.
"""

from datetime import datetime

from .base import db


class HealthRecord(db.Model):
    """Model for health records"""

    __tablename__ = "health_records"

    id = db.Column(db.Integer, primary_key=True)

    # Legacy fields for backward compatibility
    record_type = db.Column(
        db.String(50), nullable=True
    )  # complaint, doctor_visit, investigation, prescription, lab_report, note
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)

    # Core fields
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    family_member_id = db.Column(
        db.Integer, db.ForeignKey("family_members.id"), nullable=True
    )

    # New standardized medical record fields
    chief_complaint = db.Column(db.Text, nullable=True)
    doctor = db.Column(db.String(200), nullable=True)
    investigations = db.Column(db.Text, nullable=True)
    diagnosis = db.Column(db.Text, nullable=True)
    prescription = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    review_followup = db.Column(db.Text, nullable=True)

    # Enhanced doctor visit tracking fields
    appointment_type = db.Column(
        db.String(100), nullable=True
    )  # consultation, follow-up, emergency, routine
    doctor_specialty = db.Column(
        db.String(100), nullable=True
    )  # cardiology, neurology, general practice, etc.
    clinic_hospital = db.Column(db.String(200), nullable=True)  # facility name
    visit_duration = db.Column(db.Integer, nullable=True)  # minutes
    insurance_claim = db.Column(
        db.String(100), nullable=True
    )  # claim number if applicable
    cost = db.Column(db.Float, nullable=True)  # visit cost

    # Medical condition tracking
    current_symptoms = db.Column(
        db.Text, nullable=True
    )  # active symptoms at time of visit
    vital_signs = db.Column(
        db.Text, nullable=True
    )  # blood pressure, heart rate, temperature, etc.
    medical_urgency = db.Column(
        db.String(20), nullable=True, default="routine"
    )  # routine, urgent, emergency

    # Treatment and prognosis tracking
    treatment_plan = db.Column(db.Text, nullable=True)  # detailed treatment plan
    medication_changes = db.Column(db.Text, nullable=True)  # changes to medications
    prognosis = db.Column(db.Text, nullable=True)  # doctor's prognosis
    next_appointment = db.Column(db.DateTime, nullable=True)  # scheduled follow-up

    # Condition progression tracking
    condition_status = db.Column(
        db.String(50), nullable=True
    )  # improving, stable, worsening, resolved
    pain_scale = db.Column(db.Integer, nullable=True)  # 1-10 pain scale if applicable
    functional_status = db.Column(
        db.Text, nullable=True
    )  # how condition affects daily activities

    # Link to ongoing medical conditions
    related_condition_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "medical_conditions.id", name="fk_health_records_related_condition"
        ),
        nullable=True,
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    documents = db.relationship(
        "Document",
        backref="health_record",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        # Generate title from available fields for display
        display_title = self.title
        if not display_title and self.chief_complaint:
            MAX_TITLE_LENGTH = 50
            display_title = (
                self.chief_complaint[:MAX_TITLE_LENGTH] + "..."
                if len(self.chief_complaint) > MAX_TITLE_LENGTH
                else self.chief_complaint
            )
        if not display_title:
            display_title = f"Health Record {self.id}"
        return f"<HealthRecord {display_title}>"


class Document(db.Model):
    """Model for uploaded documents"""

    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # PDF, image, etc.
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    health_record_id = db.Column(
        db.Integer, db.ForeignKey("health_records.id"), nullable=False
    )
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    extracted_text = db.Column(
        db.Text, nullable=True
    )  # Store OCR extracted text for PDFs
    vectorized = db.Column(
        db.Boolean, default=False
    )  # Flag to track if document is vectorized for RAG

    def __repr__(self) -> str:
        return f"<Document {self.filename}>"


class AISummary(db.Model):
    """Model for AI-generated summaries"""

    __tablename__ = "ai_summaries"

    id = db.Column(db.Integer, primary_key=True)
    health_record_id = db.Column(
        db.Integer, db.ForeignKey("health_records.id"), nullable=False
    )
    summary_text = db.Column(db.Text, nullable=False)
    summary_type = db.Column(
        db.String(20), nullable=False, default="standard"
    )  # standard, detailed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    health_record = db.relationship("HealthRecord", backref="summaries")

    def __repr__(self) -> str:
        return f"<AISummary for record {self.health_record_id}>"

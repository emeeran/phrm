"""
Streamlined health record and document models.
"""

from datetime import datetime

from .base import db

# Constants
SUMMARY_PREVIEW_LENGTH = 50


class HealthRecord(db.Model):
    """Streamlined health record model with essential fields only"""

    __tablename__ = "health_records"

    id = db.Column(db.Integer, primary_key=True)

    # Core record information
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    family_member_id = db.Column(
        db.Integer, db.ForeignKey("family_members.id"), nullable=True
    )

    # Essential medical fields
    chief_complaint = db.Column(db.Text, nullable=True)
    doctor = db.Column(db.String(200), nullable=True)
    investigations = db.Column(db.Text, nullable=True)
    diagnosis = db.Column(db.Text, nullable=True)
    prescription = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    review_followup = db.Column(db.Text, nullable=True)

    # Visit details
    appointment_type = db.Column(db.String(50), nullable=True)
    doctor_specialty = db.Column(db.String(100), nullable=True)
    clinic_hospital = db.Column(db.String(200), nullable=True)

    # Follow-up and cost
    next_appointment = db.Column(db.DateTime, nullable=True)
    cost = db.Column(db.Float, nullable=True)

    # Link to medical conditions
    related_condition_id = db.Column(
        db.Integer,
        db.ForeignKey("medical_conditions.id"),
        nullable=True,
    )

    # Timestamps
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
        return f"<HealthRecord {self.id} - {self.date.strftime('%Y-%m-%d')}>"

    @property
    def title(self) -> str:
        """Generate a title for the health record"""
        if self.chief_complaint:
            # Use first chars of chief complaint
            return self.chief_complaint[:SUMMARY_PREVIEW_LENGTH] + (
                "..." if len(self.chief_complaint) > SUMMARY_PREVIEW_LENGTH else ""
            )
        elif self.diagnosis:
            # Use first chars of diagnosis
            return self.diagnosis[:SUMMARY_PREVIEW_LENGTH] + (
                "..." if len(self.diagnosis) > SUMMARY_PREVIEW_LENGTH else ""
            )
        else:
            # Use date as fallback
            return f"Health Record - {self.date.strftime('%Y-%m-%d')}"


class Document(db.Model):
    """Document storage model"""

    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    health_record_id = db.Column(
        db.Integer, db.ForeignKey("health_records.id"), nullable=False
    )
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    content_type = db.Column(db.String(100), nullable=True)
    extracted_text = db.Column(db.Text, nullable=True)  # OCR/extracted content for AI
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def file_type(self) -> str:
        """Get file type from content_type or filename extension"""
        if self.content_type:
            # Map MIME types to file extensions
            mime_to_ext = {
                "application/pdf": "pdf",
                "image/jpeg": "jpg",
                "image/jpg": "jpg",
                "image/png": "png",
                "image/gif": "gif",
                "text/plain": "txt",
                "application/msword": "doc",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
            }
            return mime_to_ext.get(self.content_type, "unknown")

        # Fallback to filename extension
        if self.filename:
            import os

            _, ext = os.path.splitext(self.filename)
            return ext.lower().lstrip(".")

        return "unknown"

    def __repr__(self) -> str:
        return f"<Document {self.filename}>"


class AISummary(db.Model):
    """AI-generated summaries model"""

    __tablename__ = "ai_summaries"

    id = db.Column(db.Integer, primary_key=True)
    health_record_id = db.Column(
        db.Integer, db.ForeignKey("health_records.id"), nullable=False
    )
    summary_text = db.Column(db.Text, nullable=False)
    summary_type = db.Column(db.String(20), nullable=False, default="standard")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    health_record = db.relationship("HealthRecord", backref="summaries")

    def __repr__(self) -> str:
        return f"<AISummary for record {self.health_record_id}>"

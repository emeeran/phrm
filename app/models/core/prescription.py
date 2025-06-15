"""
Prescription entry model for structured medication tracking.
"""

from datetime import datetime

from .base import db


class PrescriptionEntry(db.Model):
    """Individual prescription entry with structured dosage information"""

    __tablename__ = "prescription_entries"

    id = db.Column(db.Integer, primary_key=True)
    health_record_id = db.Column(
        db.Integer, db.ForeignKey("health_records.id"), nullable=False
    )

    # Medication details
    medicine = db.Column(db.String(200), nullable=False)
    strength = db.Column(db.String(100), nullable=True)

    # Dosage schedule
    morning = db.Column(db.String(50), nullable=True)  # e.g., "1 tablet", "2 ml", etc.
    noon = db.Column(db.String(50), nullable=True)
    evening = db.Column(db.String(50), nullable=True)
    bedtime = db.Column(db.String(50), nullable=True)

    # Duration and additional info
    duration = db.Column(
        db.String(100), nullable=True
    )  # e.g., "7 days", "2 weeks", etc.
    notes = db.Column(db.Text, nullable=True)  # Additional instructions

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    health_record = db.relationship(
        "HealthRecord",
        backref=db.backref(
            "prescription_entries", lazy=True, cascade="all, delete-orphan"
        ),
    )

    def __repr__(self):
        return f"<PrescriptionEntry {self.medicine} - {self.strength}>"

    def to_dict(self):
        """Convert prescription entry to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "medicine": self.medicine,
            "strength": self.strength,
            "morning": self.morning,
            "noon": self.noon,
            "evening": self.evening,
            "bedtime": self.bedtime,
            "duration": self.duration,
            "notes": self.notes,
        }

    @property
    def total_daily_doses(self):
        """Calculate total number of doses per day"""
        doses = [self.morning, self.noon, self.evening, self.bedtime]
        return len([dose for dose in doses if dose and dose.strip()])

    @property
    def dosage_summary(self):
        """Get a summary of the dosage schedule"""
        schedule = []
        if self.morning:
            schedule.append(f"Morning: {self.morning}")
        if self.noon:
            schedule.append(f"Noon: {self.noon}")
        if self.evening:
            schedule.append(f"Evening: {self.evening}")
        if self.bedtime:
            schedule.append(f"Bedtime: {self.bedtime}")
        return " | ".join(schedule) if schedule else "No dosage specified"

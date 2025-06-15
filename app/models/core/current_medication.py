"""
Current medication model for family members.
"""

from datetime import datetime

from .base import db


class CurrentMedication(db.Model):
    """Current medication entries for family members"""

    __tablename__ = "current_medications"

    id = db.Column(db.Integer, primary_key=True)
    family_member_id = db.Column(
        db.Integer, db.ForeignKey("family_members.id"), nullable=False
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
        db.String(150), nullable=True
    )  # e.g., "Ongoing", "3 months", etc.
    notes = db.Column(db.Text, nullable=True)  # Additional instructions

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    family_member = db.relationship(
        "FamilyMember",
        backref=db.backref(
            "current_medication_entries", lazy=True, cascade="all, delete-orphan"
        ),
    )

    def __repr__(self):
        return f"<CurrentMedication {self.medicine} - {self.strength}>"

    def to_dict(self):
        """Convert current medication to dictionary for JSON serialization"""
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

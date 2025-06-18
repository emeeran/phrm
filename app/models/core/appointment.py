"""
Appointment model for scheduling and tracking doctor appointments.
"""

from datetime import datetime

from .base import db


class Appointment(db.Model):
    """Model for tracking doctor appointments"""

    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)

    # Ownership - either user or family member
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    family_member_id = db.Column(
        db.Integer, db.ForeignKey("family_members.id"), nullable=True
    )

    # Appointment details
    title = db.Column(db.String(200), nullable=False)
    doctor_name = db.Column(db.String(200), nullable=False)
    doctor_specialty = db.Column(db.String(100), nullable=True)
    clinic_hospital = db.Column(db.String(200), nullable=True)

    # Date and time
    appointment_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=True, default=30)

    # Status tracking
    status = db.Column(
        db.String(20),
        nullable=False,
        default="scheduled",  # scheduled, completed, cancelled, rescheduled
    )

    # Additional information
    purpose = db.Column(db.Text, nullable=True)
    preparation = db.Column(db.Text, nullable=True)  # Any pre-appointment instructions
    notes = db.Column(db.Text, nullable=True)

    # Follow-up information
    follow_up_needed = db.Column(db.Boolean, default=False)
    follow_up_appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointments.id"), nullable=True
    )

    # Related health records
    health_record_id = db.Column(
        db.Integer, db.ForeignKey("health_records.id"), nullable=True
    )

    # Reminders
    reminder_sent = db.Column(db.Boolean, default=False)
    reminder_date = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = db.relationship("User", backref=db.backref("appointments", lazy=True))
    family_member = db.relationship(
        "FamilyMember", backref=db.backref("appointments", lazy=True)
    )
    health_record = db.relationship(
        "HealthRecord", backref=db.backref("appointment", uselist=False)
    )
    follow_up_appointment = db.relationship(
        "Appointment",
        remote_side=[id],
        backref=db.backref("previous_appointment", uselist=False),
    )

    def __repr__(self) -> str:
        person = self.family_member.first_name if self.family_member else "Self"
        return f"<Appointment: {person} with Dr. {self.doctor_name} on {self.appointment_date.strftime('%Y-%m-%d %H:%M')}>"

    @property
    def is_upcoming(self) -> bool:
        """Check if appointment is in the future"""
        return self.appointment_date > datetime.utcnow() and self.status == "scheduled"

    @property
    def is_today(self) -> bool:
        """Check if appointment is today"""
        today = datetime.utcnow().date()
        return self.appointment_date.date() == today and self.status == "scheduled"

    @property
    def person_name(self) -> str:
        """Get the name of the person who has the appointment"""
        if self.family_member:
            return f"{self.family_member.first_name} {self.family_member.last_name}"
        elif self.user:
            return (
                f"{self.user.first_name} {self.user.last_name}"
                if self.user.first_name
                else self.user.username
            )
        return "Unknown"

    def to_dict(self) -> dict:
        """Convert appointment to dictionary for API responses"""
        return {
            "id": self.id,
            "title": self.title,
            "doctor_name": self.doctor_name,
            "doctor_specialty": self.doctor_specialty,
            "clinic_hospital": self.clinic_hospital,
            "appointment_date": (
                self.appointment_date.isoformat() if self.appointment_date else None
            ),
            "duration_minutes": self.duration_minutes,
            "status": self.status,
            "purpose": self.purpose,
            "preparation": self.preparation,
            "notes": self.notes,
            "person_name": self.person_name,
            "is_upcoming": self.is_upcoming,
            "is_today": self.is_today,
        }

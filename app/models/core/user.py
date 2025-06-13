"""
User and family member models for the Personal Health Record Manager.
"""

import secrets
from datetime import datetime, timedelta, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .base import db, user_family


class User(UserMixin, db.Model):
    """User model for authentication and profile management"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Notification preferences
    email_notifications = db.Column(db.Boolean, default=True, nullable=False)
    record_reminders = db.Column(db.Boolean, default=True, nullable=False)
    security_alerts = db.Column(db.Boolean, default=True, nullable=False)
    ai_insights = db.Column(db.Boolean, default=True, nullable=False)
    notification_frequency = db.Column(db.String(20), default="daily", nullable=False)

    # Password reset fields
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    # Relationships
    family_members = db.relationship(
        "FamilyMember", secondary=user_family, backref="caregivers"
    )
    records = db.relationship("HealthRecord", backref="user", lazy="dynamic")

    def set_password(self, password: str) -> None:
        """Set password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self) -> str:
        """Generate a secure reset token"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        return self.reset_token

    def verify_reset_token(self, token: str) -> bool:
        """Verify if the reset token is valid and not expired"""
        if not self.reset_token or not self.reset_token_expiry:
            return False
        if self.reset_token != token:
            return False
        if datetime.now(timezone.utc) > self.reset_token_expiry:
            return False
        return True

    def reset_password(self, new_password: str) -> None:
        """Reset the password and clear the reset token"""
        self.set_password(new_password)
        self.reset_token = None
        self.reset_token_expiry = None

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class FamilyMember(db.Model):
    """Model for family members"""

    __tablename__ = "family_members"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    relationship = db.Column(
        db.String(50), nullable=True
    )  # e.g., spouse, child, parent

    # Basic Information
    gender = db.Column(db.String(20), nullable=True)
    blood_type = db.Column(db.String(10), nullable=True)
    height = db.Column(db.Float, nullable=True)
    weight = db.Column(db.Float, nullable=True)

    # Contact Information
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    primary_doctor = db.Column(db.String(100), nullable=True)

    # Insurance Information
    insurance_provider = db.Column(db.String(100), nullable=True)
    insurance_number = db.Column(db.String(50), nullable=True)

    # Medical History Fields
    allergies = db.Column(db.Text, nullable=True)
    chronic_conditions = db.Column(db.Text, nullable=True)
    current_medications = db.Column(db.Text, nullable=True)
    family_medical_history = db.Column(db.Text, nullable=True)
    surgical_history = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    records = db.relationship("HealthRecord", backref="family_member", lazy="dynamic")

    def get_complete_medical_context(self) -> str:
        """Get complete medical context for AI chat"""
        context = f"--- Medical Profile for {self.first_name} {self.last_name} ---\n"

        # Build context sections
        context += self._get_demographics_context()
        context += self._get_medical_conditions_context()
        context += self._get_medications_context()
        context += self._get_medical_history_context()
        context += self._get_health_records_context()

        return context

    def _get_demographics_context(self) -> str:
        """Get demographics section of medical context"""
        context = ""

        if self.date_of_birth:
            today = datetime.now(timezone.utc)
            age = (
                today.year
                - self.date_of_birth.year
                - (
                    (today.month, today.day)
                    < (self.date_of_birth.month, self.date_of_birth.day)
                )
            )
            context += f"Age: {age} years old\n"

        for attr, label in [
            ("relationship", "Relationship"),
            ("gender", "Gender"),
            ("blood_type", "Blood Type"),
        ]:
            value = getattr(self, attr)
            if value:
                context += f"{label}: {value}\n"

        if self.height:
            context += f"Height: {self.height} cm\n"
        if self.weight:
            context += f"Weight: {self.weight} kg\n"

        return context

    def _get_medical_conditions_context(self) -> str:
        """Get medical conditions section"""
        context = ""

        if self.chronic_conditions:
            context += f"\nChronic Conditions:\n{self.chronic_conditions}\n"

        if self.allergies:
            context += f"\nKnown Allergies:\n{self.allergies}\n"

        return context

    def _get_medications_context(self) -> str:
        """Get medications section"""
        context = ""

        if self.current_medications:
            context += f"\nCurrent Medications:\n{self.current_medications}\n"

        return context

    def _get_medical_history_context(self) -> str:
        """Get medical history section"""
        context = ""

        if self.family_medical_history:
            context += f"\nFamily Medical History:\n{self.family_medical_history}\n"

        if self.surgical_history:
            context += f"\nSurgical History:\n{self.surgical_history}\n"

        return context

    def _get_health_records_context(self) -> str:
        """Get health records context"""
        context = ""

        recent_records = (
            self.records.order_by(db.desc(self.records.property.mapper.class_.date))
            .limit(5)
            .all()
        )

        if recent_records:
            context += f"\nRecent Health Records ({len(recent_records)} most recent):\n"
            for record in recent_records:
                context += f"- {record.date.strftime('%Y-%m-%d')}: {record.title or 'Health Record'}\n"
                if record.chief_complaint:
                    context += f"  Complaint: {record.chief_complaint}\n"
                if record.diagnosis:
                    context += f"  Diagnosis: {record.diagnosis}\n"

        return context

    def __repr__(self) -> str:
        return f"<FamilyMember {self.first_name} {self.last_name}>"

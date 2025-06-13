"""
AI Security Event Model

Security-related AI events and incidents tracking.
"""

from datetime import datetime

from sqlalchemy import Index

from ..core.base import db


class AISecurityEvent(db.Model):
    """
    Security-related AI events and incidents

    Tracks security events, anomalies, and potential threats in AI operations
    """

    __tablename__ = "ai_security_events"

    id = db.Column(db.Integer, primary_key=True)

    # Event identification
    event_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    event_type = db.Column(
        db.String(50), nullable=False, index=True
    )  # ANOMALY, THREAT, VIOLATION, BREACH
    severity = db.Column(
        db.String(20), nullable=False, index=True
    )  # LOW, MEDIUM, HIGH, CRITICAL

    # Related audit log
    audit_log_id = db.Column(
        db.Integer, db.ForeignKey("ai_audit_logs.id"), nullable=True, index=True
    )

    # Event details
    event_description = db.Column(db.Text, nullable=False)
    detection_method = db.Column(
        db.String(100), nullable=True
    )  # How was this detected?

    # Context
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True, index=True
    )
    operation_type = db.Column(db.String(50), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)

    # Risk assessment
    risk_score = db.Column(db.Float, nullable=True)  # 0-100
    potential_impact = db.Column(db.String(500), nullable=True)
    affected_data_types = db.Column(db.Text, nullable=True)  # JSON array

    # Response tracking
    status = db.Column(
        db.String(20), nullable=False, default="OPEN"
    )  # OPEN, INVESTIGATING, RESOLVED, CLOSED
    assigned_to = db.Column(db.String(100), nullable=True)
    response_actions = db.Column(db.Text, nullable=True)  # JSON array of actions taken
    resolution_notes = db.Column(db.Text, nullable=True)

    # Timestamps
    detected_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)

    # Notification tracking
    notifications_sent = db.Column(db.Boolean, default=False)
    escalated = db.Column(db.Boolean, default=False)
    escalation_level = db.Column(db.Integer, nullable=True)  # 1, 2, 3, etc.

    # Indexes
    __table_args__ = (
        Index("idx_security_severity_status", "severity", "status"),
        Index("idx_security_type_detected", "event_type", "detected_at"),
        Index("idx_security_user_detected", "user_id", "detected_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<AISecurityEvent {self.event_id} - {self.event_type} ({self.severity})>"
        )

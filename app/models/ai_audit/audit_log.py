"""
AI Audit Log Model

Core audit log table for AI operations tracking.
"""

from datetime import datetime

from sqlalchemy import Index

from ..core.base import db


class AIAuditLog(db.Model):
    """
    Core audit log table for AI operations

    This table stores detailed audit information for all AI-related operations
    including chat interactions, summary generation, symptom checking, etc.
    """

    __tablename__ = "ai_audit_logs"

    id = db.Column(db.Integer, primary_key=True)

    # Basic audit information
    timestamp = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    session_id = db.Column(
        db.String(128), nullable=True, index=True
    )  # Track user sessions

    # Operation details
    operation_type = db.Column(
        db.String(50), nullable=False, index=True
    )  # chat, summarize, symptom_check, etc.
    operation_subtype = db.Column(
        db.String(50), nullable=True
    )  # detailed operation classification

    # Data classification and sensitivity
    data_classification = db.Column(
        db.String(20), nullable=False, default="PHI"
    )  # PHI, PII, PUBLIC, INTERNAL
    sensitivity_level = db.Column(
        db.String(20), nullable=False, default="HIGH"
    )  # LOW, MEDIUM, HIGH, CRITICAL

    # AI model information
    ai_model_used = db.Column(
        db.String(100), nullable=True
    )  # gemini-2.5-flash, gpt-4, etc.
    ai_model_version = db.Column(db.String(50), nullable=True)
    fallback_used = db.Column(db.Boolean, default=False)  # Was fallback model used?

    # Request/Response details
    input_size = db.Column(
        db.Integer, nullable=True
    )  # Input text/data size in characters
    output_size = db.Column(db.Integer, nullable=True)  # Output text size in characters
    processing_time_ms = db.Column(
        db.Integer, nullable=True
    )  # Processing time in milliseconds

    # Content classification
    medical_context_accessed = db.Column(
        db.Boolean, default=False
    )  # Was medical data accessed?
    pii_detected = db.Column(
        db.Boolean, default=False
    )  # Was PII detected in input/output?
    family_member_id = db.Column(
        db.Integer, db.ForeignKey("family_members.id"), nullable=True
    )  # Related family member
    health_record_ids = db.Column(
        db.Text, nullable=True
    )  # JSON array of accessed record IDs

    # Security and compliance
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4/IPv6 address
    user_agent = db.Column(db.String(500), nullable=True)  # Browser/client information
    geographic_location = db.Column(
        db.String(100), nullable=True
    )  # Country/region if available

    # Risk assessment
    risk_score = db.Column(db.Float, nullable=True)  # Calculated risk score (0-100)
    risk_factors = db.Column(db.Text, nullable=True)  # JSON array of risk factors

    # Compliance framework tracking
    hipaa_applicable = db.Column(db.Boolean, default=True)
    gdpr_applicable = db.Column(db.Boolean, default=False)
    soc2_applicable = db.Column(db.Boolean, default=True)
    nist_applicable = db.Column(db.Boolean, default=True)

    # Status and outcome
    operation_status = db.Column(
        db.String(20), nullable=False, default="SUCCESS"
    )  # SUCCESS, FAILED, PARTIAL
    error_code = db.Column(
        db.String(50), nullable=True
    )  # Error code if operation failed
    error_message = db.Column(db.Text, nullable=True)  # Error details

    # Audit metadata
    retention_period_days = db.Column(
        db.Integer, nullable=False, default=2555
    )  # 7 years default
    archived = db.Column(db.Boolean, default=False)
    archive_date = db.Column(db.DateTime, nullable=True)

    # Additional context (JSON)
    additional_context = db.Column(
        db.Text, nullable=True
    )  # JSON blob for extensibility

    # Indexes for performance
    __table_args__ = (
        Index("idx_ai_audit_user_timestamp", "user_id", "timestamp"),
        Index("idx_ai_audit_operation_timestamp", "operation_type", "timestamp"),
        Index(
            "idx_ai_audit_classification", "data_classification", "sensitivity_level"
        ),
        Index(
            "idx_ai_audit_compliance",
            "hipaa_applicable",
            "gdpr_applicable",
            "timestamp",
        ),
        Index("idx_ai_audit_risk", "risk_score", "timestamp"),
        Index("idx_ai_audit_status", "operation_status", "timestamp"),
        Index("idx_ai_audit_session", "session_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<AIAuditLog {self.operation_type} for user {self.user_id} at {self.timestamp}>"

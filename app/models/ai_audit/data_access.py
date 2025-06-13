"""
AI Data Access Model

Detailed data access tracking for AI operations for GDPR/HIPAA compliance.
"""

from datetime import datetime

from sqlalchemy import Index

from ..core.base import db


class AIDataAccess(db.Model):
    """
    Detailed data access tracking for AI operations

    Tracks specific data access patterns for GDPR/HIPAA compliance
    """

    __tablename__ = "ai_data_access"

    id = db.Column(db.Integer, primary_key=True)

    # Access identification
    access_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    audit_log_id = db.Column(
        db.Integer, db.ForeignKey("ai_audit_logs.id"), nullable=False, index=True
    )

    # Data identification
    data_type = db.Column(
        db.String(50), nullable=False, index=True
    )  # HEALTH_RECORD, FAMILY_MEMBER, USER_PROFILE
    data_id = db.Column(
        db.String(100), nullable=False, index=True
    )  # ID of the accessed data
    data_classification = db.Column(
        db.String(20), nullable=False, index=True
    )  # PHI, PII, PUBLIC

    # Access details
    access_purpose = db.Column(
        db.String(100), nullable=False, index=True
    )  # AI_CHAT, SUMMARIZATION, ANALYSIS
    access_method = db.Column(db.String(50), nullable=False)  # READ, PROCESS, ANALYZE
    data_fields_accessed = db.Column(
        db.Text, nullable=True
    )  # JSON array of specific fields

    # Data content summary
    data_size_chars = db.Column(db.Integer, nullable=True)  # Size of accessed data
    sensitive_data_detected = db.Column(db.Boolean, default=False)
    phi_categories = db.Column(
        db.Text, nullable=True
    )  # JSON array of PHI categories found

    # Legal basis (for GDPR compliance)
    legal_basis = db.Column(
        db.String(100), nullable=True
    )  # CONSENT, LEGITIMATE_INTEREST, etc.
    consent_id = db.Column(db.String(100), nullable=True)  # Reference to user consent

    # Data minimization
    data_necessary = db.Column(
        db.Boolean, default=True
    )  # Was this data necessary for the operation?
    alternative_available = db.Column(
        db.Boolean, default=False
    )  # Could operation work without this data?

    # Timestamps
    accessed_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    data_last_modified = db.Column(
        db.DateTime, nullable=True
    )  # When was the accessed data last modified?

    # Retention and disposal
    retention_period_days = db.Column(
        db.Integer, nullable=False, default=2555
    )  # 7 years
    data_disposed = db.Column(db.Boolean, default=False)
    disposal_date = db.Column(db.DateTime, nullable=True)
    disposal_method = db.Column(db.String(50), nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_data_access_type_id", "data_type", "data_id"),
        Index("idx_data_access_audit", "audit_log_id", "accessed_at"),
        Index("idx_data_access_classification", "data_classification", "accessed_at"),
        Index("idx_data_access_purpose", "access_purpose", "accessed_at"),
    )

    def __repr__(self) -> str:
        return f"<AIDataAccess {self.access_id} - {self.data_type}:{self.data_id}>"

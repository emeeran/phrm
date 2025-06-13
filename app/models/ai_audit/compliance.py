"""
AI Compliance Report Model

Compliance assessment reports for periodic auditing.
"""

from datetime import datetime

from sqlalchemy import Index

from ..core.base import db


class AIComplianceReport(db.Model):
    """
    Compliance assessment reports for periodic auditing

    Stores periodic compliance reports and assessments for regulatory requirements
    """

    __tablename__ = "ai_compliance_reports"

    id = db.Column(db.Integer, primary_key=True)

    # Report identification
    report_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    compliance_framework = db.Column(
        db.String(50), nullable=False, index=True
    )  # HIPAA, GDPR, SOC2, NIST

    # Report period
    period_start = db.Column(db.DateTime, nullable=False, index=True)
    period_end = db.Column(db.DateTime, nullable=False, index=True)

    # Compliance metrics
    total_operations = db.Column(db.Integer, nullable=False, default=0)
    compliant_operations = db.Column(db.Integer, nullable=False, default=0)
    non_compliant_operations = db.Column(db.Integer, nullable=False, default=0)
    compliance_score = db.Column(db.Float, nullable=False, default=0.0)  # 0-100

    # Risk assessment
    high_risk_operations = db.Column(db.Integer, nullable=False, default=0)
    medium_risk_operations = db.Column(db.Integer, nullable=False, default=0)
    low_risk_operations = db.Column(db.Integer, nullable=False, default=0)
    average_risk_score = db.Column(db.Float, nullable=True)

    # Violations and issues
    critical_violations = db.Column(db.Integer, nullable=False, default=0)
    major_violations = db.Column(db.Integer, nullable=False, default=0)
    minor_violations = db.Column(db.Integer, nullable=False, default=0)
    violation_details = db.Column(
        db.Text, nullable=True
    )  # JSON array of violation details

    # Recommendations
    recommendations = db.Column(db.Text, nullable=True)  # JSON array of recommendations
    action_items = db.Column(db.Text, nullable=True)  # JSON array of required actions

    # Report metadata
    report_summary = db.Column(db.Text, nullable=True)
    executive_summary = db.Column(db.Text, nullable=True)
    detailed_findings = db.Column(db.Text, nullable=True)

    # Status tracking
    status = db.Column(
        db.String(20), nullable=False, default="DRAFT"
    )  # DRAFT, FINAL, ARCHIVED
    generated_by = db.Column(
        db.String(100), nullable=True
    )  # System or user who generated
    reviewed_by = db.Column(db.String(100), nullable=True)  # Who reviewed the report
    approved_by = db.Column(db.String(100), nullable=True)  # Who approved the report

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    finalized_at = db.Column(db.DateTime, nullable=True)
    next_review_date = db.Column(db.DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        Index(
            "idx_compliance_framework_period",
            "compliance_framework",
            "period_start",
            "period_end",
        ),
        Index("idx_compliance_score_status", "compliance_score", "status"),
        Index("idx_compliance_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AIComplianceReport {self.report_id} for {self.compliance_framework}>"

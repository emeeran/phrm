"""
AI Operation Metrics Model

Performance and usage metrics aggregation for AI operations.
"""

from datetime import datetime

from sqlalchemy import Index

from ..core.base import db


class AIOperationMetrics(db.Model):
    """
    Performance and usage metrics aggregation

    Stores aggregated metrics for AI operations performance monitoring
    """

    __tablename__ = "ai_operation_metrics"

    id = db.Column(db.Integer, primary_key=True)

    # Time aggregation
    metric_date = db.Column(db.Date, nullable=False, index=True)
    aggregation_period = db.Column(
        db.String(20), nullable=False, index=True
    )  # HOURLY, DAILY, WEEKLY, MONTHLY

    # Operation classification
    operation_type = db.Column(db.String(50), nullable=False, index=True)
    ai_model_used = db.Column(db.String(100), nullable=True)

    # Usage metrics
    total_operations = db.Column(db.Integer, nullable=False, default=0)
    successful_operations = db.Column(db.Integer, nullable=False, default=0)
    failed_operations = db.Column(db.Integer, nullable=False, default=0)

    # Performance metrics
    avg_processing_time_ms = db.Column(db.Float, nullable=True)
    min_processing_time_ms = db.Column(db.Integer, nullable=True)
    max_processing_time_ms = db.Column(db.Integer, nullable=True)
    total_processing_time_ms = db.Column(db.BigInteger, nullable=True)

    # Data volume metrics
    total_input_chars = db.Column(db.BigInteger, nullable=True)
    total_output_chars = db.Column(db.BigInteger, nullable=True)
    avg_input_size = db.Column(db.Float, nullable=True)
    avg_output_size = db.Column(db.Float, nullable=True)

    # User engagement metrics
    unique_users = db.Column(db.Integer, nullable=False, default=0)
    unique_sessions = db.Column(db.Integer, nullable=False, default=0)

    # Risk and compliance metrics
    avg_risk_score = db.Column(db.Float, nullable=True)
    high_risk_operations = db.Column(db.Integer, nullable=False, default=0)
    phi_accessed_operations = db.Column(db.Integer, nullable=False, default=0)

    # Error tracking
    error_rate = db.Column(db.Float, nullable=True)  # Percentage
    common_errors = db.Column(
        db.Text, nullable=True
    )  # JSON array of error codes/counts

    # Geographic distribution
    geographic_distribution = db.Column(
        db.Text, nullable=True
    )  # JSON object of location:count

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Indexes
    __table_args__ = (
        Index("idx_metrics_date_type", "metric_date", "operation_type"),
        Index("idx_metrics_period_model", "aggregation_period", "ai_model_used"),
        Index("idx_metrics_performance", "avg_processing_time_ms", "error_rate"),
    )

    def __repr__(self) -> str:
        return f"<AIOperationMetrics {self.operation_type} for {self.metric_date}>"

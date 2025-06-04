from datetime import datetime, timedelta
import secrets
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index, text

db = SQLAlchemy()

# User-Family relationship table
user_family = db.Table('user_family',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('family_member_id', db.Integer, db.ForeignKey('family_members.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    """User model for authentication and profile management"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    # Notification preferences
    email_notifications = db.Column(db.Boolean, default=True, nullable=False)
    record_reminders = db.Column(db.Boolean, default=True, nullable=False)
    security_alerts = db.Column(db.Boolean, default=True, nullable=False)
    ai_insights = db.Column(db.Boolean, default=True, nullable=False)
    notification_frequency = db.Column(db.String(20), default='daily', nullable=False)

    # Password reset fields
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    # Relationships
    family_members = db.relationship('FamilyMember', secondary=user_family, backref='caregivers')
    records = db.relationship('HealthRecord', backref='user', lazy='dynamic')

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        """Generate a secure reset token"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token

    def verify_reset_token(self, token):
        """Verify if the reset token is valid and not expired"""
        if not self.reset_token or not self.reset_token_expiry:
            return False
        if self.reset_token != token:
            return False
        if datetime.utcnow() > self.reset_token_expiry:
            return False
        return True

    def reset_password(self, new_password):
        """Reset the password and clear the reset token"""
        self.set_password(new_password)
        self.reset_token = None
        self.reset_token_expiry = None

    def __repr__(self):
        return f'<User {self.username}>'

class FamilyMember(db.Model):
    """Model for family members"""
    __tablename__ = 'family_members'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    relationship = db.Column(db.String(50), nullable=True)  # e.g., spouse, child, parent
    
    # Basic Information (existing fields)
    gender = db.Column(db.String(20), nullable=True)
    blood_type = db.Column(db.String(10), nullable=True)
    height = db.Column(db.Float, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    
    # Contact Information (existing fields)
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    primary_doctor = db.Column(db.String(100), nullable=True)
    
    # Insurance Information (existing fields)
    insurance_provider = db.Column(db.String(100), nullable=True)
    insurance_number = db.Column(db.String(50), nullable=True)
    
    # Medical History Fields (existing fields)
    allergies = db.Column(db.Text, nullable=True)  # Known allergies
    chronic_conditions = db.Column(db.Text, nullable=True)  # Chronic conditions
    current_medications = db.Column(db.Text, nullable=True)  # Current medications
    family_medical_history = db.Column(db.Text, nullable=True)  # Family medical history
    surgical_history = db.Column(db.Text, nullable=True)  # Surgical history
    notes = db.Column(db.Text, nullable=True)  # Additional notes
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    records = db.relationship('HealthRecord', backref='family_member', lazy='dynamic')

    def get_complete_medical_context(self):
        """Get complete medical context for AI chat"""
        context = f"--- Medical Profile for {self.first_name} {self.last_name} ---\n"
        
        # Basic Demographics
        if self.date_of_birth:
            from datetime import datetime
            today = datetime.today()
            age = today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
            context += f"Age: {age} years old\n"
        
        if self.relationship:
            context += f"Relationship: {self.relationship}\n"
        
        if self.gender:
            context += f"Gender: {self.gender}\n"
        
        if self.blood_type:
            context += f"Blood Type: {self.blood_type}\n"
        
        if self.height:
            context += f"Height: {self.height} cm\n"
        
        if self.weight:
            context += f"Weight: {self.weight} kg\n"
        
        # Medical Conditions
        if self.chronic_conditions:
            context += f"\nChronic Conditions:\n{self.chronic_conditions}\n"
        
        if self.allergies:
            context += f"\nAllergies:\n{self.allergies}\n"
        
        # Medications
        if self.current_medications:
            context += f"\nCurrent Medications:\n{self.current_medications}\n"
        
        # Medical History
        if self.family_medical_history:
            context += f"\nFamily Medical History:\n{self.family_medical_history}\n"
        
        if self.surgical_history:
            context += f"\nSurgical History:\n{self.surgical_history}\n"
        
        # Additional Notes
        if self.notes:
            context += f"\nAdditional Notes:\n{self.notes}\n"
        
        # Add health records
        records = self.records.order_by(HealthRecord.date.desc()).all()
        if records:
            context += f"\n--- Health Records ({len(records)} total) ---\n"
            for idx, record in enumerate(records[:10]):  # Limit to 10 most recent
                context += f"\n{idx+1}. {record.title}\n"
                context += f"   Type: {record.record_type.replace('_', ' ').title()}\n"
                context += f"   Date: {record.date.strftime('%Y-%m-%d')}\n"
                if record.description:
                    context += f"   Details: {record.description[:200]}{'...' if len(record.description) > 200 else ''}\n"
        
        return context

    def __repr__(self):
        return f'<FamilyMember {self.first_name} {self.last_name}>'

class HealthRecord(db.Model):
    """Model for health records"""
    __tablename__ = 'health_records'

    id = db.Column(db.Integer, primary_key=True)
    # Legacy fields (maintained for backward compatibility)
    record_type = db.Column(db.String(50), nullable=True)  # complaint, doctor_visit, investigation, prescription, lab_report, note
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Core fields
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    family_member_id = db.Column(db.Integer, db.ForeignKey('family_members.id'), nullable=True)
    
    # New standardized medical record fields
    chief_complaint = db.Column(db.Text, nullable=True)
    doctor = db.Column(db.String(200), nullable=True)
    investigations = db.Column(db.Text, nullable=True)
    diagnosis = db.Column(db.Text, nullable=True)
    prescription = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    review_followup = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = db.relationship('Document', backref='health_record', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        # Generate title from available fields for display
        display_title = self.title
        if not display_title and self.chief_complaint:
            display_title = self.chief_complaint[:50] + "..." if len(self.chief_complaint) > 50 else self.chief_complaint
        if not display_title:
            display_title = f"Health Record {self.id}"
        return f'<HealthRecord {display_title}>'

class Document(db.Model):
    """Model for uploaded documents"""
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # PDF, image, etc.
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    health_record_id = db.Column(db.Integer, db.ForeignKey('health_records.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    extracted_text = db.Column(db.Text, nullable=True)  # Store OCR extracted text for PDFs
    vectorized = db.Column(db.Boolean, default=False)  # Flag to track if document is vectorized for RAG

    def __repr__(self):
        return f'<Document {self.filename}>'

class AISummary(db.Model):
    """Model for AI-generated summaries"""
    __tablename__ = 'ai_summaries'

    id = db.Column(db.Integer, primary_key=True)
    health_record_id = db.Column(db.Integer, db.ForeignKey('health_records.id'), nullable=False)
    summary_text = db.Column(db.Text, nullable=False)
    summary_type = db.Column(db.String(20), nullable=False, default='standard')  # standard, detailed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    health_record = db.relationship('HealthRecord', backref='summaries')

    def __repr__(self):
        return f'<AISummary for record {self.health_record_id}>'

# =============================================================================
# AI AUDIT MODELS
# =============================================================================

class AIAuditLog(db.Model):
    """
    Core audit log table for AI operations
    
    This table stores detailed audit information for all AI-related operations
    including chat interactions, summary generation, symptom checking, etc.
    """
    __tablename__ = 'ai_audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    
    # Basic audit information
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    session_id = db.Column(db.String(128), nullable=True, index=True)  # Track user sessions
    
    # Operation details
    operation_type = db.Column(db.String(50), nullable=False, index=True)  # chat, summarize, symptom_check, etc.
    operation_subtype = db.Column(db.String(50), nullable=True)  # detailed operation classification
    
    # Data classification and sensitivity
    data_classification = db.Column(db.String(20), nullable=False, default='PHI')  # PHI, PII, PUBLIC, INTERNAL
    sensitivity_level = db.Column(db.String(20), nullable=False, default='HIGH')  # LOW, MEDIUM, HIGH, CRITICAL
    
    # AI model information
    ai_model_used = db.Column(db.String(100), nullable=True)  # gemini-2.5-flash, gpt-4, etc.
    ai_model_version = db.Column(db.String(50), nullable=True)
    fallback_used = db.Column(db.Boolean, default=False)  # Was fallback model used?
    
    # Request/Response details
    input_size = db.Column(db.Integer, nullable=True)  # Input text/data size in characters
    output_size = db.Column(db.Integer, nullable=True)  # Output text size in characters
    processing_time_ms = db.Column(db.Integer, nullable=True)  # Processing time in milliseconds
    
    # Content classification
    medical_context_accessed = db.Column(db.Boolean, default=False)  # Was medical data accessed?
    pii_detected = db.Column(db.Boolean, default=False)  # Was PII detected in input/output?
    family_member_id = db.Column(db.Integer, db.ForeignKey('family_members.id'), nullable=True)  # Related family member
    health_record_ids = db.Column(db.Text, nullable=True)  # JSON array of accessed record IDs
    
    # Security and compliance
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4/IPv6 address
    user_agent = db.Column(db.String(500), nullable=True)  # Browser/client information
    geographic_location = db.Column(db.String(100), nullable=True)  # Country/region if available
    
    # Risk assessment
    risk_score = db.Column(db.Float, nullable=True)  # Calculated risk score (0-100)
    risk_factors = db.Column(db.Text, nullable=True)  # JSON array of risk factors
    
    # Compliance framework tracking
    hipaa_applicable = db.Column(db.Boolean, default=True)
    gdpr_applicable = db.Column(db.Boolean, default=False)
    soc2_applicable = db.Column(db.Boolean, default=True)
    nist_applicable = db.Column(db.Boolean, default=True)
    
    # Status and outcome
    operation_status = db.Column(db.String(20), nullable=False, default='SUCCESS')  # SUCCESS, FAILED, PARTIAL
    error_code = db.Column(db.String(50), nullable=True)  # Error code if operation failed
    error_message = db.Column(db.Text, nullable=True)  # Error details
    
    # Audit metadata
    retention_period_days = db.Column(db.Integer, nullable=False, default=2555)  # 7 years default
    archived = db.Column(db.Boolean, default=False)
    archive_date = db.Column(db.DateTime, nullable=True)
    
    # Additional context (JSON)
    additional_context = db.Column(db.Text, nullable=True)  # JSON blob for extensibility
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_ai_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_ai_audit_operation_timestamp', 'operation_type', 'timestamp'),
        Index('idx_ai_audit_classification', 'data_classification', 'sensitivity_level'),
        Index('idx_ai_audit_compliance', 'hipaa_applicable', 'gdpr_applicable', 'timestamp'),
        Index('idx_ai_audit_risk', 'risk_score', 'timestamp'),
        Index('idx_ai_audit_status', 'operation_status', 'timestamp'),
        Index('idx_ai_audit_session', 'session_id', 'timestamp'),
    )

    def __repr__(self):
        return f'<AIAuditLog {self.operation_type} for user {self.user_id} at {self.timestamp}>'


class AIComplianceReport(db.Model):
    """
    Compliance assessment reports for periodic auditing
    
    Stores periodic compliance reports and assessments for regulatory requirements
    """
    __tablename__ = 'ai_compliance_reports'

    id = db.Column(db.Integer, primary_key=True)
    
    # Report identification
    report_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    compliance_framework = db.Column(db.String(50), nullable=False, index=True)  # HIPAA, GDPR, SOC2, NIST
    
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
    violation_details = db.Column(db.Text, nullable=True)  # JSON array of violation details
    
    # Recommendations
    recommendations = db.Column(db.Text, nullable=True)  # JSON array of recommendations
    action_items = db.Column(db.Text, nullable=True)  # JSON array of required actions
    
    # Report metadata
    report_summary = db.Column(db.Text, nullable=True)
    executive_summary = db.Column(db.Text, nullable=True)
    detailed_findings = db.Column(db.Text, nullable=True)
    
    # Status tracking
    status = db.Column(db.String(20), nullable=False, default='DRAFT')  # DRAFT, FINAL, ARCHIVED
    generated_by = db.Column(db.String(100), nullable=True)  # System or user who generated
    reviewed_by = db.Column(db.String(100), nullable=True)  # Who reviewed the report
    approved_by = db.Column(db.String(100), nullable=True)  # Who approved the report
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    finalized_at = db.Column(db.DateTime, nullable=True)
    next_review_date = db.Column(db.DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_compliance_framework_period', 'compliance_framework', 'period_start', 'period_end'),
        Index('idx_compliance_score_status', 'compliance_score', 'status'),
        Index('idx_compliance_created', 'created_at'),
    )

    def __repr__(self):
        return f'<AIComplianceReport {self.report_id} for {self.compliance_framework}>'


class AIOperationMetrics(db.Model):
    """
    Performance and usage metrics aggregation
    
    Stores aggregated metrics for AI operations performance monitoring
    """
    __tablename__ = 'ai_operation_metrics'

    id = db.Column(db.Integer, primary_key=True)
    
    # Time aggregation
    metric_date = db.Column(db.Date, nullable=False, index=True)
    aggregation_period = db.Column(db.String(20), nullable=False, index=True)  # HOURLY, DAILY, WEEKLY, MONTHLY
    
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
    common_errors = db.Column(db.Text, nullable=True)  # JSON array of error codes/counts
    
    # Geographic distribution
    geographic_distribution = db.Column(db.Text, nullable=True)  # JSON object of location:count
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_metrics_date_type', 'metric_date', 'operation_type'),
        Index('idx_metrics_period_model', 'aggregation_period', 'ai_model_used'),
        Index('idx_metrics_performance', 'avg_processing_time_ms', 'error_rate'),
    )

    def __repr__(self):
        return f'<AIOperationMetrics {self.operation_type} for {self.metric_date}>'


class AISecurityEvent(db.Model):
    """
    Security-related AI events and incidents
    
    Tracks security events, anomalies, and potential threats in AI operations
    """
    __tablename__ = 'ai_security_events'

    id = db.Column(db.Integer, primary_key=True)
    
    # Event identification
    event_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)  # ANOMALY, THREAT, VIOLATION, BREACH
    severity = db.Column(db.String(20), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Related audit log
    audit_log_id = db.Column(db.Integer, db.ForeignKey('ai_audit_logs.id'), nullable=True, index=True)
    
    # Event details
    event_description = db.Column(db.Text, nullable=False)
    detection_method = db.Column(db.String(100), nullable=True)  # How was this detected?
    
    # Context
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    operation_type = db.Column(db.String(50), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    
    # Risk assessment
    risk_score = db.Column(db.Float, nullable=True)  # 0-100
    potential_impact = db.Column(db.String(500), nullable=True)
    affected_data_types = db.Column(db.Text, nullable=True)  # JSON array
    
    # Response tracking
    status = db.Column(db.String(20), nullable=False, default='OPEN')  # OPEN, INVESTIGATING, RESOLVED, CLOSED
    assigned_to = db.Column(db.String(100), nullable=True)
    response_actions = db.Column(db.Text, nullable=True)  # JSON array of actions taken
    resolution_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    detected_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    
    # Notification tracking
    notifications_sent = db.Column(db.Boolean, default=False)
    escalated = db.Column(db.Boolean, default=False)
    escalation_level = db.Column(db.Integer, nullable=True)  # 1, 2, 3, etc.
    
    # Indexes
    __table_args__ = (
        Index('idx_security_severity_status', 'severity', 'status'),
        Index('idx_security_type_detected', 'event_type', 'detected_at'),
        Index('idx_security_user_detected', 'user_id', 'detected_at'),
    )

    def __repr__(self):
        return f'<AISecurityEvent {self.event_id} - {self.event_type} ({self.severity})>'


class AIDataAccess(db.Model):
    """
    Detailed data access tracking for AI operations
    
    Tracks specific data access patterns for GDPR/HIPAA compliance
    """
    __tablename__ = 'ai_data_access'

    id = db.Column(db.Integer, primary_key=True)
    
    # Access identification
    access_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    audit_log_id = db.Column(db.Integer, db.ForeignKey('ai_audit_logs.id'), nullable=False, index=True)
    
    # Data identification
    data_type = db.Column(db.String(50), nullable=False, index=True)  # HEALTH_RECORD, FAMILY_MEMBER, USER_PROFILE
    data_id = db.Column(db.String(100), nullable=False, index=True)  # ID of the accessed data
    data_classification = db.Column(db.String(20), nullable=False, index=True)  # PHI, PII, PUBLIC
    
    # Access details
    access_purpose = db.Column(db.String(100), nullable=False, index=True)  # AI_CHAT, SUMMARIZATION, ANALYSIS
    access_method = db.Column(db.String(50), nullable=False)  # READ, PROCESS, ANALYZE
    data_fields_accessed = db.Column(db.Text, nullable=True)  # JSON array of specific fields
    
    # Data content summary
    data_size_chars = db.Column(db.Integer, nullable=True)  # Size of accessed data
    sensitive_data_detected = db.Column(db.Boolean, default=False)
    phi_categories = db.Column(db.Text, nullable=True)  # JSON array of PHI categories found
    
    # Legal basis (for GDPR compliance)
    legal_basis = db.Column(db.String(100), nullable=True)  # CONSENT, LEGITIMATE_INTEREST, etc.
    consent_id = db.Column(db.String(100), nullable=True)  # Reference to user consent
    
    # Data minimization
    data_necessary = db.Column(db.Boolean, default=True)  # Was this data necessary for the operation?
    alternative_available = db.Column(db.Boolean, default=False)  # Could operation work without this data?
    
    # Timestamps
    accessed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    data_last_modified = db.Column(db.DateTime, nullable=True)  # When was the accessed data last modified?
    
    # Retention and disposal
    retention_period_days = db.Column(db.Integer, nullable=False, default=2555)  # 7 years
    data_disposed = db.Column(db.Boolean, default=False)
    disposal_date = db.Column(db.DateTime, nullable=True)
    disposal_method = db.Column(db.String(50), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_data_access_type_id', 'data_type', 'data_id'),
        Index('idx_data_access_audit', 'audit_log_id', 'accessed_at'),
        Index('idx_data_access_classification', 'data_classification', 'accessed_at'),
        Index('idx_data_access_purpose', 'access_purpose', 'accessed_at'),
    )

    def __repr__(self):
        return f'<AIDataAccess {self.access_id} - {self.data_type}:{self.data_id}>'
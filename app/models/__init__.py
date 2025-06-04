from datetime import datetime, timedelta
import secrets
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

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
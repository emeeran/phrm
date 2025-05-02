from datetime import datetime
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

    # Relationships
    family_members = db.relationship('FamilyMember', secondary=user_family, backref='caregivers')
    records = db.relationship('HealthRecord', backref='user', lazy='dynamic')

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    records = db.relationship('HealthRecord', backref='family_member', lazy='dynamic')

    def __repr__(self):
        return f'<FamilyMember {self.first_name} {self.last_name}>'

class HealthRecord(db.Model):
    """Model for health records"""
    __tablename__ = 'health_records'

    id = db.Column(db.Integer, primary_key=True)
    record_type = db.Column(db.String(50), nullable=False)  # complaint, doctor_visit, investigation, prescription, lab_report, note
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    family_member_id = db.Column(db.Integer, db.ForeignKey('family_members.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = db.relationship('Document', backref='health_record', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<HealthRecord {self.title}>'

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
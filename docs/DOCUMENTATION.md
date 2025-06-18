# PHRM - Personal Health Record Manager
## Comprehensive Technical Documentation

### 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Configuration](#configuration)
5. [Database Design](#database-design)
6. [API Documentation](#api-documentation)
7. [AI Integration](#ai-integration)
8. [Security Features](#security-features)
9. [Development Guide](#development-guide)
10. [Testing](#testing)
11. [Deployment](#deployment)
12. [Troubleshooting](#troubleshooting)
13. [Contributing](#contributing)

---

## Project Overview

PHRM is a secure, production-ready Flask-based Personal Health Record Manager that enables users to manage their health records and those of their family members. The application features AI-powered medical assistance, document management, and comprehensive security measures.

### 🎯 Key Features
- **Secure Health Record Management**: Create, view, edit, and organize health records
- **Family Member Support**: Manage health records for family members
- **AI Medical Assistant**: Chat interface with medical AI models (MedGemma, GROQ, DeepSeek)
- **Local RAG System**: Enhanced AI responses using vectorized medical reference books
- **Document Storage**: Upload and manage medical documents with automatic OCR text extraction
- **AI Summarization**: Generate summaries of health records with reference context
- **Security-First Design**: Comprehensive security features and audit logging
- **Production Ready**: Optimized for production deployment with Docker support

### 🏗️ Technology Stack
- **Backend**: Flask 3.1+, Python 3.9+
- **Database**: SQLAlchemy with PostgreSQL/SQLite support
- **Vector Database**: ChromaDB for Local RAG functionality
- **Document Processing**: PyMuPDF for PDF text extraction
- **Caching**: Redis for session management and rate limiting
- **Security**: Flask-Talisman, bcrypt, CSRF protection
- **AI Integration**: Hugging Face Inference API, GROQ, DeepSeek
- **Frontend**: Jinja2 templates with modern CSS/JavaScript
- **Deployment**: Docker, Gunicorn, Nginx

---

## Architecture

### 🏛️ Application Structure

```
phrm/
├── app/                          # Main application package
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration classes
│   ├── ai/                      # AI functionality
│   │   ├── routes/              # AI route handlers
│   │   │   ├── chat.py         # Chat interface
│   │   │   └── summarization.py # Record summarization
│   │   └── summarization.py     # AI summarization logic
│   ├── api/                     # REST API endpoints
│   ├── auth/                    # Authentication & user management
│   ├── models/                  # Database models
│   │   ├── core/               # Core models (User, HealthRecord)
│   │   ├── ai_audit/           # AI audit & compliance
│   │   └── security/           # Security event logging
│   ├── records/                 # Health record management
│   │   ├── routes/             # Record route handlers
│   │   ├── forms.py            # WTForms definitions
│   │   ├── services.py         # Business logic
│   │   └── file_utils.py       # File handling utilities
│   ├── static/                  # Static assets (CSS, JS, images)
│   ├── templates/               # Jinja2 templates
│   └── utils/                   # Utility modules
├── migrations/                  # Database migrations
├── tests/                       # Test suite
├── uploads/                     # User uploaded files
└── instance/                    # Instance-specific files
```

### 🔧 Core Components

#### Flask App Factory Pattern
The application uses the Flask app factory pattern for better testability and configuration management:

```python
def create_app(config_name=None):
    app = Flask(__name__)
    _configure_app(app)
    _initialize_extensions(app)
    _configure_security(app)
    _register_blueprints(app)
    return app
```

#### Blueprint Organization
- **Auth Blueprint**: User authentication, registration, profile management
- **Records Blueprint**: Health record CRUD operations, family management
- **AI Blueprint**: AI chat interface and summarization
- **API Blueprint**: REST API endpoints for programmatic access

#### Database Models
- **User**: Authentication and profile information
- **FamilyMember**: Family member profiles
- **HealthRecord**: Core health record data
- **Document**: File attachments for records
- **AISummary**: AI-generated summaries
- **Security/Audit Models**: Security event logging and AI audit trails

---

## Installation & Setup

### 🚀 Quick Start

#### Prerequisites
- Python 3.9 or higher
- PostgreSQL (recommended for production) or SQLite (development)
- Redis (for caching and rate limiting)

#### 1. Clone and Install
```bash
git clone <repository-url>
cd phrm
uv sync
```

#### 2. Environment Configuration
Copy and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

#### 3. Database Setup
```bash
# Initialize database
flask db upgrade

# Create admin user (optional)
flask create-admin admin@example.com admin adminuser Admin User
```

#### 4. Run Development Server
```bash
python run.py
# Or use Flask's built-in server
flask run
```

#### 5. Local RAG Setup (Optional)
```bash
# Create reference books directory
mkdir -p reference_books

# Place PDF medical reference books in the directory
# Example: cp ~/medical-books/*.pdf reference_books/

# Process reference books for AI enhancement
./scripts/run_vectorization.sh
# Choose option 2 to vectorize books

# Verify RAG status
python scripts/rag_manager.py status
```

#### 6. Access Application
Open http://localhost:5000 in your browser.

### 🐳 Docker Setup

#### Development with Docker Compose
```bash
docker-compose up -d
```

#### Production Docker Deployment
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## Configuration

### 🔧 Environment Variables

#### Core Configuration
```bash
# Flask Configuration
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=development  # or production
DEBUG=false  # true for development

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/phrm
# Or for SQLite: sqlite:///phrm.db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Security Configuration
SESSION_COOKIE_SECURE=true  # Set to true in production with HTTPS
WTF_CSRF_TIME_LIMIT=3600
```

#### AI Provider Configuration
```bash
# Primary AI Provider (MedGemma via Hugging Face)
HUGGINGFACE_ACCESS_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
HUGGINGFACE_MODEL=google/medgemma-27b-text-it

# Secondary AI Provider (GROQ)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=deepseek-r1-distill-llama-70b

# Fallback AI Provider (DeepSeek)
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
DEEPSEEK_MODEL=deepseek-chat
```

#### Optional Configuration
```bash
# Email Configuration (for password reset)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# File Upload Configuration
MAX_CONTENT_LENGTH=16777216  # 16MB
UPLOAD_FOLDER=uploads

# Rate Limiting
RATELIMIT_DEFAULT=100 per hour
RATELIMIT_STORAGE_URL=redis://localhost:6379/0

# Local RAG Configuration
RAG_ISOLATED_MODE=false  # Set to true for standalone processing scripts
REFERENCE_BOOKS_PATH=reference_books  # Path to PDF reference books
```

### 📁 Configuration Classes

#### Development Configuration
```python
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = False
```

#### Production Configuration
```python
class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True
    # Enhanced security settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'max_overflow': 30,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
```

---

## Database Design

### 📊 Entity Relationship Diagram

#### Core Entities

**Users Table**
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email address
- `password_hash`: Bcrypt hashed password
- `first_name`, `last_name`: User name
- `date_of_birth`: Date of birth
- `created_at`, `updated_at`: Timestamps
- `is_admin`: Admin flag
- Notification preferences
- Security fields (reset tokens, etc.)

**Family Members Table**
- `id`: Primary key
- `name`: Family member name
- `relationship`: Relationship to user
- `date_of_birth`: Date of birth
- `medical_history`: Medical background
- `created_at`, `updated_at`: Timestamps

**Health Records Table**
- `id`: Primary key
- `user_id`: Foreign key to users
- `family_member_id`: Foreign key to family_members (optional)
- `date`: Record date
- `chief_complaint`: Main health concern
- `doctor`: Doctor/clinic information
- `investigations`: Tests and procedures
- `diagnosis`: Medical diagnosis
- `prescription`: Medications prescribed
- `notes`: Additional notes
- `review_followup`: Follow-up instructions
- `created_at`, `updated_at`: Timestamps

**Documents Table**
- `id`: Primary key
- `health_record_id`: Foreign key to health_records
- `filename`: Original filename
- `stored_filename`: Secure stored filename
- `file_path`: File storage path
- `file_size`: File size in bytes
- `content_type`: MIME type
- `uploaded_at`: Upload timestamp

#### Relationships
- Users can have multiple family members (Many-to-Many via user_family table)
- Users can have multiple health records (One-to-Many)
- Family members can have multiple health records (One-to-Many)
- Health records can have multiple documents (One-to-Many)
- Health records can have AI summaries (One-to-Many)

### 🔍 Database Indexes

#### Performance Indexes
```sql
-- User lookup indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- Health record indexes
CREATE INDEX idx_health_records_user_id ON health_records(user_id);
CREATE INDEX idx_health_records_date ON health_records(date DESC);
CREATE INDEX idx_health_records_family_member ON health_records(family_member_id);

-- Document indexes
CREATE INDEX idx_documents_record_id ON documents(health_record_id);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at DESC);
```

### 🔒 Security Considerations
- All user passwords are hashed using bcrypt
- Session data is stored in Redis with expiration
- File uploads are validated and stored with secure filenames
- Database queries use parameterized statements (SQLAlchemy ORM)
- Audit logging for all AI operations and security events

---

## API Documentation

### 🔌 REST API Endpoints

#### Authentication Required
All API endpoints require authentication via session cookies or API token.

#### Health Check
```
GET /api/v1/health
```
Returns application health status.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "uptime": 3600.5
}
```

#### User Information
```
GET /api/v1/user
```
Returns current user information.

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Health Records
```
GET /api/v1/records
POST /api/v1/records
GET /api/v1/records/{id}
PUT /api/v1/records/{id}
DELETE /api/v1/records/{id}
```

**GET /api/v1/records Response:**
```json
{
  "records": [
    {
      "id": 1,
      "date": "2024-01-15",
      "chief_complaint": "Headache",
      "doctor": "Dr. Smith",
      "diagnosis": "Tension headache",
      "family_member": {
        "id": 1,
        "name": "John Doe",
        "relationship": "self"
      },
      "documents": [
        {
          "id": 1,
          "filename": "lab_results.pdf",
          "uploaded_at": "2024-01-15T10:30:00Z"
        }
      ]
    }
  ],
  "total": 1,
  "page": 1,
  "pages": 1
}
```

#### Family Members
```
GET /api/v1/family
POST /api/v1/family
GET /api/v1/family/{id}
PUT /api/v1/family/{id}
DELETE /api/v1/family/{id}
```

#### AI Chat
```
POST /api/v1/ai/chat
```

**Request:**
```json
{
  "message": "What should I know about my recent blood pressure readings?",
  "mode": "general",
  "patient_id": 1
}
```

**Response:**
```json
{
  "response": "Based on your recent records, your blood pressure readings show...",
  "model_used": "medgemma",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 📝 Rate Limiting

#### Default Limits
- General API: 100 requests per hour
- Authentication: 10 requests per minute
- AI endpoints: 5 requests per minute
- File uploads: 30 requests per minute

#### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 3600
```

---

## AI Integration

### 🤖 AI Provider Architecture

#### Provider Hierarchy
1. **Primary**: MedGemma (via Hugging Face Inference API)
2. **Secondary**: GROQ (with medical models)
3. **Fallback**: DeepSeek (general purpose)

#### AI Capabilities
- **Medical Chat**: Interactive health consultations
- **Record Summarization**: AI-generated health record summaries
- **Symptom Analysis**: Symptom checker functionality
- **Health Insights**: Personalized health recommendations
- **Local RAG**: Enhanced responses using vectorized medical reference books

### 📚 Local RAG (Retrieval-Augmented Generation)

#### Overview
The Local RAG system enhances AI responses by providing context from vectorized medical reference books. This allows the AI to give more accurate, evidence-based medical information.

#### Features
- **PDF Vectorization**: Automatic processing of medical reference books
- **Semantic Search**: Find relevant medical content for user queries
- **Context Integration**: Seamlessly integrate reference content into AI responses
- **Separate Processing**: Vectorization runs independently from app startup
- **Process Isolation**: Safe concurrent operation with the main application

#### Setup Process
1. **Add Reference Books**: Place PDF medical references in `reference_books/` directory
2. **Run Vectorization**: Use `./scripts/run_vectorization.sh` for interactive setup
3. **Verify Status**: Check processing status via dashboard or CLI tools
4. **Enhanced AI**: AI responses automatically include relevant reference context

#### Management Commands
```bash
# Interactive management
./scripts/run_vectorization.sh

# Command-line management
python scripts/rag_manager.py status
python scripts/rag_manager.py vectorize
python scripts/rag_manager.py refresh
python scripts/rag_manager.py clean
python scripts/rag_manager.py test
```

#### Technical Architecture
- **Vector Database**: ChromaDB for semantic similarity search
- **Text Processing**: PyMuPDF for PDF text extraction
- **Isolation**: Separate vector stores for app vs standalone processing
- **API Integration**: RESTful endpoints for RAG management
- **Background Processing**: Non-blocking vectorization with progress tracking

### 🔧 Configuration

#### MedGemma Setup
1. Request access to MedGemma models on Hugging Face
2. Generate Hugging Face access token
3. Configure environment variables:
```bash
HUGGINGFACE_ACCESS_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
HUGGINGFACE_MODEL=google/medgemma-27b-text-it
```

#### Provider Fallback Logic
```python
def call_ai_with_fallback(system_message, user_message):
    try:
        # Try MedGemma first
        return call_medgemma_api(system_message, user_message)
    except Exception:
        try:
            # Fallback to GROQ
            return call_groq_api(system_message, user_message)
        except Exception:
            # Final fallback to DeepSeek
            return call_deepseek_api(system_message, user_message)
```

### 🛡️ AI Security Features

#### Input Validation
- User input sanitization
- Content length limits
- Suspicious pattern detection
- Rate limiting per user

#### Output Processing
- Response content filtering
- Medical disclaimer injection
- Audit logging
- Security headers

#### Privacy Protection
- No model fine-tuning on user data
- Remote-only API calls
- Data minimization
- Audit trail maintenance

### 📊 AI Audit & Compliance

#### Audit Logging
```python
class AIAuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    operation_type = db.Column(db.String(50))  # chat, summarize, analyze
    input_content = db.Column(db.Text)  # Hashed for privacy
    model_used = db.Column(db.String(100))
    response_length = db.Column(db.Integer)
    processing_time = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
```

#### Compliance Features
- HIPAA-conscious design
- Data retention policies
- User consent tracking
- Audit report generation

---

## Security Features

### 🔒 Authentication & Authorization

#### User Authentication
- **Session-based authentication** with Flask-Login
- **Password hashing** with bcrypt (12 rounds)
- **Password reset** functionality with secure tokens
- **Remember me** functionality with secure cookies
- **Session timeout** configurable per environment

#### Authorization Levels
- **Regular Users**: Manage own and family records
- **Admin Users**: System administration capabilities
- **API Access**: Token-based authentication for API endpoints

### 🛡️ Security Headers & CSRF Protection

#### Flask-Talisman Configuration
```python
talisman.init_app(app,
    force_https=True,  # Production only
    strict_transport_security=True,
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline' cdn.jsdelivr.net",
        'style-src': "'self' 'unsafe-inline' fonts.googleapis.com",
        'font-src': "'self' fonts.gstatic.com",
        'img-src': "'self' data:",
    }
)
```

#### CSRF Protection
- All forms protected with CSRF tokens
- 1-hour token lifetime
- Automatic token regeneration
- AJAX support with meta tag tokens

### 🚫 Rate Limiting

#### Endpoint-Specific Limits
```python
# Authentication endpoints
@limiter.limit("10 per minute")
def login():
    pass

# AI endpoints
@limiter.limit("5 per minute")
def ai_chat():
    pass

# File uploads
@limiter.limit("30 per minute")
def upload_file():
    pass
```

#### Rate Limiting Storage
- **Redis-based** storage for production
- **In-memory** fallback for development
- **User-specific** rate limiting when authenticated
- **IP-based** rate limiting for anonymous users

### 📋 Input Validation & Sanitization

#### Form Validation
```python
class RecordForm(FlaskForm, SecurityValidationMixin):
    chief_complaint = TextAreaField(
        validators=[Optional(), Length(max=2000)]
    )

    def validate_chief_complaint(self, field):
        if field.data:
            # Check for suspicious patterns
            if detect_suspicious_patterns(field.data):
                raise ValidationError("Invalid content detected")
            # Sanitize HTML content
            field.data = sanitize_html(field.data)
```

#### File Upload Security
```python
def validate_file_security(file):
    # Check file extension
    if not allowed_file(file.filename):
        raise ValidationError("File type not allowed")

    # Check file size
    if len(file.read()) > current_app.config['MAX_CONTENT_LENGTH']:
        raise ValidationError("File too large")

    # Reset file pointer
    file.seek(0)

    # Scan file content (implement virus scanning if needed)
    return True
```

### 🔍 Security Event Logging

#### Security Event Types
- Failed login attempts
- Password changes
- Admin actions
- Suspicious activity detection
- File access attempts
- AI model usage

#### Event Logging
```python
def log_security_event(event_type, details):
    security_event = SecurityEvent(
        user_id=current_user.id if current_user.is_authenticated else None,
        event_type=event_type,
        details=json.dumps(details),
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        timestamp=datetime.utcnow()
    )
    db.session.add(security_event)
    db.session.commit()
```

---

## Development Guide

### 🛠️ Development Environment Setup

#### Local Development
```bash
# Clone repository
git clone <repository-url>
cd phrm

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
uv sync
uv sync --group dev  # Development dependencies

# Setup pre-commit hooks
pre-commit install

# Configure environment
cp .env.example .env
# Edit .env with development settings

# Initialize database
flask db upgrade

# Run development server
python run.py
```

#### Development Dependencies
```bash
# Code formatting and linting
black==23.12.1
isort==5.13.2
flake8==7.0.0
mypy==1.8.0

# Testing
pytest==7.4.4
pytest-flask==1.3.0
pytest-cov==4.0.0

# Pre-commit hooks
pre-commit==3.6.0
```

### 🏗️ Code Organization Principles

#### Module Structure
- **Blueprints**: Organize routes by functionality
- **Models**: Database models in logical groups
- **Utils**: Reusable utility functions
- **Services**: Business logic layer
- **Forms**: WTForms definitions

#### Naming Conventions
- **Classes**: PascalCase (e.g., `HealthRecord`)
- **Functions**: snake_case (e.g., `create_health_record`)
- **Variables**: snake_case (e.g., `user_id`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_FILE_SIZE`)
- **Templates**: kebab-case (e.g., `health-records.html`)

#### Import Organization
```python
# Standard library imports
import os
from datetime import datetime

# Third-party imports
from flask import Flask, request
from sqlalchemy import text

# Local imports
from .models import User, HealthRecord
from .utils import sanitize_html
```

### 🧪 Testing Strategy

#### Test Structure
```
tests/
├── unit/                    # Unit tests
│   ├── test_models.py      # Model tests
│   ├── test_forms.py       # Form validation tests
│   └── test_utils.py       # Utility function tests
├── integration/            # Integration tests
│   ├── test_auth_workflows.py
│   └── test_record_workflows.py
├── performance/            # Performance tests
│   └── test_database_performance.py
└── fixtures/               # Test data fixtures
```

#### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

#### Test Configuration
```python
# conftest.py
@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def user(app):
    user = User(username='testuser', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user
```

### 📝 Code Quality Tools

#### Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
```

#### Type Checking with mypy
```bash
# Run type checking
mypy app/

# Configuration in pyproject.toml
[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

---

## Testing

### 🧪 Test Suite Overview

#### Test Categories
1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **Performance Tests**: Test application performance
4. **Security Tests**: Test security features

#### Test Tools
- **pytest**: Primary testing framework
- **pytest-flask**: Flask-specific testing utilities
- **pytest-cov**: Coverage reporting
- **Factory Boy**: Test data generation
- **responses**: HTTP request mocking

### 🔧 Test Configuration

#### Test Database
```python
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
```

#### Test Fixtures
```python
@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def authenticated_user(client):
    """Create and login a test user"""
    user = User(username='testuser', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True

    return user
```

### 📊 Test Examples

#### Model Tests
```python
def test_user_password_hashing():
    user = User(username='test', email='test@example.com')
    user.set_password('password123')

    assert user.password_hash is not None
    assert user.check_password('password123')
    assert not user.check_password('wrongpassword')

def test_health_record_creation():
    user = User(username='test', email='test@example.com')
    db.session.add(user)
    db.session.commit()

    record = HealthRecord(
        user_id=user.id,
        date=date.today(),
        chief_complaint='Test complaint'
    )
    db.session.add(record)
    db.session.commit()

    assert record.id is not None
    assert record.user_id == user.id
```

#### Route Tests
```python
def test_login_required_redirect(client):
    response = client.get('/records/dashboard')
    assert response.status_code == 302
    assert '/auth/login' in response.location

def test_successful_login(client):
    user = User(username='test', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()

    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 302
```

#### AI Integration Tests
```python
@responses.activate
def test_ai_chat_fallback():
    # Mock MedGemma API failure
    responses.add(
        responses.POST,
        'https://api-inference.huggingface.co/models/google/medgemma-27b-text-it',
        status=503
    )

    # Mock GROQ API success
    responses.add(
        responses.POST,
        'https://api.groq.com/openai/v1/chat/completions',
        json={'choices': [{'message': {'content': 'Test response'}}]},
        status=200
    )

    response = call_ai_with_fallback("System", "User message")
    assert response == "Test response"
```

### 📈 Coverage Requirements
- **Minimum Coverage**: 80%
- **Critical Paths**: 95% (authentication, security, data handling)
- **Exclusions**: Migration files, configuration files

#### Running Coverage
```bash
# Generate coverage report
pytest --cov=app --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Coverage configuration in pyproject.toml
[tool.coverage.run]
source = ["app"]
omit = ["migrations/*", "tests/*", "venv/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError"
]
```

---

## Deployment

### 🚀 Production Deployment Options

#### Option 1: Docker Deployment (Recommended)

**Prerequisites:**
- Docker and Docker Compose installed
- Domain name configured
- SSL certificates (Let's Encrypt recommended)

**Deployment Steps:**
```bash
# Clone repository
git clone <repository-url>
cd phrm

# Configure production environment
cp .env.production.example .env.production
# Edit .env.production with production values

# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Initialize database
docker-compose exec app flask db upgrade

# Create admin user
docker-compose exec app flask create-admin admin@yourdomain.com admin adminuser "Admin User"
```

**Production Docker Compose:**
```yaml
version: '3.8'
services:
  app:
    build: .
    environment:
      - DATABASE_URL=postgresql://phrm:${DB_PASSWORD}@db:5432/phrm
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=phrm
      - POSTGRES_USER=phrm
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

#### Option 2: Traditional Server Deployment

**Server Requirements:**
- Ubuntu 20.04+ or CentOS 8+
- 2GB+ RAM
- PostgreSQL 12+
- Redis 6+
- Nginx
- Python 3.9+

**Installation Steps:**
```bash
# Install system dependencies
sudo apt update
sudo apt install python3.9 python3.9-venv python3.9-dev postgresql postgresql-contrib redis-server nginx

# Create application user
sudo useradd -m -s /bin/bash phrm
sudo su - phrm

# Clone and setup application
git clone <repository-url> /home/phrm/app
cd /home/phrm/app
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Configure environment
cp .env.production.example .env
# Edit .env with production values

# Setup database
sudo -u postgres createuser phrm
sudo -u postgres createdb phrm -O phrm
sudo -u postgres psql -c "ALTER USER phrm PASSWORD 'secure_password';"

# Initialize application database
flask db upgrade

# Create systemd service
sudo cp systemd/phrm.service /etc/systemd/system/
sudo systemctl enable phrm
sudo systemctl start phrm

# Configure Nginx
sudo cp nginx/phrm.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/phrm.conf /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

### 🔧 Production Configuration

#### Environment Variables
```bash
# Core Configuration
SECRET_KEY=generate-a-strong-secret-key-here
FLASK_ENV=production
DEBUG=false

# Database
DATABASE_URL=postgresql://phrm:password@localhost:5432/phrm

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SESSION_COOKIE_SECURE=true
WTF_CSRF_TIME_LIMIT=3600

# AI Providers
HUGGINGFACE_ACCESS_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx

# Email (optional)
MAIL_SERVER=smtp.yourdomain.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=noreply@yourdomain.com
MAIL_PASSWORD=email_password

# Monitoring (optional)
SENTRY_DSN=your_sentry_dsn_here
```

#### Nginx Configuration
```nginx
upstream phrm_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.com.pem;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

    # Static files
    location /static {
        alias /home/phrm/app/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # File uploads (protected)
    location /uploads {
        internal;
        alias /home/phrm/app/uploads;
    }

    # API rate limiting
    location /api {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://phrm_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Login rate limiting
    location /auth/login {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://phrm_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Main application
    location / {
        proxy_pass http://phrm_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
```

#### Systemd Service
```ini
[Unit]
Description=PHRM Gunicorn Application
After=network.target postgresql.service redis.service

[Service]
User=phrm
Group=phrm
WorkingDirectory=/home/phrm/app
Environment=PATH=/home/phrm/app/venv/bin
ExecStart=/home/phrm/app/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 --timeout 120 --keep-alive 2 --max-requests 1000 --max-requests-jitter 100 run:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always

[Install]
WantedBy=multi-user.target
```

### 📊 Monitoring & Maintenance

#### Health Checks
```bash
# Application health check
curl -f http://localhost:8000/health

# Database connection check
sudo -u postgres psql -c "SELECT 1;" phrm

# Redis check
redis-cli ping
```

#### Log Management
```bash
# Application logs
tail -f /home/phrm/app/logs/app.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Systemd service logs
journalctl -u phrm -f
```

#### Backup Strategy
```bash
#!/bin/bash
# Database backup script
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U phrm phrm | gzip > /backups/phrm_db_$DATE.sql.gz

# File backup
tar -czf /backups/phrm_files_$DATE.tar.gz /home/phrm/app/uploads

# Retention (keep 30 days)
find /backups -name "phrm_*" -mtime +30 -delete
```

### 🔄 Updates & Maintenance

#### Application Updates
```bash
# Backup before update
sudo systemctl stop phrm
cp -r /home/phrm/app /home/phrm/app.backup

# Update application
cd /home/phrm/app
git pull origin main
source venv/bin/activate
pip install -r requirements.txt

# Run migrations
flask db upgrade

# Restart services
sudo systemctl start phrm
sudo systemctl reload nginx
```

#### Security Updates
```bash
# System updates
sudo apt update && sudo apt upgrade

# Python package updates
pip list --outdated
pip install --upgrade <package_name>

# Monitor security advisories
pip-audit
```

---

## Troubleshooting

### 🐛 Common Issues & Solutions

#### Database Connection Issues

**Issue**: `SQLALCHEMY_DATABASE_URI` not found
```
sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgresql
```

**Solutions:**
```bash
# Install PostgreSQL adapter
pip install psycopg2-binary

# Check database connection
psql -h localhost -U phrm -d phrm -c "SELECT 1;"

# Verify environment variables
echo $DATABASE_URL
```

#### Redis Connection Issues

**Issue**: Redis connection failures
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379. Connection refused.
```

**Solutions:**
```bash
# Check Redis service
sudo systemctl status redis
sudo systemctl start redis

# Test Redis connection
redis-cli ping

# Check Redis configuration
redis-cli CONFIG GET "*"
```

#### AI Provider Issues

**Issue**: Hugging Face API access denied
```
HTTPError: 403 Client Error: Forbidden for url: https://api-inference.huggingface.co/models/google/medgemma-27b-text-it
```

**Solutions:**
```bash
# Verify token access
python check_medgemma_token.py

# Check token permissions on Hugging Face
# Visit: https://huggingface.co/settings/tokens

# Test API access
curl -H "Authorization: Bearer $HUGGINGFACE_ACCESS_TOKEN" \
     https://api-inference.huggingface.co/models/google/medgemma-27b-text-it
```

#### File Upload Issues

**Issue**: File upload size exceeded
```
RequestEntityTooLarge: The data value transmitted exceeds the capacity limit.
```

**Solutions:**
```python
# Increase upload limit in config
MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB

# Check Nginx client_max_body_size
client_max_body_size 32m;

# Verify disk space
df -h /home/phrm/app/uploads
```

#### Performance Issues

**Issue**: Slow database queries
```
# Enable query logging
SQLALCHEMY_ECHO = True

# Check slow queries
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

**Solutions:**
```sql
-- Add missing indexes
CREATE INDEX idx_health_records_user_date ON health_records(user_id, date DESC);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM health_records WHERE user_id = 1;

-- Update table statistics
ANALYZE health_records;
```

#### Memory Issues

**Issue**: Application consuming too much memory
```bash
# Monitor memory usage
ps aux | grep gunicorn
htop

# Check for memory leaks
valgrind --tool=memcheck python run.py
```

**Solutions:**
```python
# Optimize Gunicorn configuration
--workers 2 --max-requests 1000 --max-requests-jitter 100

# Add SQLAlchemy optimizations
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 5,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}

# Enable garbage collection
import gc
gc.collect()
```

### 📋 Debug Mode

#### Enable Debug Logging
```python
# In development
import logging
logging.basicConfig(level=logging.DEBUG)

# Flask debug mode
FLASK_ENV=development
DEBUG=true
```

#### Database Debug Mode
```python
# Enable SQL query logging
SQLALCHEMY_ECHO = True

# Log slow queries
SQLALCHEMY_RECORD_QUERIES = True
```

#### AI Debug Mode
```python
# Test AI providers
python test_medgemma.py

# Debug AI responses
logger.setLevel(logging.DEBUG)
```

### 🔍 Log Analysis

#### Common Log Patterns
```bash
# Authentication failures
grep "Failed login" /var/log/phrm/app.log

# AI API failures
grep "AI API Error" /var/log/phrm/app.log

# Database errors
grep "SQLAlchemy" /var/log/phrm/app.log

# Rate limiting triggers
grep "Rate limit exceeded" /var/log/phrm/app.log
```

#### Log Monitoring Setup
```bash
# Install log monitoring
sudo apt install logwatch

# Configure logrotate
sudo vim /etc/logrotate.d/phrm

# Monitor logs in real-time
tail -f /var/log/phrm/app.log | grep ERROR
```

---

## Contributing

### 🤝 Contribution Guidelines

#### Getting Started
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Write tests for new functionality
5. Ensure all tests pass: `pytest`
6. Run code quality checks: `pre-commit run --all-files`
7. Submit a pull request

#### Code Standards
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Maintain test coverage above 80%
- Use meaningful variable and function names

#### Commit Messages
```
feat: add new health record export functionality
fix: resolve database connection timeout issue
docs: update installation instructions
test: add integration tests for AI chat
refactor: optimize database query performance
```

#### Pull Request Process
1. Ensure your PR description clearly describes the problem and solution
2. Include the relevant issue number if applicable
3. Ensure all CI checks pass
4. Request review from maintainers
5. Address any feedback from code review

#### Development Setup for Contributors
```bash
# Fork and clone your fork
git clone https://github.com/yourusername/phrm.git
cd phrm

# Add upstream remote
git remote add upstream https://github.com/original/phrm.git

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: your feature description"

# Push to your fork
git push origin feature/your-feature-name
```

#### Testing Requirements
- All new features must include tests
- Bug fixes must include regression tests
- Integration tests for API endpoints
- Security tests for authentication features

#### Documentation Requirements
- Update relevant documentation for new features
- Include docstrings for all public methods
- Update API documentation for new endpoints
- Add configuration examples for new settings

---

## Appendix

### 📚 Additional Resources

#### External Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Hugging Face API Documentation](https://huggingface.co/docs/api-inference/)
- [GROQ API Documentation](https://console.groq.com/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

#### Security Resources
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.0.x/security/)
- [HIPAA Compliance Guidelines](https://www.hhs.gov/hipaa/for-professionals/security/index.html)

#### Performance Resources
- [Flask Performance Tips](https://flask.palletsprojects.com/en/2.0.x/deploying/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Redis Performance Best Practices](https://redis.io/documentation)

### 🔖 Quick Reference

#### Useful Commands
```bash
# Development
python run.py                    # Start development server
flask db migrate                 # Create migration
flask db upgrade                 # Apply migration
pytest --cov=app                # Run tests with coverage

# Production
docker-compose up -d             # Start production stack
systemctl restart phrm          # Restart application service
nginx -t && systemctl reload nginx  # Test and reload Nginx

# Database
flask shell                      # Open Flask shell
pg_dump phrm > backup.sql       # Backup database
psql phrm < backup.sql          # Restore database

# Monitoring
journalctl -u phrm -f           # Follow application logs
htop                            # Monitor system resources
redis-cli monitor               # Monitor Redis commands
```

#### Configuration Templates
```bash
# Development .env
SECRET_KEY=dev-secret-key
DEBUG=true
DATABASE_URL=sqlite:///phrm.db
REDIS_URL=redis://localhost:6379/0

# Production .env
SECRET_KEY=secure-production-key
DEBUG=false
DATABASE_URL=postgresql://user:pass@localhost/phrm
REDIS_URL=redis://localhost:6379/0
SESSION_COOKIE_SECURE=true
```

### 📞 Support

For technical support, bug reports, or feature requests:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section
- Contact maintainers

---

*This documentation is continuously updated. Last updated: June 2025*

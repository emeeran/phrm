# Personal Health Record Manager (PHRM) v2.0

## Overview
PHRM is a Flask-based web application for managing personal health records, featuring AI-powered chat, symptom checking, document summarization, and web-enhanced AI responses. The system supports multiple AI providers with intelligent fallback logic and robust error handling.

## Key Features
- **Personal Health Records**: Secure storage and management of medical data
- **AI-Powered Chat**: Medical question answering with multiple AI providers
- **Web-Enhanced AI**: Real-time web search integration via Google Search API (Serper)
- **Document Processing**: PDF upload and AI summarization with OCR
- **Family Records**: Multi-user health record management
- **Public Mode**: Anonymous access with hidden patient selector
- **Demo Mode**: Fallback system when APIs are unavailable

## AI Provider System
- **Primary Providers:** GROQ, DeepSeek
- **Fallback Providers:** OpenAI, Claude (optional)
- **Enhanced with:** Google Search via Serper API for real-time medical information
- **Demo Mode:** Simulated responses when all providers are unavailable

## Quick Start

### Option 1: Using Makefile (Recommended)
```bash
make setup    # Setup database and sample data
make run      # Start the application
```

### Option 2: Manual Setup
1. **Setup Database and Sample Data:**
   ```bash
   python setup_database.py
   ```

2. **Run the Application:**
   ```bash
   python start_phrm.py
   ```

3. **Access the Application:**
   - Open: http://localhost:5000
   - Demo Login: `demo@example.com` / `demo123`

## Installation and Setup

### Prerequisites
- Python 3.10 or higher
- UV package manager (recommended) or pip

### 1. Install Dependencies
```bash
# Using UV (recommended)
uv sync

# Or using pip
pip install -e .
```

### 2. Environment Configuration
Create a `.env` file with your API keys:

```env
# Primary AI Providers
GROQ_API_KEY=gsk_...
DEEPSEEK_API_KEY=sk-...

# Web Search Enhancement
SERPER_API_KEY=your_serper_api_key

# Optional AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

### 3. Database Setup
```bash
python setup_database.py
```

### 4. Start the Application
```bash
# Development mode
python start_phrm.py

# Or with debug mode
FLASK_ENV=development python start_phrm.py

# Production mode with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```
## Redis Setup (Optional)
Redis improves performance by providing:
- **Rate limiting storage**: Better than in-memory for production
- **Session caching**: Faster user session management
- **General caching**: Improved response times

### Installation & Usage
- **Start Redis**: `./scripts/start-redis.sh`
- **Stop Redis**: `./scripts/stop-redis.sh`
- **Check Status**: `redis-cli ping` (should return "PONG")

The application automatically detects Redis availability and falls back to in-memory storage if Redis is not running.

## Development

### Available Commands
```bash
make help     # Show all available commands
make setup    # Initialize database and sample data
make run      # Start the application
make dev      # Start with debug mode and auto-reload
make test     # Run test suite
make clean    # Clean cache and temporary files
make install  # Install dependencies
```

### Project Structure
```
phrm/
├── app/                    # Main application package
│   ├── ai/                # AI chat and summarization
│   ├── api/               # API endpoints
│   ├── appointments/      # Appointment management
│   ├── auth/              # Authentication system
│   ├── models/            # Database models
│   ├── records/           # Health records management
│   ├── static/            # CSS, JS, images
│   ├── templates/         # Jinja2 templates
│   └── utils/             # Utility modules
├── docs/                  # Documentation
├── scripts/               # Utility scripts
├── migrations/            # Database migrations
└── instance/              # Database and uploads
```

## Core Features

### 🤖 AI Chat System
- **Multi-Provider Support**: GROQ, DeepSeek, OpenAI, Claude
- **Intelligent Fallback**: Automatic provider switching on failures
- **Web Enhancement**: Real-time Google Search integration
- **Demo Mode**: Graceful degradation when APIs unavailable
- **Context Awareness**: Patient-specific medical context

### 📋 Health Records
- **Comprehensive Records**: Demographics, medications, allergies, conditions
- **Document Management**: PDF upload with OCR text extraction
- **AI Summarization**: Automated record analysis and insights
- **Family Support**: Multi-user records with relationship management
- **Secure Access**: Role-based permissions and audit logging

### 🔍 Document Processing
- **PDF OCR**: Automatic text extraction from uploaded documents
- **AI Analysis**: Intelligent document summarization
- **Caching**: Smart cache system for instant retrieval
- **Security**: Secure file upload and storage

### 🌐 Public Access
- **Anonymous Mode**: Public access without patient data
- **Hidden Controls**: Patient selector automatically hidden
- **General Medical Chat**: AI assistance without personal context

## API Integration

### AI Providers
Configure multiple AI providers for redundancy:

```python
# Primary providers
GROQ_API_KEY=gsk_...        # Fast inference, good quality
DEEPSEEK_API_KEY=sk-...     # High quality reasoning

# Optional providers
OPENAI_API_KEY=sk-...       # GPT models
ANTHROPIC_API_KEY=sk-...    # Claude models
```

### Web Search
Enhance AI responses with real-time web data:

```python
SERPER_API_KEY=your_key     # Google Search via Serper API
```

## Testing
- **Health Check**: `curl http://localhost:5000/health`
- **System Status**: Available in dashboard after login
- **Test Scripts**: Run specific feature tests in `scripts/`

## Production Deployment

### 1. Environment Setup
```bash
# Production dependencies
uv sync --no-dev

# Copy production environment
cp .env.example .env
# Edit .env with production keys
```

### 2. Database Configuration
```bash
# Use PostgreSQL for production
pip install psycopg2-binary

# Update database URL in .env
DATABASE_URL=postgresql://user:pass@localhost/phrm
```

### 3. Web Server
```bash
# Using Gunicorn (recommended)
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"

# With process management
./start_with_env.sh
```

### 4. Reverse Proxy
Configure Nginx or Apache for:
- HTTPS termination
- Static file serving
- Load balancing
- Security headers

## Security Features
- **Authentication**: Flask-Login with secure sessions
- **Authorization**: Role-based access control
- **CSRF Protection**: Flask-WTF CSRF tokens
- **Rate Limiting**: Configurable API rate limits
- **Audit Logging**: Comprehensive activity tracking
- **File Security**: Safe upload handling and validation

## Performance Optimizations
- **Caching**: Redis or in-memory caching
- **Rate Limiting**: Intelligent request throttling
- **Database**: Optimized queries and indexing
- **Static Files**: Efficient serving and compression
- **AI Responses**: Smart caching and fallback logic

## Maintenance

### Dependency Updates
```bash
# Update all dependencies
uv sync --upgrade

# Check for security issues
uv audit
```

### Database Maintenance
```bash
# Run migrations
flask db upgrade

# Create new migration
flask db migrate -m "Description"
```

### Health Monitoring
- Monitor `/health` endpoint
- Check logs for AI provider failures
- Monitor Redis performance (if used)
- Review rate limiting metrics

## Troubleshooting

### Common Issues
1. **AI Provider Errors**: Check API keys and quotas
2. **Database Errors**: Verify connection and migrations
3. **Upload Failures**: Check file permissions and disk space
4. **Redis Connection**: Verify Redis service status

### Debugging
```bash
# Enable debug mode
export FLASK_ENV=development

# Check logs
tail -f logs/phrm.log

# Test AI providers
python scripts/test_ai_providers.py
```

## License
MIT License - see LICENSE file for details.

## Support
- Documentation: `/docs` directory
- Health Check: `/health` endpoint
- System Status: Available in application dashboard

"""
Production Deployment Configuration for PHRM
Optimized settings for production environment with security, performance, and monitoring.
"""

import os
from datetime import timedelta
from typing import ClassVar


class ProductionConfig:
    """Production configuration with optimized settings."""

    # Basic Flask Configuration
    SECRET_KEY = os.environ.get("SECRET_KEY") or "your-super-secret-production-key-here"

    # Database Configuration
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or "sqlite:///phrm_production.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS: ClassVar[dict[str, int | bool]] = {
        "pool_size": 20,
        "pool_timeout": 20,
        "pool_recycle": -1,
        "max_overflow": 0,
        "pool_pre_ping": True,
    }

    # Redis Cache Configuration
    REDIS_URL = os.environ.get("REDIS_URL") or "redis://localhost:6379/0"
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_KEY_PREFIX = "phrm:"

    # Session Configuration
    SESSION_TYPE = "redis"
    SESSION_REDIS = REDIS_URL
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = "phrm:session:"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # Security Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # Rate Limiting Configuration
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = "1000 per hour"
    RATELIMIT_HEADERS_ENABLED = True

    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or "/opt/phrm/uploads"
    ALLOWED_EXTENSIONS: ClassVar[set[str]] = {
        "txt",
        "pdf",
        "png",
        "jpg",
        "jpeg",
        "gif",
        "doc",
        "docx",
    }

    # Email Configuration (for notifications)
    MAIL_SERVER = os.environ.get("MAIL_SERVER") or "smtp.gmail.com"
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "on", "1"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # Logging Configuration
    LOG_LEVEL = "INFO"
    LOG_FILE = "/var/log/phrm/app.log"
    LOG_MAX_BYTES = 10485760  # 10MB
    LOG_BACKUP_COUNT = 10

    # Performance Configuration
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(seconds=31536000)  # 1 year for static files

    # AI/ML Configuration
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    AI_MODEL = "gpt-3.5-turbo"
    AI_MAX_TOKENS = 1000
    AI_TEMPERATURE = 0.7

    # Monitoring Configuration
    PERFORMANCE_MONITORING = True
    METRICS_ENABLED = True
    HEALTH_CHECK_ENABLED = True

    # Security Headers
    SECURITY_HEADERS: ClassVar[dict[str, str]] = {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;",
    }

    # Asset Optimization
    OPTIMIZE_ASSETS = True
    MINIFY_PAGE = True
    COMPRESS_MIMETYPES: ClassVar[list[str]] = [
        "text/html",
        "text/css",
        "text/xml",
        "application/json",
        "application/javascript",
    ]


class DockerConfig(ProductionConfig):
    """Docker-specific configuration."""

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or "postgresql://phrm:password@db:5432/phrm"
    )
    REDIS_URL = os.environ.get("REDIS_URL") or "redis://redis:6379/0"

    # Docker-specific paths
    UPLOAD_FOLDER = "/app/uploads"
    LOG_FILE = "/app/logs/app.log"


def create_production_dockerfile() -> str:
    """Generate optimized Dockerfile for production."""
    dockerfile_content = """# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    libpq5 \\
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app user
RUN groupadd -r phrm && useradd -r -g phrm phrm

# Create directories
RUN mkdir -p /app/uploads /app/logs && \\
    chown -R phrm:phrm /app

# Copy application
COPY . /app
WORKDIR /app

# Set ownership
RUN chown -R phrm:phrm /app

# Switch to non-root user
USER phrm

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "gevent", "--worker-connections", "1000", "--max-requests", "1000", "--max-requests-jitter", "100", "--timeout", "30", "--keep-alive", "5", "app:create_app()"]
"""
    return dockerfile_content


def create_docker_compose() -> str:
    """Generate Docker Compose for production deployment."""
    compose_content = """version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://phrm:password@db:5432/phrm
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=phrm
      - POSTGRES_USER=phrm
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U phrm"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./app/static:/var/www/static
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
"""
    return compose_content


def create_nginx_config() -> str:
    """Generate optimized Nginx configuration."""
    nginx_config = """events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Performance settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

    # Upstream
    upstream app {
        server app:8000;
    }

    # HTTP server (redirects to HTTPS)
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name _;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Static files
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # API endpoints with rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Login endpoints with stricter rate limiting
        location /auth/login {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Application
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
    }
}
"""
    return nginx_config


def create_systemd_service() -> str:
    """Generate systemd service file for production deployment."""
    service_content = """[Unit]
Description=PHRM Personal Health Record Manager
After=network.target

[Service]
Type=exec
User=phrm
Group=phrm
WorkingDirectory=/opt/phrm
Environment=FLASK_ENV=production
Environment=DATABASE_URL=sqlite:///opt/phrm/data/phrm.db
Environment=REDIS_URL=redis://localhost:6379/0
ExecStart=/opt/phrm/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 4 --worker-class gevent app:create_app()
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    return service_content


def create_monitoring_config() -> dict:
    """Create monitoring and alerting configuration."""
    monitoring_config = {
        "health_checks": [
            {
                "name": "database",
                "endpoint": "/health/db",
                "timeout": 5,
                "critical": True,
            },
            {
                "name": "redis",
                "endpoint": "/health/redis",
                "timeout": 3,
                "critical": False,
            },
            {"name": "api", "endpoint": "/health/api", "timeout": 10, "critical": True},
        ],
        "metrics": [
            "response_time",
            "error_rate",
            "throughput",
            "memory_usage",
            "cpu_usage",
            "disk_usage",
            "database_connections",
            "cache_hit_rate",
        ],
        "alerts": {
            "response_time_threshold": 2.0,  # seconds
            "error_rate_threshold": 0.05,  # 5%
            "memory_usage_threshold": 0.85,  # 85%
            "disk_usage_threshold": 0.90,  # 90%
        },
    }
    return monitoring_config


# Export configurations
production_configs = {
    "dockerfile": create_production_dockerfile(),
    "docker_compose": create_docker_compose(),
    "nginx_config": create_nginx_config(),
    "systemd_service": create_systemd_service(),
    "monitoring": create_monitoring_config(),
}

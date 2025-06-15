import os
from datetime import timedelta
from typing import Any, ClassVar, Optional


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a secret from environment variables"""
    return os.environ.get(key, default)


class Config:
    """Base configuration class"""

    SECRET_KEY = get_secret("SECRET_KEY", "dev-key-for-development-only")
    # Use SQLALCHEMY_DATABASE_URI if set, else fallback to DATABASE_URL, else default
    SQLALCHEMY_DATABASE_URI = get_secret(
        "SQLALCHEMY_DATABASE_URI", get_secret("DATABASE_URL", "sqlite:///phrm.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Security Settings
    SESSION_COOKIE_SECURE = (
        os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true"
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour CSRF token lifetime

    # Rate Limiting Configuration
    RATELIMIT_STORAGE_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
    RATELIMIT_DEFAULT = "100 per hour"

    # Logging Configuration
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get("LOG_FILE", "logs/app.log")

    # Cache Configuration
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "SimpleCache")
    CACHE_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes

    # Hugging Face API Configuration (Primary Provider for MedGemma)
    HUGGINGFACE_ACCESS_TOKEN = os.environ.get("HUGGINGFACE_ACCESS_TOKEN")
    HUGGINGFACE_MODEL = os.environ.get(
        "HUGGINGFACE_MODEL", "google/medgemma-27b-text-it"
    )  # Use 27B text-only as default
    HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/"

    # GROQ API Configuration (Secondary Provider)
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "deepseek-r1-distill-llama-70b")
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

    # DEEPSEEK API Configuration (Fallback Provider)
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
    DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

    # Default AI Model Settings
    DEFAULT_AI_MODEL = "google/medgemma-4b-it"
    DEFAULT_AI_PROVIDER = "huggingface"

    # Pinecone Configuration for RAG
    PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT", "us-west1-gcp")

    # Health Check Configuration
    HEALTH_CHECK_PATH = "/health"


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    SQLALCHEMY_ECHO = True

    # Disable HTTPS forcing in development
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    TESTING = False

    # Security - Override base settings for production
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SESSION_COOKIE_SECURE = True  # Force HTTPS cookies
    WTF_CSRF_ENABLED = True

    # Database - Use SQLALCHEMY_DATABASE_URI if set, else fallback to DATABASE_URL
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI"
    ) or os.environ.get("DATABASE_URL")
    SQLALCHEMY_ENGINE_OPTIONS: ClassVar[dict[str, Any]] = {
        "pool_size": 20,
        "max_overflow": 30,
        "pool_recycle": 3600,  # 1 hour
        "pool_pre_ping": True,
        "pool_timeout": 30,
        "echo": False,
        "connect_args": (
            {"options": "-c timezone=utc"}  # Set timezone for PostgreSQL
            if (
                os.environ.get("SQLALCHEMY_DATABASE_URI")
                or os.environ.get("DATABASE_URL")
                or ""
            ).startswith("postgresql")
            else {}
        ),
    }

    # SQLite optimizations for development/testing
    if not (
        os.environ.get("SQLALCHEMY_DATABASE_URI") or os.environ.get("DATABASE_URL")
    ) or "sqlite" in (
        os.environ.get("SQLALCHEMY_DATABASE_URI")
        or os.environ.get("DATABASE_URL")
        or ""
    ):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_recycle": 300,
            "pool_pre_ping": True,
            "pool_timeout": 20,
            "echo": False,
        }

    # Use Redis for rate limiting in production
    RATELIMIT_STORAGE_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Database optimization settings
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_QUERY_TIMEOUT = 30

    # Enable database optimization features
    ENABLE_DATABASE_OPTIMIZATION = True
    ENABLE_QUERY_LOGGING = (
        os.environ.get("ENABLE_QUERY_LOGGING", "false").lower() == "true"
    )

    # Strict rate limiting in production
    RATELIMIT_DEFAULT = "60 per hour"

    # Production logging
    LOG_LEVEL = "WARNING"

    # Use Redis for caching in production
    CACHE_TYPE = "RedisCache"

    # Backup configuration
    BACKUP_ENABLED = os.environ.get("BACKUP_ENABLED", "true").lower() == "true"
    BACKUP_DIRECTORY = os.environ.get("BACKUP_DIRECTORY", "/var/backups/phrm")
    BACKUP_RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS", "30"))


# Configuration dictionary
config_dict = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config() -> Any:
    """Return the appropriate configuration object based on the environment."""
    config_name = os.environ.get("FLASK_ENV", "default")
    return config_dict.get(config_name, config_dict["default"])

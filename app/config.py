import os
from datetime import timedelta

def get_secret(key, default=None):
    """Get a secret from environment variables"""
    return os.environ.get(key, default)

class Config:
    """Base configuration class"""
    SECRET_KEY = get_secret('SECRET_KEY', 'dev-key-for-development-only')
    SQLALCHEMY_DATABASE_URI = get_secret('DATABASE_URL', 'sqlite:///phrm.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Security Settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour CSRF token lifetime
    
    # Rate Limiting Configuration
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    
    # Cache Configuration
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'SimpleCache')
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes

    # OpenAI API Configuration
    OPENAI_API_KEY = get_secret('OPENAI_API_KEY')

    # Gemini API Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash-preview-05-20')
    USE_OPENAI_FALLBACK = os.environ.get('USE_OPENAI_FALLBACK', 'True').lower() == 'true'

    # Default AI Model Settings
    DEFAULT_AI_MODEL = "llama3"

    # Pinecone Configuration for RAG
    PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
    PINECONE_ENVIRONMENT = os.environ.get('PINECONE_ENVIRONMENT', 'us-west1-gcp')
    
    # Health Check Configuration
    HEALTH_CHECK_PATH = '/health'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Security - Override base settings for production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_SECURE = True  # Force HTTPS cookies
    WTF_CSRF_ENABLED = True
    
    # Database - Use PostgreSQL in production with optimization
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'max_overflow': 30,
        'pool_recycle': 3600,  # 1 hour
        'pool_pre_ping': True,
        'pool_timeout': 30,
        'echo': False,
        'connect_args': {
            'options': '-c timezone=utc'  # Set timezone for PostgreSQL
        } if os.environ.get('DATABASE_URL', '').startswith('postgresql') else {}
    }
    
    # SQLite optimizations for development/testing
    if not os.environ.get('DATABASE_URL') or 'sqlite' in os.environ.get('DATABASE_URL', ''):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 5,
            'max_overflow': 10,
            'pool_recycle': 300,
            'pool_pre_ping': True,
            'pool_timeout': 20,
            'echo': False
        }
    
    # Database optimization settings
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_QUERY_TIMEOUT = 30
    
    # Enable database optimization features
    ENABLE_DATABASE_OPTIMIZATION = True
    ENABLE_QUERY_LOGGING = os.environ.get('ENABLE_QUERY_LOGGING', 'false').lower() == 'true'
    
    # Strict rate limiting in production
    RATELIMIT_DEFAULT = "60 per hour"
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Use Redis for caching in production
    CACHE_TYPE = 'RedisCache'
    
    # Backup configuration
    BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'true').lower() == 'true'
    BACKUP_DIRECTORY = os.environ.get('BACKUP_DIRECTORY', '/var/backups/phrm')
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', '30'))

# Configuration dictionary
config_dict = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Return the appropriate configuration object based on the environment."""
    config_name = os.environ.get('FLASK_ENV', 'default')
    return config_dict.get(config_name, config_dict['default'])
import os
from datetime import timedelta
try:
    from doppler.client import DopplerClient
    doppler_available = True
except ImportError:
    doppler_available = False

def get_doppler_secret(key, default=None):
    """Get a secret from Doppler if available, or from environment variable"""
    if doppler_available:
        try:
            client = DopplerClient()
            return client.get_secret(key).value
        except Exception as e:
            # Fallback to environment variable
            print(f"Warning: Doppler SDK failed: {e}. Falling back to environment variables.")
            return os.environ.get(key, default)
    return os.environ.get(key, default)

class Config:
    """Base configuration class"""
    SECRET_KEY = get_doppler_secret('SECRET_KEY', 'dev-key-for-development-only')
    SQLALCHEMY_DATABASE_URI = get_doppler_secret('DATABASE_URL', 'sqlite:///phrm.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # OpenAI API Configuration - Using Doppler
    OPENAI_API_KEY = get_doppler_secret('OPENAI_API_KEY')

    # Gemini API Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-1.5-pro')
    USE_OPENAI_FALLBACK = os.environ.get('USE_OPENAI_FALLBACK', 'True').lower() == 'true'

    # Default AI Model Settings
    DEFAULT_AI_MODEL = "llama3"

    # Pinecone Configuration for RAG
    PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
    PINECONE_ENVIRONMENT = os.environ.get('PINECONE_ENVIRONMENT', 'us-west1-gcp')

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
    # Use strong secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Use PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

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
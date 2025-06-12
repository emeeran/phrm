"""
Optimized configuration management for the Personal Health Record Manager.
Consolidates configuration logic and provides caching for better performance.
"""

import os
from datetime import timedelta
from functools import lru_cache
from typing import Any, Dict, Optional


@lru_cache(maxsize=1)
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get secret from environment with caching"""
    return os.environ.get(key, default)


@lru_cache(maxsize=1)
def get_database_config() -> Dict[str, Any]:
    """Get database configuration with optimizations"""
    # Use SQLALCHEMY_DATABASE_URI if set, else fallback to DATABASE_URL, else default
    database_uri = (
        get_secret("SQLALCHEMY_DATABASE_URI")
        or get_secret("DATABASE_URL")
        or "sqlite:///phrm.db"
    )

    config = {
        "SQLALCHEMY_DATABASE_URI": database_uri,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "pool_pre_ping": True,
            "pool_recycle": 300,
        },
    }

    # SQLite-specific optimizations
    if database_uri.startswith("sqlite"):
        engine_options = config["SQLALCHEMY_ENGINE_OPTIONS"]
        if isinstance(engine_options, dict):
            engine_options.update(
                {"connect_args": {"check_same_thread": False, "timeout": 20}}
            )

    return config


@lru_cache(maxsize=1)
def get_security_config() -> Dict[str, Any]:
    """Get security configuration"""
    return {
        "SECRET_KEY": get_secret("SECRET_KEY", "dev-key-for-development-only"),
        "SESSION_COOKIE_SECURE": (
            get_secret("SESSION_COOKIE_SECURE", "False") or "False"
        ).lower()
        == "true",
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "WTF_CSRF_TIME_LIMIT": 3600,  # 1 hour CSRF token lifetime
        "PERMANENT_SESSION_LIFETIME": timedelta(days=7),
    }


@lru_cache(maxsize=1)
def get_ai_config() -> Dict[str, Any]:
    """Get AI-related configuration"""
    return {
        # Hugging Face Configuration
        "HUGGINGFACE_API_KEY": get_secret("HUGGINGFACE_API_KEY"),
        "HUGGINGFACE_MODEL": get_secret("HUGGINGFACE_MODEL", "google/medgemma-4b-it"),
        "HUGGINGFACE_API_URL": "https://api-inference.huggingface.co/models/",
        # GROQ API Configuration
        "GROQ_API_KEY": get_secret("GROQ_API_KEY"),
        "GROQ_MODEL": get_secret("GROQ_MODEL", "deepseek-r1-distill-llama-70b"),
        "GROQ_API_URL": "https://api.groq.com/openai/v1/chat/completions",
        # DEEPSEEK API Configuration (Fallback Provider)
        "DEEPSEEK_API_KEY": get_secret("DEEPSEEK_API_KEY"),
        "DEEPSEEK_MODEL": get_secret("DEEPSEEK_MODEL", "deepseek-chat"),
        "DEEPSEEK_API_URL": "https://api.deepseek.com/chat/completions",
        # Default AI Model Settings
        "DEFAULT_AI_MODEL": "google/medgemma-4b-it",
        "DEFAULT_AI_PROVIDER": "huggingface",
        # Pinecone Configuration for RAG
        "PINECONE_API_KEY": get_secret("PINECONE_API_KEY"),
        "PINECONE_ENVIRONMENT": get_secret("PINECONE_ENVIRONMENT", "us-west1-gcp"),
    }


@lru_cache(maxsize=1)
def get_upload_config() -> Dict[str, Any]:
    """Get file upload configuration"""
    upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    return {
        "UPLOAD_FOLDER": upload_folder,
        "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,  # 16MB max upload
    }


@lru_cache(maxsize=1)
def get_rate_limiting_config() -> Dict[str, Any]:
    """Get rate limiting configuration"""
    return {
        "RATELIMIT_STORAGE_URL": get_secret("REDIS_URL", "redis://localhost:6379"),
        "RATELIMIT_DEFAULT": "1000 per hour",
    }


@lru_cache(maxsize=1)
def get_caching_config() -> Dict[str, Any]:
    """Get caching configuration"""
    cache_type = "redis" if get_secret("REDIS_URL") else "simple"

    config = {
        "CACHE_TYPE": cache_type,
        "CACHE_DEFAULT_TIMEOUT": 300,  # 5 minutes
    }

    if cache_type == "redis":
        config["CACHE_REDIS_URL"] = get_secret("REDIS_URL")

    return config


class Config:
    """Optimized base configuration class"""

    def __init__(self) -> None:
        # Combine all configuration sections
        self.update_from_dict(get_database_config())
        self.update_from_dict(get_security_config())
        self.update_from_dict(get_ai_config())
        self.update_from_dict(get_upload_config())
        self.update_from_dict(get_rate_limiting_config())
        self.update_from_dict(get_caching_config())

        # Health Check Configuration
        self.HEALTH_CHECK_PATH = "/health"

        # Performance optimizations
        self.SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=12)

        # Development settings
        self.DEBUG = (get_secret("FLASK_DEBUG", "False") or "False").lower() == "true"
        self.TESTING = False

    def update_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Update configuration from dictionary"""
        for key, value in config_dict.items():
            setattr(self, key, value)


class DevelopmentConfig(Config):
    """Development configuration"""

    def __init__(self) -> None:
        super().__init__()
        self.DEBUG = True
        self.SESSION_COOKIE_SECURE = False
        self.WTF_CSRF_ENABLED = True


class ProductionConfig(Config):
    """Production configuration"""

    def __init__(self) -> None:
        super().__init__()
        self.DEBUG = False
        self.SESSION_COOKIE_SECURE = True
        self.WTF_CSRF_ENABLED = True

        # Enhanced security for production
        self.PERMANENT_SESSION_LIFETIME = timedelta(
            hours=2
        )  # Shorter session in production


class TestingConfig(Config):
    """Testing configuration"""

    def __init__(self) -> None:
        super().__init__()
        self.TESTING = True
        self.DEBUG = True
        self.WTF_CSRF_ENABLED = False
        self.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


# Configuration mapping
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


@lru_cache(maxsize=1)
def get_config(config_name: Optional[str] = None) -> Config:
    """Get configuration instance with caching"""
    if config_name is None:
        config_name = get_secret("FLASK_ENV", "development") or "development"

    config_class = config_map.get(config_name, config_map["default"])
    return config_class()


def clear_config_cache() -> None:
    """Clear configuration cache (useful for testing)"""
    get_config.cache_clear()
    get_secret.cache_clear()
    get_database_config.cache_clear()
    get_security_config.cache_clear()
    get_ai_config.cache_clear()
    get_upload_config.cache_clear()
    get_rate_limiting_config.cache_clear()
    get_caching_config.cache_clear()


# ============================================================================
# CONFIG MANAGER CLASS
# ============================================================================


class ConfigManager:
    """Configuration manager class for centralized config access"""

    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with caching"""
        if key in self._cache:
            return self._cache[key]

        # Get from environment
        value = os.environ.get(key, default)
        self._cache[key] = value
        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self._cache[key] = value
        os.environ[key] = str(value)

    def clear_cache(self) -> None:
        """Clear configuration cache"""
        self._cache.clear()

    def get_database_uri(self) -> str:
        """Get database URI"""
        return str(self.get("SQLALCHEMY_DATABASE_URI", "sqlite:///phrm.db"))

    def get_secret_key(self) -> str:
        """Get Flask secret key"""
        return str(self.get("SECRET_KEY", "dev-secret-change-in-production"))

    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return str(self.get("DEBUG", "False")).lower() in ("true", "1", "yes")

    def get_upload_folder(self) -> str:
        """Get upload folder path"""
        return str(self.get("UPLOAD_FOLDER", "uploads"))


# Global config manager instance
config_manager = ConfigManager()

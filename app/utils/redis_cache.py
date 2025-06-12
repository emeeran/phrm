"""
Redis Cache Configuration and Management for PHRM
Provides Redis-based caching for improved performance in production environments.
"""

import json
import logging
import pickle
from functools import wraps
from typing import Any, Optional

import redis

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache manager with fallback to in-memory cache."""

    def __init__(self, app=None) -> None:
        self.redis_client = None
        self.fallback_cache = {}
        self.is_redis_available = False

        if app:
            self.init_app(app)

    def init_app(self, app) -> None:
        """Initialize Redis cache with Flask app."""
        try:
            redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                health_check_interval=30,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )

            # Test Redis connection
            self.redis_client.ping()
            self.is_redis_available = True
            logger.info("Redis cache initialized successfully")

        except Exception as e:
            logger.warning(f"Redis unavailable, using fallback cache: {e}")
            self.is_redis_available = False

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            if self.is_redis_available and self.redis_client:
                value = self.redis_client.get(key)
                if value is not None:
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        # Try pickle for complex objects
                        return pickle.loads(value.encode('latin-1'))
                return default
            else:
                return self.fallback_cache.get(key, default)

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return self.fallback_cache.get(key, default)

    def set(self, key: str, value: Any, timeout: int = 300) -> bool:
        """Set value in cache with timeout."""
        try:
            if self.is_redis_available and self.redis_client:
                try:
                    serialized_value = json.dumps(value)
                except (TypeError, ValueError):
                    # Use pickle for complex objects
                    serialized_value = pickle.dumps(value).decode('latin-1')

                return bool(self.redis_client.setex(key, timeout, serialized_value))
            else:
                self.fallback_cache[key] = value
                return True

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self.fallback_cache[key] = value
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if self.is_redis_available and self.redis_client:
                return bool(self.redis_client.delete(key))
            else:
                return self.fallback_cache.pop(key, None) is not None

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def clear(self) -> bool:
        """Clear all cache."""
        try:
            if self.is_redis_available and self.redis_client:
                return bool(self.redis_client.flushdb())
            else:
                self.fallback_cache.clear()
                return True

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if self.is_redis_available and self.redis_client:
                return bool(self.redis_client.exists(key))
            else:
                return key in self.fallback_cache

        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    def get_stats(self) -> dict:
        """Get cache statistics."""
        if self.is_redis_available and self.redis_client:
            try:
                info = self.redis_client.info()
                return {
                    'type': 'redis',
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory': info.get('used_memory', 0),
                    'used_memory_human': info.get('used_memory_human', '0B'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0)
                }
            except Exception as e:
                logger.error(f"Error getting Redis stats: {e}")

        return {
            'type': 'fallback',
            'keys_count': len(self.fallback_cache),
            'available': self.is_redis_available
        }


# Global cache instance
cache = RedisCache()


def cached(timeout: int = 300, key_prefix: str = "phrm"):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__module__, func.__name__]
            if args:
                key_parts.extend([str(arg) for arg in args])
            if kwargs:
                key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])

            cache_key = ":".join(key_parts)

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result

        return wrapper
    return decorator


class CacheManager:
    """Advanced cache management with patterns and batch operations."""

    @staticmethod
    def cache_user_data(user_id: int, data: dict, timeout: int = 600):
        """Cache user-specific data."""
        key = f"user:{user_id}:data"
        return cache.set(key, data, timeout)

    @staticmethod
    def get_user_data(user_id: int) -> Optional[dict]:
        """Get cached user data."""
        key = f"user:{user_id}:data"
        return cache.get(key)

    @staticmethod
    def invalidate_user_cache(user_id: int):
        """Invalidate all cache for a user."""
        if cache.is_redis_available and cache.redis_client:
            try:
                keys = cache.redis_client.keys(f"user:{user_id}:*")
                if keys:
                    cache.redis_client.delete(*keys)
                return True
            except Exception as e:
                logger.error(f"Error invalidating user cache: {e}")
        else:
            # Fallback for in-memory cache
            keys_to_delete = [k for k in cache.fallback_cache.keys() if k.startswith(f"user:{user_id}:")]
            for key in keys_to_delete:
                cache.delete(key)
        return False

    @staticmethod
    def cache_health_records(user_id: int, records: list, timeout: int = 300):
        """Cache health records for a user."""
        key = f"health_records:{user_id}"
        return cache.set(key, records, timeout)

    @staticmethod
    def get_health_records(user_id: int) -> Optional[list]:
        """Get cached health records."""
        key = f"health_records:{user_id}"
        return cache.get(key)

    @staticmethod
    def cache_ai_response(prompt_hash: str, response: dict, timeout: int = 1800):
        """Cache AI responses to avoid duplicate API calls."""
        key = f"ai_response:{prompt_hash}"
        return cache.set(key, response, timeout)

    @staticmethod
    def get_ai_response(prompt_hash: str) -> Optional[dict]:
        """Get cached AI response."""
        key = f"ai_response:{prompt_hash}"
        return cache.get(key)


def configure_redis_for_production():
    """Configure Redis for production deployment."""
    config = {
        'REDIS_URL': 'redis://localhost:6379/0',
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': 'redis://localhost:6379/0',
        'CACHE_DEFAULT_TIMEOUT': 300,
        'CACHE_KEY_PREFIX': 'phrm:',

        # Redis connection pool settings
        'REDIS_CONNECTION_POOL': {
            'max_connections': 20,
            'retry_on_timeout': True,
            'health_check_interval': 30,
            'socket_connect_timeout': 5,
            'socket_timeout': 5
        }
    }

    return config


def setup_redis_monitoring():
    """Setup Redis monitoring and alerts."""
    def check_redis_health():
        """Check Redis health and log metrics."""
        stats = cache.get_stats()

        if stats.get('type') == 'redis':
            memory_usage = stats.get('used_memory', 0)
            hit_rate = 0

            hits = stats.get('keyspace_hits', 0)
            misses = stats.get('keyspace_misses', 0)

            if hits + misses > 0:
                hit_rate = hits / (hits + misses) * 100

            logger.info(f"Redis Stats - Memory: {stats.get('used_memory_human', '0B')}, "
                       f"Hit Rate: {hit_rate:.2f}%, Clients: {stats.get('connected_clients', 0)}")

            # Alert on low hit rate
            if hit_rate < 50 and hits + misses > 100:
                logger.warning(f"Low Redis hit rate: {hit_rate:.2f}%")

            # Alert on high memory usage (>1GB)
            if memory_usage > 1024 * 1024 * 1024:
                logger.warning(f"High Redis memory usage: {stats.get('used_memory_human', '0B')}")

        return stats

    return check_redis_health


# Initialize cache manager
cache_manager = CacheManager()

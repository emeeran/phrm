"""
Unified Cache Management System for PHRM
Consolidates Redis and performance monitoring cache functionality
"""

import functools
import hashlib
import logging
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Union

import click
import psutil
from flask import current_app, g, request

logger = logging.getLogger(__name__)

# Thread-safe locks
cache_lock = threading.Lock()
metrics_lock = threading.Lock()

# Performance metrics storage
performance_metrics = defaultdict(list)
query_metrics = defaultdict(list)
template_metrics = defaultdict(list)
cache_stats = defaultdict(lambda: {"hits": 0, "misses": 0, "operations": 0, "errors": 0})

# Configuration constants
DEFAULT_TIMEOUT = 300
MAX_CACHE_SIZE = 1000
MAX_METRIC_ENTRIES = 500
CACHE_HIT_THRESHOLD = 0.7
RECOMMENDED_QUERY_THRESHOLD = 0.1
RECOMMENDED_TEMPLATE_THRESHOLD = 0.05


class UnifiedCacheManager:
    """
    Unified cache management system with Redis backend and in-memory fallback.
    Includes performance monitoring and advanced cache operations.
    """
    
    def __init__(self, app=None):
        self.redis_client = None
        self.redis_available = False
        self.fallback_cache = {}
        self.app = app
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        self._setup_redis()
        app.extensions['unified_cache'] = self
    
    def _setup_redis(self):
        """Setup Redis connection with fallback handling"""
        try:
            import redis
            from urllib.parse import urlparse
            
            redis_url = self.app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            
            if redis_url.startswith('redis://'):
                parsed = urlparse(redis_url)
                self.redis_client = redis.Redis(
                    host=parsed.hostname or 'localhost',
                    port=parsed.port or 6379,
                    db=int(parsed.path.lstrip('/')) if parsed.path else 0,
                    password=parsed.password,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
            else:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
            
            # Test connection
            self.redis_client.ping()
            self.redis_available = True
            logger.info("✅ Redis cache connected successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable, using in-memory fallback: {e}")
            self.redis_available = False
            self.redis_client = None
    
    # ========================================================================
    # CORE CACHE OPERATIONS
    # ========================================================================
    
    def get(self, key: str, default=None) -> Any:
        """Get value from cache with automatic fallback"""
        with cache_lock:
            cache_stats[key]["operations"] += 1
            
            try:
                if self.redis_available and self.redis_client:
                    value = self.redis_client.get(key)
                    if value is not None:
                        cache_stats[key]["hits"] += 1
                        try:
                            import json
                            return json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            return value
                    else:
                        cache_stats[key]["misses"] += 1
                        return default
                else:
                    # Fallback to in-memory cache
                    if key in self.fallback_cache:
                        entry = self.fallback_cache[key]
                        if entry['expires'] > time.time():
                            cache_stats[key]["hits"] += 1
                            return entry['value']
                        else:
                            del self.fallback_cache[key]
                    
                    cache_stats[key]["misses"] += 1
                    return default
                    
            except Exception as e:
                logger.error(f"Cache get error for key '{key}': {e}")
                cache_stats[key]["errors"] += 1
                return default
    
    def set(self, key: str, value: Any, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """Set value in cache with automatic fallback"""
        with cache_lock:
            cache_stats[key]["operations"] += 1
            
            try:
                if self.redis_available and self.redis_client:
                    import json
                    serialized_value = json.dumps(value) if not isinstance(value, str) else value
                    result = self.redis_client.setex(key, timeout, serialized_value)
                    return bool(result)
                else:
                    # Fallback to in-memory cache
                    self._cleanup_expired_entries()
                    
                    if len(self.fallback_cache) >= MAX_CACHE_SIZE:
                        self._evict_oldest_entry()
                    
                    self.fallback_cache[key] = {
                        'value': value,
                        'expires': time.time() + timeout,
                        'created': time.time()
                    }
                    return True
                    
            except Exception as e:
                logger.error(f"Cache set error for key '{key}': {e}")
                cache_stats[key]["errors"] += 1
                return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with cache_lock:
            try:
                if self.redis_available and self.redis_client:
                    result = self.redis_client.delete(key)
                    return bool(result)
                else:
                    if key in self.fallback_cache:
                        del self.fallback_cache[key]
                        return True
                    return False
                    
            except Exception as e:
                logger.error(f"Cache delete error for key '{key}': {e}")
                return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if self.redis_available and self.redis_client:
                return bool(self.redis_client.exists(key))
            else:
                if key in self.fallback_cache:
                    entry = self.fallback_cache[key]
                    if entry['expires'] > time.time():
                        return True
                    else:
                        del self.fallback_cache[key]
                return False
                
        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries"""
        try:
            if self.redis_available and self.redis_client:
                self.redis_client.flushdb()
            else:
                self.fallback_cache.clear()
            
            # Clear cache stats
            cache_stats.clear()
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    # ========================================================================
    # ADVANCED CACHE OPERATIONS
    # ========================================================================
    
    def get_or_set(self, key: str, callable_or_value, timeout: int = DEFAULT_TIMEOUT) -> Any:
        """Get value from cache, or set it if not found"""
        value = self.get(key)
        if value is None:
            if callable(callable_or_value):
                value = callable_or_value()
            else:
                value = callable_or_value
            self.set(key, value, timeout)
        return value
    
    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""
        result = {}
        for key in keys:
            result[key] = self.get(key)
        return result
    
    def mset(self, mapping: Dict[str, Any], timeout: int = DEFAULT_TIMEOUT) -> bool:
        """Set multiple values in cache"""
        success = True
        for key, value in mapping.items():
            if not self.set(key, value, timeout):
                success = False
        return success
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        deleted = 0
        try:
            if self.redis_available and self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted = self.redis_client.delete(*keys)
            else:
                import fnmatch
                keys_to_delete = [
                    key for key in self.fallback_cache.keys()
                    if fnmatch.fnmatch(key, pattern)
                ]
                for key in keys_to_delete:
                    del self.fallback_cache[key]
                    deleted += 1
            
            return deleted
            
        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        total_hits = sum(stats["hits"] for stats in cache_stats.values())
        total_misses = sum(stats["misses"] for stats in cache_stats.values())
        total_ops = total_hits + total_misses
        hit_ratio = total_hits / total_ops if total_ops > 0 else 0
        
        memory_info = {}
        if not self.redis_available:
            import sys
            memory_info = {
                "fallback_cache_size": len(self.fallback_cache),
                "fallback_cache_memory": sys.getsizeof(self.fallback_cache)
            }
        
        return {
            "redis_available": self.redis_available,
            "total_operations": total_ops,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "hit_ratio": hit_ratio,
            "total_errors": sum(stats["errors"] for stats in cache_stats.values()),
            "unique_keys": len(cache_stats),
            **memory_info
        }
    
    # ========================================================================
    # SPECIALIZED CACHE METHODS
    # ========================================================================
    
    def cache_user_data(self, user_id: int, data: Dict, timeout: int = 600) -> bool:
        """Cache user-specific data"""
        key = f"user:{user_id}:data"
        return self.set(key, data, timeout)
    
    def get_user_data(self, user_id: int) -> Optional[Dict]:
        """Get cached user data"""
        key = f"user:{user_id}:data"
        return self.get(key)
    
    def invalidate_user_cache(self, user_id: int) -> int:
        """Invalidate all cache for a user"""
        pattern = f"user:{user_id}:*"
        return self.delete_pattern(pattern)
    
    def cache_health_records(self, user_id: int, records: List, timeout: int = 300) -> bool:
        """Cache health records for a user"""
        key = f"health_records:{user_id}"
        return self.set(key, records, timeout)
    
    def get_health_records(self, user_id: int) -> Optional[List]:
        """Get cached health records"""
        key = f"health_records:{user_id}"
        return self.get(key)
    
    def cache_ai_response(self, prompt_hash: str, response: Dict, timeout: int = 1800) -> bool:
        """Cache AI responses to avoid duplicate API calls"""
        key = f"ai_response:{prompt_hash}"
        return self.set(key, response, timeout)
    
    def get_ai_response(self, prompt_hash: str) -> Optional[Dict]:
        """Get cached AI response"""
        key = f"ai_response:{prompt_hash}"
        return self.get(key)
    
    def cache_query_result(self, query_hash: str, result: Any, timeout: int = 900) -> bool:
        """Cache database query results"""
        key = f"query:{query_hash}"
        return self.set(key, result, timeout)
    
    def get_query_result(self, query_hash: str) -> Any:
        """Get cached query result"""
        key = f"query:{query_hash}"
        return self.get(key)
    
    # ========================================================================
    # PERFORMANCE MONITORING
    # ========================================================================
    
    def track_performance(self, operation: str, duration: float, metadata: Dict = None):
        """Track performance metrics"""
        with metrics_lock:
            metric_entry = {
                "operation": operation,
                "duration": duration,
                "timestamp": datetime.now(timezone.utc),
                "metadata": metadata or {}
            }
            
            performance_metrics[operation].append(metric_entry)
            
            # Limit metric storage
            if len(performance_metrics[operation]) > MAX_METRIC_ENTRIES:
                performance_metrics[operation] = performance_metrics[operation][-MAX_METRIC_ENTRIES:]
    
    def track_query(self, query: str, duration: float, parameters: Dict = None):
        """Track database query performance"""
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        
        with metrics_lock:
            query_entry = {
                "query": query,
                "query_hash": query_hash,
                "duration": duration,
                "parameters": parameters,
                "timestamp": datetime.now(timezone.utc)
            }
            
            query_metrics[query_hash].append(query_entry)
            
            if len(query_metrics[query_hash]) > MAX_METRIC_ENTRIES:
                query_metrics[query_hash] = query_metrics[query_hash][-MAX_METRIC_ENTRIES:]
    
    def track_template(self, template: str, duration: float, context_size: int = 0):
        """Track template rendering performance"""
        with metrics_lock:
            template_entry = {
                "template": template,
                "duration": duration,
                "context_size": context_size,
                "timestamp": datetime.now(timezone.utc)
            }
            
            template_metrics[template].append(template_entry)
            
            if len(template_metrics[template]) > MAX_METRIC_ENTRIES:
                template_metrics[template] = template_metrics[template][-MAX_METRIC_ENTRIES:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with metrics_lock:
            # Analyze slow queries
            slow_queries = []
            for query_hash, entries in query_metrics.items():
                avg_duration = sum(e["duration"] for e in entries) / len(entries)
                if avg_duration > RECOMMENDED_QUERY_THRESHOLD:
                    slow_queries.append({
                        "query_hash": query_hash,
                        "avg_duration": avg_duration,
                        "count": len(entries),
                        "last_query": entries[-1]["query"][:100] + "..." if len(entries[-1]["query"]) > 100 else entries[-1]["query"]
                    })
            
            # Analyze slow templates
            slow_templates = []
            for template, entries in template_metrics.items():
                avg_duration = sum(e["duration"] for e in entries) / len(entries)
                if avg_duration > RECOMMENDED_TEMPLATE_THRESHOLD:
                    slow_templates.append({
                        "template": template,
                        "avg_duration": avg_duration,
                        "count": len(entries)
                    })
            
            # Get system resources
            try:
                process = psutil.Process()
                memory_info = process.memory_info()
                system_resources = {
                    "cpu_percent": process.cpu_percent(),
                    "memory_mb": memory_info.rss / 1024 / 1024,
                    "memory_percent": process.memory_percent()
                }
            except Exception:
                system_resources = {"error": "Unable to collect system resources"}
            
            return {
                "cache_stats": self.get_stats(),
                "slow_queries": slow_queries,
                "slow_templates": slow_templates,
                "system_resources": system_resources,
                "total_operations": len(performance_metrics),
                "recommendations": self._generate_recommendations()
            }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Cache performance
        stats = self.get_stats()
        if stats["hit_ratio"] < CACHE_HIT_THRESHOLD:
            recommendations.append(
                f"Cache hit ratio is {stats['hit_ratio']:.2%}. Consider reviewing cache strategy."
            )
        
        # Query performance
        slow_query_count = sum(
            1 for entries in query_metrics.values()
            if sum(e["duration"] for e in entries) / len(entries) > RECOMMENDED_QUERY_THRESHOLD
        )
        if slow_query_count > 0:
            recommendations.append(
                f"Found {slow_query_count} slow database queries. Consider adding indexes or optimization."
            )
        
        # Template performance
        slow_template_count = sum(
            1 for entries in template_metrics.values()
            if sum(e["duration"] for e in entries) / len(entries) > RECOMMENDED_TEMPLATE_THRESHOLD
        )
        if slow_template_count > 0:
            recommendations.append(
                f"Found {slow_template_count} slow template renders. Consider template caching."
            )
        
        if not recommendations:
            recommendations.append("No performance issues detected. System running optimally.")
        
        return recommendations
    
    # ========================================================================
    # MAINTENANCE OPERATIONS
    # ========================================================================
    
    def _cleanup_expired_entries(self):
        """Clean up expired entries from in-memory cache"""
        if not self.redis_available:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self.fallback_cache.items()
                if entry['expires'] <= current_time
            ]
            for key in expired_keys:
                del self.fallback_cache[key]
    
    def _evict_oldest_entry(self):
        """Evict oldest entry from in-memory cache"""
        if not self.redis_available and self.fallback_cache:
            oldest_key = min(
                self.fallback_cache.keys(),
                key=lambda k: self.fallback_cache[k]['created']
            )
            del self.fallback_cache[oldest_key]


# ============================================================================
# DECORATORS
# ============================================================================

def cached(timeout: int = DEFAULT_TIMEOUT, key_prefix: str = ""):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cache_manager = current_app.extensions.get('cache')
            if cache_manager:
                result = cache_manager.get(cache_key)
                if result is not None:
                    return result
            
            # Execute function and cache result
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            if cache_manager:
                cache_manager.set(cache_key, result, timeout)
                cache_manager.track_performance(f"cached_function:{func.__name__}", duration)
            
            return result
        return wrapper
    return decorator


def performance_monitor(track_args: bool = False):
    """Decorator for monitoring function performance"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Track performance
                cache_manager = current_app.extensions.get('cache')
                if cache_manager:
                    metadata = {}
                    if track_args:
                        metadata["args_count"] = len(args)
                        metadata["kwargs_count"] = len(kwargs)
                    
                    cache_manager.track_performance(func.__name__, duration, metadata)
                
                # Log slow operations
                if duration > 1.0:
                    logger.warning(f"Slow operation: {func.__name__} took {duration:.2f}s")
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Error in {func.__name__} after {duration:.2f}s: {e}")
                raise
                
        return wrapper
    return decorator


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

# Create global cache manager instance
cache_manager = UnifiedCacheManager()

# Backward compatibility
cache = cache_manager

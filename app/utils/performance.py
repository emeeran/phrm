"""
Performance monitoring and optimization utilities for PHRM.
Provides database query optimization, caching strategies, and performance metrics.
"""

import functools
import time
from typing import Any, Dict, List

from flask import current_app, g, request
from sqlalchemy import event
from sqlalchemy.engine import Engine


class PerformanceMonitor:
    """Central performance monitoring class"""

    def __init__(self):
        self.query_times = []
        self.route_times = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def track_query_time(self, duration: float):
        """Track database query execution time"""
        self.query_times.append(duration)

        # Import constant from utils
        from . import SLOW_QUERY_THRESHOLD

        # Log slow queries (> 100ms)
        if duration > SLOW_QUERY_THRESHOLD:
            current_app.logger.warning(f"Slow query detected: {duration:.3f}s")

    def track_route_time(self, route: str, duration: float):
        """Track route execution time"""
        if route not in self.route_times:
            self.route_times[route] = []
        self.route_times[route].append(duration)

        # Log slow routes (> 1s)
        if duration > 1.0:
            current_app.logger.warning(
                f"Slow route detected: {route} took {duration:.3f}s"
            )

    def cache_hit(self):
        """Record cache hit"""
        self.cache_hits += 1

    def cache_miss(self):
        """Record cache miss"""
        self.cache_misses += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        avg_query_time = (
            sum(self.query_times) / len(self.query_times) if self.query_times else 0
        )
        cache_hit_rate = (
            self.cache_hits / (self.cache_hits + self.cache_misses)
            if (self.cache_hits + self.cache_misses) > 0
            else 0
        )

        # Import constant from utils
        from . import SLOW_QUERY_THRESHOLD

        return {
            "total_queries": len(self.query_times),
            "avg_query_time": avg_query_time,
            "slow_queries": len(
                [t for t in self.query_times if t > SLOW_QUERY_THRESHOLD]
            ),
            "cache_hit_rate": cache_hit_rate,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "monitored_routes": len(self.route_times),
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def setup_database_monitoring(_app):
    """Set up database performance monitoring"""

    @event.listens_for(Engine, "before_cursor_execute")
    def receive_before_cursor_execute(
        _conn, _cursor, _statement, _parameters, context, _executemany
    ):
        context._query_start_time = time.time()

    @event.listens_for(Engine, "after_cursor_execute")
    def receive_after_cursor_execute(
        _conn, _cursor, _statement, _parameters, context, _executemany
    ):
        total = time.time() - context._query_start_time
        performance_monitor.track_query_time(total)


def monitor_route_performance(f):
    """Decorator to monitor route performance"""

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()

        try:
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time

            route_name = f"{request.method} {request.endpoint}"
            performance_monitor.track_route_time(route_name, execution_time)

            return result
        except Exception as e:
            execution_time = time.time() - start_time
            current_app.logger.error(
                f"Error in {f.__name__} after {execution_time:.3f}s: {e}"
            )
            raise

    return decorated_function


class DatabaseOptimizer:
    """Database optimization utilities"""

    @staticmethod
    def optimize_sqlite_connection(dbapi_connection, _connection_record):
        """Optimize SQLite connection settings"""
        if "sqlite" in str(dbapi_connection):
            cursor = dbapi_connection.cursor()
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            # Increase cache size (10MB)
            cursor.execute("PRAGMA cache_size=10000")
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")
            # Optimize synchronous mode
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

    @staticmethod
    def create_indexes(db):
        """Create optimized database indexes"""
        try:
            # User indexes
            db.engine.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
            )
            db.engine.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"
            )

            # Health record indexes
            db.engine.execute(
                "CREATE INDEX IF NOT EXISTS idx_health_records_user_id ON health_records(user_id)"
            )
            db.engine.execute(
                "CREATE INDEX IF NOT EXISTS idx_health_records_date ON health_records(date)"
            )
            db.engine.execute(
                "CREATE INDEX IF NOT EXISTS idx_health_records_type ON health_records(record_type)"
            )

            # Document indexes
            db.engine.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_record_id ON documents(health_record_id)"
            )
            db.engine.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at)"
            )

            current_app.logger.info("Database indexes created successfully")
        except Exception as e:
            current_app.logger.error(f"Failed to create database indexes: {e}")


class CacheManager:
    """Enhanced caching utilities"""

    def __init__(self, cache):
        self.cache = cache

    def cached_query(self, timeout=300):
        """Decorator for caching database queries"""

        def decorator(f):
            @functools.wraps(f)
            def decorated_function(*args, **kwargs):
                # Create cache key from function name and arguments
                cache_key = f"{f.__name__}:{hash(str(args) + str(kwargs))}"

                # Try to get from cache
                result = self.cache.get(cache_key)
                if result is not None:
                    performance_monitor.cache_hit()
                    return result

                # Cache miss - execute function and cache result
                performance_monitor.cache_miss()
                result = f(*args, **kwargs)
                self.cache.set(cache_key, result, timeout=timeout)

                return result

            return decorated_function

        return decorator

    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching a pattern"""
        # Note: This requires Redis cache backend for pattern matching
        try:
            if hasattr(self.cache, "cache") and hasattr(
                self.cache.cache, "delete_pattern"
            ):
                self.cache.cache.delete_pattern(pattern)
            else:
                current_app.logger.warning(
                    "Pattern-based cache invalidation not supported with current cache backend"
                )
        except Exception as e:
            current_app.logger.error(
                f"Failed to invalidate cache pattern {pattern}: {e}"
            )


def optimize_static_files(app):
    """Configure static file optimization"""

    @app.after_request
    def add_cache_headers(response):
        """Add cache headers for static files"""
        if request.endpoint == "static":
            # Cache static files for 1 day
            response.cache_control.max_age = 86400
            response.cache_control.public = True
        return response


def setup_performance_monitoring(app, db):
    """Set up comprehensive performance monitoring"""

    # Set up database monitoring
    setup_database_monitoring(app)

    # Set up database optimizations
    if "sqlite" in app.config.get("SQLALCHEMY_DATABASE_URI", ""):
        event.listen(db.engine, "connect", DatabaseOptimizer.optimize_sqlite_connection)

    # Create database indexes
    with app.app_context():
        DatabaseOptimizer.create_indexes(db)

    # Set up static file optimization
    optimize_static_files(app)

    # Add performance endpoint for monitoring
    @app.route("/api/performance-stats")
    def performance_stats():
        """Get performance statistics"""
        if not current_app.config.get("DEBUG"):
            return {"error": "Performance stats only available in debug mode"}, 403

        return performance_monitor.get_stats()


# Export commonly used decorators
monitor_performance = monitor_route_performance


# ============================================================================
# DATABASE OPTIMIZATION UTILITIES
# ============================================================================


def optimize_database_query(query_func):
    """Decorator to optimize database queries with caching and monitoring"""

    @functools.wraps(query_func)
    def wrapper(*args, **kwargs):
        # Generate cache key based on function name and arguments
        cache_key = f"{query_func.__name__}:{hash(str(args) + str(kwargs))}"

        # Try to get from cache first
        cached_result = get_cache(cache_key)
        if cached_result is not None:
            return cached_result

        # Execute query with timing
        start_time = time.time()
        result = query_func(*args, **kwargs)
        duration = time.time() - start_time

        # Import constant from utils
        from . import SLOW_QUERY_THRESHOLD

        # Log slow queries
        if duration > SLOW_QUERY_THRESHOLD:  # 100ms threshold
            current_app.logger.warning(
                f"Slow query in {query_func.__name__}: {duration:.3f}s"
            )

        # Cache result for 5 minutes by default
        set_cache(cache_key, result, timeout=300)

        return result

    return wrapper


def get_cache(key: str) -> Any:
    """Get value from cache"""
    if not hasattr(g, "_cache"):
        g._cache = {}
    return g._cache.get(key)


def set_cache(key: str, value: Any, timeout: int = 300) -> None:
    """Set value in cache with timeout"""
    if not hasattr(g, "_cache"):
        g._cache = {}
    g._cache[key] = {"value": value, "expires": time.time() + timeout}


def clear_expired_cache() -> int:
    """Clear expired cache entries and return count of cleared items"""
    if not hasattr(g, "_cache"):
        return 0

    current_time = time.time()
    expired_keys = [
        key
        for key, data in g._cache.items()
        if isinstance(data, dict) and data.get("expires", 0) < current_time
    ]

    for key in expired_keys:
        del g._cache[key]

    return len(expired_keys)


# ============================================================================
# PERFORMANCE DASHBOARD
# ============================================================================


class PerformanceDashboard:
    """Performance monitoring dashboard for operations"""

    def __init__(self):
        self.performance_monitor = PerformanceMonitor()

    def get_metrics(self) -> Dict[str, Any]:
        """Get all performance metrics"""
        stats = self.performance_monitor.get_stats()

        # Import constant from utils
        from . import SLOW_QUERY_THRESHOLD

        return {
            "query_performance": {
                "avg_query_time": sum(stats.get("query_times", []))
                / len(stats.get("query_times", [1])),
                "slow_queries": len(
                    [
                        t
                        for t in stats.get("query_times", [])
                        if t > SLOW_QUERY_THRESHOLD
                    ]
                ),
                "total_queries": len(stats.get("query_times", [])),
            },
            "route_performance": stats.get("route_times", {}),
            "cache_performance": {
                "hits": stats.get("cache_hits", 0),
                "misses": stats.get("cache_misses", 0),
                "hit_ratio": stats.get("cache_hits", 0)
                / max(1, stats.get("cache_hits", 0) + stats.get("cache_misses", 0)),
            },
            "memory_usage": self._get_memory_usage(),
            "recommendations": self._generate_recommendations(stats),
        }

    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information"""
        try:
            import psutil

            process = psutil.Process()
            return {
                "rss": process.memory_info().rss / 1024 / 1024,  # MB
                "vms": process.memory_info().vms / 1024 / 1024,  # MB
                "percent": process.memory_percent(),
            }
        except ImportError:
            return {"error": "psutil not available"}

    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []

        # Import constants from utils
        from . import CACHE_HIT_THRESHOLD, RECOMMENDED_QUERY_THRESHOLD

        query_times = stats.get("query_times", [])
        if query_times:
            avg_time = sum(query_times) / len(query_times)
            if avg_time > RECOMMENDED_QUERY_THRESHOLD:  # 50ms
                recommendations.append(
                    f"Average query time is {avg_time:.3f}s. Consider optimizing database queries."
                )

        cache_hits = stats.get("cache_hits", 0)
        cache_misses = stats.get("cache_misses", 0)
        if cache_hits + cache_misses > 0:
            hit_ratio = cache_hits / (cache_hits + cache_misses)
            if hit_ratio < CACHE_HIT_THRESHOLD:
                recommendations.append(
                    f"Cache hit ratio is {hit_ratio:.2%}. Consider improving caching strategy."
                )

        if not recommendations:
            recommendations.append("Performance looks good!")

        return recommendations

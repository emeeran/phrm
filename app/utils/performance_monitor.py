"""
Performance monitoring and caching utilities for PHRM
Provides real-time performance tracking and optimization suggestions
"""

import functools
import logging
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable, Optional

import click
import psutil
from flask import g, request

# Performance metrics storage
performance_metrics = defaultdict(list)
query_metrics = defaultdict(list)
template_metrics = defaultdict(list)
cache_metrics = defaultdict(int)

# Thread-safe locks
metrics_lock = threading.Lock()
logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Comprehensive performance tracking for PHRM application
    """

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.metrics = {}
        self.queries = []
        self.template_renders = []

    def start(self):
        """Start performance tracking"""
        self.start_time = time.perf_counter()
        self.metrics["memory_start"] = (
            psutil.Process().memory_info().rss / 1024 / 1024
        )  # MB

    def stop(self):
        """Stop performance tracking and calculate metrics"""
        if self.start_time:
            self.end_time = time.perf_counter()
            self.metrics["duration"] = self.end_time - self.start_time
            self.metrics["memory_end"] = (
                psutil.Process().memory_info().rss / 1024 / 1024
            )  # MB
            self.metrics["memory_delta"] = (
                self.metrics["memory_end"] - self.metrics["memory_start"]
            )

    def add_query(self, query: str, duration: float, parameters: Optional[dict] = None):
        """Add database query metrics"""
        self.queries.append(
            {
                "query": query,
                "duration": duration,
                "parameters": parameters,
                "timestamp": datetime.now(timezone.utc),
            }
        )

    def add_template_render(
        self, template: str, duration: float, context_size: int = 0
    ):
        """Add template rendering metrics"""
        self.template_renders.append(
            {
                "template": template,
                "duration": duration,
                "context_size": context_size,
                "timestamp": datetime.now(timezone.utc),
            }
        )

    def get_summary(self) -> dict[str, Any]:
        """Get performance summary"""
        return {
            "total_duration": self.metrics.get("duration", 0),
            "memory_usage": self.metrics.get("memory_delta", 0),
            "query_count": len(self.queries),
            "total_query_time": sum(q["duration"] for q in self.queries),
            "template_count": len(self.template_renders),
            "total_template_time": sum(t["duration"] for t in self.template_renders),
            "slowest_query": (
                max(self.queries, key=lambda x: x["duration"]) if self.queries else None
            ),
            "slowest_template": (
                max(self.template_renders, key=lambda x: x["duration"])
                if self.template_renders
                else None
            ),
        }


def track_performance(func: Callable) -> Callable:
    """
    Decorator to track function performance
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tracker = PerformanceTracker()
        tracker.start()

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            tracker.stop()

            # Store metrics
            with metrics_lock:
                performance_metrics[func.__name__].append(tracker.get_summary())

                # Import constant from utils
                from . import MAX_PERFORMANCE_ENTRIES

                # Keep only last 100 entries to prevent memory bloat
                if len(performance_metrics[func.__name__]) > MAX_PERFORMANCE_ENTRIES:
                    performance_metrics[func.__name__] = performance_metrics[
                        func.__name__
                    ][-MAX_PERFORMANCE_ENTRIES:]

    return wrapper


def monitor_performance(func: Callable) -> Callable:
    """Performance monitoring decorator (simple version for route timing)"""

    @wraps(func)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            if execution_time > 1.0:
                logger.warning(
                    f"Slow operation: {func.__name__} took {execution_time:.2f}s"
                )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in {func.__name__} after {execution_time:.2f}s: {e}")
            raise

    return decorated_function


def track_database_query(
    query: str, duration: float, parameters: Optional[dict] = None
):
    """
    Track database query performance
    """
    # Import constant from utils
    from . import MAX_PERFORMANCE_ENTRIES as MAX_QUERY_LENGTH

    with metrics_lock:
        query_metrics[request.endpoint or "unknown"].append(
            {
                "query": (
                    query[:MAX_QUERY_LENGTH] + "..."
                    if len(query) > MAX_QUERY_LENGTH
                    else query
                ),  # Truncate long queries
                "duration": duration,
                "parameters": parameters,
                "timestamp": datetime.now(timezone.utc),
                "endpoint": request.endpoint,
                "method": request.method,
            }
        )

        # Import constant from utils
        from . import MAX_QUERY_ENTRIES

        # Keep only last 200 queries
        if len(query_metrics[request.endpoint or "unknown"]) > MAX_QUERY_ENTRIES:
            query_metrics[request.endpoint or "unknown"] = query_metrics[
                request.endpoint or "unknown"
            ][-MAX_QUERY_ENTRIES:]


def track_template_render(
    template_name: str, duration: float, context_keys: Optional[list[str]] = None
):
    """
    Track template rendering performance
    """
    with metrics_lock:
        template_metrics[template_name].append(
            {
                "duration": duration,
                "context_size": len(context_keys) if context_keys else 0,
                "context_keys": (
                    context_keys[:10] if context_keys else []
                ),  # Store first 10 keys
                "timestamp": datetime.now(timezone.utc),
                "endpoint": request.endpoint,
                "method": request.method,
            }
        )

        # Import constant from utils
        from . import MAX_TEMPLATE_ENTRIES

        # Keep only last 100 renders per template
        if len(template_metrics[template_name]) > MAX_TEMPLATE_ENTRIES:
            template_metrics[template_name] = template_metrics[template_name][
                -MAX_TEMPLATE_ENTRIES:
            ]


class CacheManager:
    """
    Advanced caching manager with performance tracking
    """

    def __init__(self):
        self.local_cache = {}
        self.cache_stats = defaultdict(lambda: {"hits": 0, "misses": 0, "size": 0})

    def get(self, key: str, default=None):
        """Get item from cache"""
        if key in self.local_cache:
            self.cache_stats[key]["hits"] += 1
            cache_metrics["hits"] += 1
            return self.local_cache[key]
        else:
            self.cache_stats[key]["misses"] += 1
            cache_metrics["misses"] += 1
            return default

    def set(self, key: str, value: Any, ttl: int = 300):
        """Set item in cache with TTL"""
        self.local_cache[key] = {
            "value": value,
            "expires": datetime.now(timezone.utc) + timedelta(seconds=ttl),
        }
        self.cache_stats[key]["size"] = len(str(value))
        cache_metrics["sets"] += 1

    def delete(self, key: str):
        """Delete item from cache"""
        if key in self.local_cache:
            del self.local_cache[key]
            cache_metrics["deletes"] += 1

    def clear_expired(self):
        """Clear expired cache entries"""
        now = datetime.now(timezone.utc)
        expired_keys = [
            key for key, data in self.local_cache.items() if data["expires"] < now
        ]
        for key in expired_keys:
            del self.local_cache[key]
        return len(expired_keys)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        total_hits = sum(stats["hits"] for stats in self.cache_stats.values())
        total_misses = sum(stats["misses"] for stats in self.cache_stats.values())
        hit_ratio = (
            total_hits / (total_hits + total_misses)
            if (total_hits + total_misses) > 0
            else 0
        )

        return {
            "total_keys": len(self.local_cache),
            "total_hits": total_hits,
            "total_misses": total_misses,
            "hit_ratio": hit_ratio,
            "memory_usage": sum(stats["size"] for stats in self.cache_stats.values()),
            "global_stats": dict(cache_metrics),
        }


# Global cache manager instance
cache_manager = CacheManager()


def get_performance_report() -> dict[str, Any]:
    """
    Generate comprehensive performance report
    """
    with metrics_lock:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_info": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
            },
            "application_metrics": {
                "function_performance": dict(performance_metrics),
                "database_queries": dict(query_metrics),
                "template_rendering": dict(template_metrics),
                "cache_performance": cache_manager.get_stats(),
            },
            "recommendations": generate_performance_recommendations(),
        }

    return report


def _analyze_slow_queries():
    """Analyze and identify slow database queries"""
    from . import SLOW_QUERY_THRESHOLD

    slow_queries = []
    for endpoint, queries in query_metrics.items():
        for query in queries:
            if query["duration"] > SLOW_QUERY_THRESHOLD:
                slow_queries.append((endpoint, query))
    return slow_queries


def _analyze_slow_templates():
    """Analyze and identify slow template renders"""
    from . import RECOMMENDED_QUERY_THRESHOLD

    slow_templates = []
    for template, renders in template_metrics.items():
        avg_duration = (
            sum(r["duration"] for r in renders) / len(renders) if renders else 0
        )
        if avg_duration > RECOMMENDED_QUERY_THRESHOLD:
            slow_templates.append((template, avg_duration))
    return slow_templates


def _analyze_cache_performance():
    """Analyze cache performance metrics"""
    from . import CACHE_HIT_THRESHOLD

    cache_stats = cache_manager.get_stats()
    return cache_stats, cache_stats["hit_ratio"] < CACHE_HIT_THRESHOLD


def _analyze_system_resources():
    """Analyze system resource usage"""
    from . import CPU_WARNING_THRESHOLD, MEMORY_WARNING_THRESHOLD

    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent

    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "cpu_high": cpu_percent > CPU_WARNING_THRESHOLD,
        "memory_high": memory_percent > MEMORY_WARNING_THRESHOLD,
    }


def generate_performance_recommendations() -> list[str]:
    """
    Generate performance optimization recommendations
    """
    recommendations = []

    # Analyze query performance
    slow_queries = _analyze_slow_queries()
    if slow_queries:
        recommendations.append(
            f"Found {len(slow_queries)} slow database queries (>100ms). Consider adding indexes or optimizing query logic."
        )

    # Analyze template performance
    slow_templates = _analyze_slow_templates()
    if slow_templates:
        recommendations.append(
            f"Found {len(slow_templates)} slow template renders (>50ms avg). Consider template caching or optimization."
        )

    # Analyze cache performance
    cache_stats, cache_needs_improvement = _analyze_cache_performance()
    if cache_needs_improvement:
        recommendations.append(
            f"Cache hit ratio is {cache_stats['hit_ratio']:.2%}. Consider reviewing cache strategy."
        )

    # System resource recommendations
    resource_stats = _analyze_system_resources()
    if resource_stats["cpu_high"]:
        recommendations.append(
            f"High CPU usage detected ({resource_stats['cpu_percent']}%). Consider scaling or optimization."
        )

    if resource_stats["memory_high"]:
        recommendations.append(
            f"High memory usage detected ({resource_stats['memory_percent']}%). Consider memory optimization or scaling."
        )

    if not recommendations:
        recommendations.append(
            "No performance issues detected. System running optimally."
        )

    return recommendations


def clear_old_metrics(days: int = 1):
    """
    Clear metrics older than specified days
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    with metrics_lock:
        # Clear old query metrics
        for endpoint in list(query_metrics.keys()):
            query_metrics[endpoint] = [
                q for q in query_metrics[endpoint] if q["timestamp"] > cutoff
            ]
            if not query_metrics[endpoint]:
                del query_metrics[endpoint]

        # Clear old template metrics
        for template in list(template_metrics.keys()):
            template_metrics[template] = [
                t for t in template_metrics[template] if t["timestamp"] > cutoff
            ]
            if not template_metrics[template]:
                del template_metrics[template]

        # Clear expired cache entries
        cache_manager.clear_expired()

    logger.info(f"Cleared performance metrics older than {days} days")


# Flask integration helpers
def init_performance_monitoring(app):
    """
    Initialize performance monitoring for Flask app
    """

    @app.before_request
    def before_request():
        g.performance_tracker = PerformanceTracker()
        g.performance_tracker.start()

    @app.after_request
    def after_request(response):
        if hasattr(g, "performance_tracker"):
            g.performance_tracker.stop()

            # Log slow requests
            duration = g.performance_tracker.metrics.get("duration", 0)
            if duration > 1.0:  # Requests taking more than 1 second
                logger.warning(
                    f"Slow request detected: {request.endpoint} took {duration:.2f}s"
                )

        return response

    @app.teardown_appcontext
    def cleanup_performance(_error):
        # Clean up any performance tracking resources
        if hasattr(g, "performance_tracker"):
            del g.performance_tracker

    # Register cleanup task to run periodically
    @app.cli.command()
    def cleanup_metrics():
        """Clean up old performance metrics"""
        clear_old_metrics()
        click.echo("Performance metrics cleaned up")

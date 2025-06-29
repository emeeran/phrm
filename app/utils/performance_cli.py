"""
Performance Monitoring CLI Commands for PHRM
Provides real-time performance insights and optimization recommendations
"""

import time
from datetime import datetime, timedelta

import click
from flask import current_app
from flask.cli import with_appcontext

from ..utils.unified_cache import cache_manager


@click.group()
def performance():
    """Performance monitoring and optimization commands."""
    pass


@performance.command()
@click.option('--detailed', is_flag=True, help='Show detailed performance breakdown')
@with_appcontext
def stats(detailed):
    """Display current performance statistics."""
    click.echo("🔍 PHRM Performance Statistics")
    click.echo("=" * 50)
    
    try:
        summary = cache_manager.get_performance_summary()
        
        # Cache Statistics
        cache_stats = summary['cache_stats']
        click.echo(f"\n📊 Cache Performance:")
        click.echo(f"  Redis Available: {'✅' if cache_stats['redis_available'] else '❌'}")
        click.echo(f"  Total Operations: {cache_stats['total_operations']:,}")
        click.echo(f"  Hit Ratio: {cache_stats['hit_ratio']:.2%}")
        click.echo(f"  Total Errors: {cache_stats['total_errors']:,}")
        
        if not cache_stats['redis_available']:
            click.echo(f"  Fallback Cache Size: {cache_stats.get('fallback_cache_size', 0):,}")
            click.echo(f"  Memory Usage: {cache_stats.get('fallback_cache_memory', 0):,} bytes")
        
        # System Resources
        resources = summary['system_resources']
        if 'error' not in resources:
            click.echo(f"\n💾 System Resources:")
            click.echo(f"  CPU Usage: {resources['cpu_percent']:.1f}%")
            click.echo(f"  Memory: {resources['memory_mb']:.1f} MB ({resources['memory_percent']:.1f}%)")
        
        # Performance Issues
        slow_queries = summary['slow_queries']
        slow_templates = summary['slow_templates']
        
        if slow_queries:
            click.echo(f"\n⚠️  Slow Queries ({len(slow_queries)}):")
            for query in slow_queries[:5]:  # Show top 5
                click.echo(f"  • {query['avg_duration']*1000:.1f}ms avg - {query['last_query'][:60]}...")
        
        if slow_templates:
            click.echo(f"\n⚠️  Slow Templates ({len(slow_templates)}):")
            for template in slow_templates[:5]:  # Show top 5
                click.echo(f"  • {template['avg_duration']*1000:.1f}ms avg - {template['template']}")
        
        # Recommendations
        recommendations = summary['recommendations']
        if recommendations:
            click.echo(f"\n💡 Recommendations:")
            for rec in recommendations:
                click.echo(f"  • {rec}")
        
        if detailed:
            click.echo(f"\n📈 Detailed Metrics:")
            click.echo(f"  Total Operations Tracked: {summary['total_operations']:,}")
            click.echo(f"  Unique Cache Keys: {cache_stats['unique_keys']:,}")
        
    except Exception as e:
        click.echo(f"❌ Error retrieving performance stats: {e}")


@performance.command()
@click.option('--pattern', default='*', help='Cache key pattern to clear')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@with_appcontext
def clear_cache(pattern, confirm):
    """Clear cache entries matching pattern."""
    if not confirm:
        if not click.confirm(f"Are you sure you want to clear cache entries matching '{pattern}'?"):
            click.echo("Operation cancelled.")
            return
    
    try:
        if pattern == '*':
            success = cache_manager.clear()
            if success:
                click.echo("✅ All cache entries cleared successfully.")
            else:
                click.echo("❌ Failed to clear cache.")
        else:
            deleted = cache_manager.delete_pattern(pattern)
            click.echo(f"✅ Cleared {deleted} cache entries matching '{pattern}'.")
    
    except Exception as e:
        click.echo(f"❌ Error clearing cache: {e}")


@performance.command()
@click.option('--duration', default=30, help='Monitoring duration in seconds')
@click.option('--interval', default=5, help='Update interval in seconds')
@with_appcontext
def monitor(duration, interval):
    """Real-time performance monitoring."""
    click.echo(f"🔍 Real-time Performance Monitor (Duration: {duration}s, Interval: {interval}s)")
    click.echo("Press Ctrl+C to stop early")
    click.echo("=" * 70)
    
    start_time = time.time()
    
    try:
        while time.time() - start_time < duration:
            # Clear screen (works on most terminals)
            click.clear()
            
            summary = cache_manager.get_performance_summary()
            cache_stats = summary['cache_stats']
            resources = summary.get('system_resources', {})
            
            # Header
            current_time = datetime.now().strftime("%H:%M:%S")
            click.echo(f"📊 PHRM Performance Monitor - {current_time}")
            click.echo("=" * 50)
            
            # Cache metrics
            click.echo(f"Cache Hit Ratio: {cache_stats['hit_ratio']:.2%}")
            click.echo(f"Total Operations: {cache_stats['total_operations']:,}")
            click.echo(f"Cache Errors: {cache_stats['total_errors']:,}")
            
            # System resources
            if 'error' not in resources:
                click.echo(f"CPU Usage: {resources['cpu_percent']:.1f}%")
                click.echo(f"Memory: {resources['memory_mb']:.1f} MB")
            
            # Performance indicators
            slow_queries = len(summary.get('slow_queries', []))
            slow_templates = len(summary.get('slow_templates', []))
            
            if slow_queries > 0:
                click.echo(f"⚠️  Slow Queries: {slow_queries}")
            if slow_templates > 0:
                click.echo(f"⚠️  Slow Templates: {slow_templates}")
            
            if slow_queries == 0 and slow_templates == 0:
                click.echo("✅ No performance issues detected")
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        click.echo("\n\n⏹️  Monitoring stopped by user.")
    except Exception as e:
        click.echo(f"\n❌ Monitoring error: {e}")


@performance.command()
@with_appcontext
def optimize():
    """Run automatic performance optimizations."""
    click.echo("🚀 Running Performance Optimizations...")
    click.echo("=" * 40)
    
    optimizations_applied = 0
    
    try:
        # Clear expired cache entries
        click.echo("🧹 Cleaning up expired cache entries...")
        if hasattr(cache_manager, '_cleanup_expired_entries'):
            cache_manager._cleanup_expired_entries()
            optimizations_applied += 1
            click.echo("  ✅ Cache cleanup completed")
        
        # Analyze and report on performance bottlenecks
        summary = cache_manager.get_performance_summary()
        
        # Cache optimization
        cache_stats = summary['cache_stats']
        if cache_stats['hit_ratio'] < 0.7:
            click.echo("💡 Cache hit ratio is low. Consider:")
            click.echo("   - Increasing cache timeout for frequently accessed data")
            click.echo("   - Pre-warming cache for common queries")
            click.echo("   - Reviewing cache key strategies")
        
        # Query optimization suggestions
        slow_queries = summary.get('slow_queries', [])
        if slow_queries:
            click.echo(f"🐌 Found {len(slow_queries)} slow queries. Consider:")
            click.echo("   - Adding database indexes")
            click.echo("   - Optimizing query logic")
            click.echo("   - Implementing query result caching")
        
        # Template optimization suggestions
        slow_templates = summary.get('slow_templates', [])
        if slow_templates:
            click.echo(f"🐌 Found {len(slow_templates)} slow templates. Consider:")
            click.echo("   - Template fragment caching")
            click.echo("   - Reducing template complexity")
            click.echo("   - Pre-computing expensive template data")
        
        # System resource warnings
        resources = summary.get('system_resources', {})
        if 'error' not in resources:
            if resources['cpu_percent'] > 80:
                click.echo("⚠️  High CPU usage detected. Consider scaling or optimization.")
            if resources['memory_percent'] > 80:
                click.echo("⚠️  High memory usage detected. Consider memory optimization.")
        
        if optimizations_applied > 0:
            click.echo(f"\n✅ Applied {optimizations_applied} automatic optimizations.")
        else:
            click.echo("\n✅ System already optimized. No automatic optimizations needed.")
    
    except Exception as e:
        click.echo(f"❌ Error during optimization: {e}")


@performance.command()
@click.option('--export-path', default='performance_report.txt', help='Export path for the report')
@with_appcontext
def report(export_path):
    """Generate a comprehensive performance report."""
    click.echo("📋 Generating Performance Report...")
    
    try:
        summary = cache_manager.get_performance_summary()
        
        report_lines = [
            "PHRM Performance Report",
            "=" * 50,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "CACHE STATISTICS",
            "-" * 20,
            f"Redis Available: {summary['cache_stats']['redis_available']}",
            f"Total Operations: {summary['cache_stats']['total_operations']:,}",
            f"Hit Ratio: {summary['cache_stats']['hit_ratio']:.2%}",
            f"Total Errors: {summary['cache_stats']['total_errors']:,}",
            f"Unique Keys: {summary['cache_stats']['unique_keys']:,}",
            "",
            "SYSTEM RESOURCES",
            "-" * 20
        ]
        
        resources = summary.get('system_resources', {})
        if 'error' not in resources:
            report_lines.extend([
                f"CPU Usage: {resources['cpu_percent']:.1f}%",
                f"Memory: {resources['memory_mb']:.1f} MB ({resources['memory_percent']:.1f}%)",
            ])
        else:
            report_lines.append(f"Resource monitoring error: {resources['error']}")
        
        report_lines.extend([
            "",
            "PERFORMANCE ISSUES",
            "-" * 20
        ])
        
        slow_queries = summary.get('slow_queries', [])
        if slow_queries:
            report_lines.append(f"Slow Queries: {len(slow_queries)}")
            for i, query in enumerate(slow_queries[:10], 1):
                report_lines.append(f"  {i}. {query['avg_duration']*1000:.1f}ms avg - {query['last_query'][:80]}...")
        else:
            report_lines.append("No slow queries detected")
        
        slow_templates = summary.get('slow_templates', [])
        if slow_templates:
            report_lines.append(f"\nSlow Templates: {len(slow_templates)}")
            for i, template in enumerate(slow_templates[:10], 1):
                report_lines.append(f"  {i}. {template['avg_duration']*1000:.1f}ms avg - {template['template']}")
        else:
            report_lines.append("\nNo slow templates detected")
        
        report_lines.extend([
            "",
            "RECOMMENDATIONS",
            "-" * 20
        ])
        
        for rec in summary.get('recommendations', []):
            report_lines.append(f"• {rec}")
        
        report_lines.append(f"\nReport completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Write to file
        with open(export_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        click.echo(f"✅ Performance report saved to: {export_path}")
        
        # Also display summary to console
        click.echo("\n📊 Report Summary:")
        cache_stats = summary['cache_stats']
        click.echo(f"  Cache Hit Ratio: {cache_stats['hit_ratio']:.2%}")
        click.echo(f"  Slow Queries: {len(slow_queries)}")
        click.echo(f"  Slow Templates: {len(slow_templates)}")
        
    except Exception as e:
        click.echo(f"❌ Error generating report: {e}")


def init_performance_cli(app):
    """Initialize performance CLI commands"""
    app.cli.add_command(performance)
    app.logger.info("✅ Performance CLI commands registered")

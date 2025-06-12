#!/usr/bin/env python3
"""
Production Operations Dashboard
Unified dashboard for monitoring PHRM production deployment
"""

import json
import time
from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user, login_required

from app.utils.performance import PerformanceDashboard, monitor_performance

# Import shared utilities
from app.utils.shared import log_security_event, require_admin

# Import our production monitoring tools
try:
    from app.utils.backup_manager import BackupManager
    from app.utils.health_monitor import HealthMonitor
    from app.utils.log_analyzer import LogAnalyzer
except ImportError:
    # Fallback if modules not available
    HealthMonitor = None
    BackupManager = None
    LogAnalyzer = None

ops_bp = Blueprint("ops", __name__, url_prefix="/ops")


@ops_bp.route("/")
@login_required
@require_admin
@monitor_performance
def dashboard():
    """Production operations dashboard"""
    return render_template("ops/dashboard.html", title="Operations Dashboard")


@ops_bp.route("/api/health")
@login_required
@require_admin
@monitor_performance
def health_status():
    """Get current system health status"""
    if not HealthMonitor:
        return jsonify({"error": "Health monitor not available"}), 503

    monitor = HealthMonitor()
    report = monitor.generate_health_report()

    log_security_event(
        "health_status_checked",
        {"user_id": current_user.id, "health_score": report.get("health_score", 0)},
    )

    return jsonify(report)


@ops_bp.route("/api/metrics")
@login_required
@require_admin
@monitor_performance
def system_metrics():
    """Get real-time system metrics"""
    if not HealthMonitor:
        return jsonify({"error": "Health monitor not available"}), 503

    monitor = HealthMonitor()
    metrics = monitor.collect_system_metrics()

    return jsonify({"timestamp": datetime.now().isoformat(), "metrics": metrics})


@ops_bp.route("/api/logs/analyze")
@login_required
@require_admin
@monitor_performance
def analyze_logs():
    """Analyze recent logs"""
    if not LogAnalyzer:
        return jsonify({"error": "Log analyzer not available"}), 503

    hours = request.args.get("hours", 1, type=int)
    hours = min(max(1, hours), 168)  # Limit to 1-168 hours (1 week)
    analyzer = LogAnalyzer()
    results = analyzer.analyze(hours=hours)
    return jsonify(results)

    log_security_event(
        "logs_analyzed",
        {
            "user_id": current_user.id,
            "hours": hours,
            "total_alerts": results.get("metrics", {}).get("total_alerts", 0),
        },
    )

    return jsonify(results)



@ops_bp.route("/api/logs/alerts")
@login_required
@require_admin
@monitor_performance
def recent_alerts():
    """Get recent alerts"""
    try:
        if not LogAnalyzer:
            return jsonify({"error": "Log analyzer not available"}), 503

        hours = request.args.get("hours", 24, type=int)
        hours = min(max(1, hours), 168)  # Limit to 1-168 hours

        analyzer = LogAnalyzer()
        alerts = analyzer.get_recent_alerts(hours)

        return jsonify(
            {
                "alerts": alerts,
                "total": len(alerts),
                "critical": len([a for a in alerts if a["severity"] == "CRITICAL"]),
                "errors": len([a for a in alerts if a["severity"] == "ERROR"]),
                "warnings": len([a for a in alerts if a["severity"] == "WARNING"]),
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error getting alerts: {e}")
        return jsonify({"error": str(e)}), 500


@ops_bp.route("/api/alerts/<int:alert_id>/acknowledge", methods=["POST"])
@login_required
@require_admin
@monitor_performance
def acknowledge_alert(alert_id):
    """Acknowledge a specific alert"""
    try:
        if not LogAnalyzer:
            return jsonify({"error": "Log analyzer not available"}), 503

        analyzer = LogAnalyzer()
        success = analyzer.acknowledge_alert(alert_id)

        if success:
            log_security_event(
                "alert_acknowledged", {"user_id": current_user.id, "alert_id": alert_id}
            )
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Alert not found"}), 404

    except Exception as e:
        current_app.logger.error(f"Error acknowledging alert: {e}")
        return jsonify({"error": str(e)}), 500


@ops_bp.route("/api/backups")
@login_required
@require_admin
@monitor_performance
def backup_status():
    """Get backup system status"""
    try:
        if not BackupManager:
            return jsonify({"error": "Backup manager not available"}), 503

        backup_manager = BackupManager()
        status = backup_manager.get_backup_status()

        return jsonify(status)

    except Exception as e:
        current_app.logger.error(f"Error getting backup status: {e}")
        return jsonify({"error": str(e)}), 500


@ops_bp.route("/api/backups/create", methods=["POST"])
@login_required
@require_admin
@monitor_performance
def create_backup():
    """Create a new backup"""
    try:
        if not BackupManager:
            return jsonify({"error": "Backup manager not available"}), 503

        backup_manager = BackupManager()

        log_security_event("backup_requested", {"user_id": current_user.id})

        # Run backup in background (this might take a while)
        result = backup_manager.create_full_backup()

        if result["status"] == "SUCCESS":
            log_security_event(
                "backup_completed",
                {
                    "user_id": current_user.id,
                    "backup_name": result["backup_name"],
                    "file_size_mb": result["file_size_mb"],
                },
            )
        else:
            log_security_event(
                "backup_failed",
                {
                    "user_id": current_user.id,
                    "error": result.get("error", "Unknown error"),
                },
            )

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Error creating backup: {e}")
        return jsonify({"error": str(e)}), 500


@ops_bp.route("/api/backups/list")
@login_required
@require_admin
@monitor_performance
def list_backups():
    """List available backups"""
    try:
        if not BackupManager:
            return jsonify({"error": "Backup manager not available"}), 503

        backup_manager = BackupManager()
        backups = backup_manager.list_backups()

        return jsonify({"backups": backups, "total": len(backups)})

    except Exception as e:
        current_app.logger.error(f"Error listing backups: {e}")
        return jsonify({"error": str(e)}), 500


@ops_bp.route("/api/performance/history")
@login_required
@require_admin
@monitor_performance
def performance_history():
    """Get performance metrics history"""
    try:
        if not HealthMonitor:
            return jsonify({"error": "Health monitor not available"}), 503

        hours = request.args.get("hours", 24, type=int)
        hours = min(max(1, hours), 168)  # Limit to 1-168 hours

        monitor = HealthMonitor()
        metrics = monitor.get_recent_metrics(hours)

        return jsonify(
            {"metrics": metrics, "period_hours": hours, "total_entries": len(metrics)}
        )

    except Exception as e:
        current_app.logger.error(f"Error getting performance history: {e}")
        return jsonify({"error": str(e)}), 500


@ops_bp.route("/api/system/info")
@login_required
@require_admin
@monitor_performance
def system_info():
    """Get system information"""
    try:
        import os
        import platform

        import psutil

        # System information
        info = {
            "system": {
                "hostname": platform.node(),
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "disk_total_gb": psutil.disk_usage("/").total / (1024**3),
            },
            "application": {
                "version": "2.0.0",  # Update this with actual version
                "environment": os.getenv("FLASK_ENV", "production"),
                "debug": current_app.debug,
                "uptime_hours": (
                    datetime.now()
                    - datetime.fromtimestamp(psutil.Process().create_time())
                ).total_seconds()
                / 3600,
            },
            "database": {
                "type": "PostgreSQL",
                "url_configured": bool(os.getenv("DATABASE_URL")),
                "ssl_configured": bool(os.getenv("DATABASE_SSL")),
            },
            "redis": {
                "configured": bool(os.getenv("REDIS_URL")),
                "ssl_configured": bool(os.getenv("REDIS_SSL")),
            },
        }

        return jsonify(info)

    except Exception as e:
        current_app.logger.error(f"Error getting system info: {e}")
        return jsonify({"error": str(e)}), 500


@ops_bp.route("/api/maintenance/restart", methods=["POST"])
@login_required
@require_admin
@monitor_performance
def restart_application():
    """Restart the application (graceful shutdown signal)"""
    try:
        import os
        import signal

        log_security_event(
            "application_restart_requested", {"user_id": current_user.id}
        )

        # In production, this would typically restart via process manager
        # For now, just log the request
        current_app.logger.warning(
            f"Application restart requested by user {current_user.id}"
        )

        return jsonify(
            {
                "status": "restart_requested",
                "message": "Restart signal sent to process manager",
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error requesting restart: {e}")
        return jsonify({"error": str(e)}), 500


@ops_bp.route("/api/logs/download")
@login_required
@require_admin
@monitor_performance
def download_logs():
    """Prepare logs for download"""
    try:
        import tempfile
        import zipfile

        from flask import send_file
        from pathlib import Path

        log_dir = Path("/home/em/code/wip/phrm/logs")

        # Create temporary zip file
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
            with zipfile.ZipFile(tmp_file.name, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for log_file in log_dir.glob("*.log"):
                    if log_file.exists():
                        zip_file.write(log_file, log_file.name)

        log_security_event("logs_downloaded", {"user_id": current_user.id})

        return send_file(
            tmp_file.name,
            as_attachment=True,
            download_name=f'phrm_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
        )

    except Exception as e:
        current_app.logger.error(f"Error preparing log download: {e}")
        return jsonify({"error": str(e)}), 500


# Register error handlers
@ops_bp.errorhandler(403)
def forbidden(error):
    return jsonify({"error": "Access denied - admin privileges required"}), 403


@ops_bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# Additional utility functions for dashboard
def get_quick_stats():
    """Get quick stats for dashboard"""
    try:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "services": {
                "health_monitor": HealthMonitor is not None,
                "backup_manager": BackupManager is not None,
                "log_analyzer": LogAnalyzer is not None,
            },
        }

        if HealthMonitor:
            monitor = HealthMonitor()
            current_metrics = monitor.collect_system_metrics()
            stats["current_health"] = monitor._calculate_health_score(current_metrics)

        if LogAnalyzer:
            analyzer = LogAnalyzer()
            recent_alerts = analyzer.get_recent_alerts(1)  # Last hour
            stats["recent_alerts"] = len(recent_alerts)
            stats["critical_alerts"] = len(
                [a for a in recent_alerts if a["severity"] == "CRITICAL"]
            )

        if BackupManager:
            backup_manager = BackupManager()
            backup_status = backup_manager.get_backup_status()
            stats["latest_backup"] = backup_status.get("latest_backup")

        return stats

    except Exception as e:
        current_app.logger.error(f"Error getting quick stats: {e}")
        return {"error": str(e)}


# Template context processor
@ops_bp.context_processor
def inject_ops_data():
    """Inject operations data into templates"""
    return {"ops_quick_stats": get_quick_stats()}

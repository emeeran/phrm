"""
Backup API endpoints for secure data export
"""

import json
from datetime import datetime

from flask import Blueprint, jsonify, send_file
from flask_login import current_user, login_required

from ..utils.backup_manager import BackupManager
from ..utils.shared import log_security_event, monitor_performance

backup_api_bp = Blueprint("backup_api", __name__, url_prefix="/api/backup")


@backup_api_bp.route("/create", methods=["POST"])
@login_required
@monitor_performance
def create_backup():
    """
    Create a JSON backup of user's health data
    """
    try:
        # Log backup request
        log_security_event(
            "backup_requested",
            {"user_id": current_user.id, "timestamp": datetime.utcnow().isoformat()},
        )

        # Create backup manager and backup data
        backup_manager = BackupManager()
        backup_path = backup_manager.create_backup(current_user.id, include_files=False)
        
        # Read the backup data
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)

        # Log successful backup creation
        log_security_event(
            "backup_created",
            {
                "user_id": current_user.id,
                "backup_size": len(str(backup_data)),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return jsonify(
            {
                "success": True,
                "data": backup_data,
                "message": "Backup created successfully",
            }
        )

    except Exception as e:
        log_security_event(
            "backup_failed",
            {
                "user_id": current_user.id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return jsonify({"success": False, "error": "Failed to create backup"}), 500


@backup_api_bp.route("/download", methods=["GET"])
@login_required
@monitor_performance
def download_backup():
    """
    Download a compressed backup file
    """
    try:
        # Log backup download request
        log_security_event(
            "backup_download_requested",
            {"user_id": current_user.id, "timestamp": datetime.utcnow().isoformat()},
        )

        # Create backup manager and backup file
        backup_manager = BackupManager()
        backup_file = backup_manager.create_backup(current_user.id, include_files=True)

        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"health_backup_{current_user.username}_{timestamp}.zip"

        # Log successful backup download
        log_security_event(
            "backup_downloaded",
            {
                "user_id": current_user.id,
                "filename": filename,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return send_file(
            backup_file,
            as_attachment=True,
            download_name=filename,
            mimetype="application/zip",
        )

    except Exception as e:
        log_security_event(
            "backup_download_failed",
            {
                "user_id": current_user.id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return jsonify({"success": False, "error": "Failed to create backup file"}), 500


@backup_api_bp.route("/status", methods=["GET"])
@login_required
@monitor_performance
def backup_status():
    """
    Get backup status and information
    """
    try:
        # Calculate backup statistics
        family_members_count = len(current_user.family_members)

        # Get record counts (simplified for status)
        from ..models import Appointment, HealthRecord

        total_records = HealthRecord.query.filter_by(user_id=current_user.id).count()
        family_member_ids = [fm.id for fm in current_user.family_members]
        if family_member_ids:
            total_records += HealthRecord.query.filter(
                HealthRecord.family_member_id.in_(family_member_ids)
            ).count()

        total_appointments = Appointment.query.filter_by(
            user_id=current_user.id
        ).count()
        if family_member_ids:
            total_appointments += Appointment.query.filter(
                Appointment.family_member_id.in_(family_member_ids)
            ).count()

        status_info = {
            "user": {
                "username": current_user.username,
                "member_since": current_user.created_at.isoformat(),
            },
            "data_summary": {
                "family_members": family_members_count,
                "health_records": total_records,
                "appointments": total_appointments,
            },
            "backup_info": {
                "last_backup": "Never",  # In production, track this
                "backup_available": True,
                "estimated_size": "Varies based on data",
                "format": "Encrypted ZIP file",
            },
            "security": {
                "encryption": "Data is encrypted during backup",
                "privacy": "Backups contain sensitive health information",
                "storage": "Store backup files securely",
            },
        }

        return jsonify({"success": True, "data": status_info})

    except Exception:
        return jsonify({"success": False, "error": "Failed to get backup status"}), 500

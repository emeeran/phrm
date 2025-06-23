"""
Backup API endpoints for secure data export
"""

import json
import os
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
        
        # Read the metadata to get backup info
        metadata_path = os.path.join(backup_path, "metadata.json")
        with open(metadata_path, 'r') as f:
            backup_metadata = json.load(f)

        # Log successful backup creation
        log_security_event(
            "backup_created",
            {
                "user_id": current_user.id,
                "backup_size": len(str(backup_metadata)),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return jsonify(
            {
                "success": True,
                "data": backup_metadata,
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
        backup_path = backup_manager.create_backup(current_user.id, include_files=True)

        # Create ZIP file from backup directory
        import tempfile
        import zipfile
        
        # Create temporary ZIP file
        zip_fd, zip_path = tempfile.mkstemp(suffix='.zip')
        os.close(zip_fd)  # Close the file descriptor, we'll use the path
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all files from backup directory to zip
                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Create relative path for zip archive
                        arcname = os.path.relpath(file_path, backup_path)
                        zipf.write(file_path, arcname)
            
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
                zip_path,
                as_attachment=True,
                download_name=filename,
                mimetype="application/zip",
            )
        
        finally:
            # Clean up backup directory (optional, comment out if you want to keep backups)
            import shutil
            try:
                shutil.rmtree(backup_path)
            except:
                pass  # Ignore cleanup errors

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


@backup_api_bp.route("/list", methods=["GET"])
@login_required
@monitor_performance
def list_backups():
    """
    List available backups for the current user
    """
    try:
        backup_manager = BackupManager()
        backups = backup_manager.list_backups(user_id=current_user.id)
        
        return jsonify({
            "success": True,
            "backups": backups,
            "count": len(backups)
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to list backups"}), 500


@backup_api_bp.route("/upload", methods=["POST"])
@login_required
@monitor_performance
def upload_backup():
    """
    Upload a backup file for restoration
    """
    try:
        from flask import request
        import tempfile
        import zipfile
        
        # Check if file was uploaded
        if 'backup_file' not in request.files:
            return jsonify({"success": False, "error": "No backup file provided"}), 400
        
        file = request.files['backup_file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        # Validate file type
        if not file.filename.lower().endswith('.zip'):
            return jsonify({"success": False, "error": "Invalid file type. Please upload a ZIP file"}), 400
        
        # Log upload attempt
        log_security_event(
            "backup_upload_attempted",
            {"user_id": current_user.id, "filename": file.filename, "timestamp": datetime.utcnow().isoformat()},
        )
        
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded file
            uploaded_file_path = os.path.join(temp_dir, "uploaded_backup.zip")
            file.save(uploaded_file_path)
            
            # Extract ZIP file
            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir)
            
            try:
                with zipfile.ZipFile(uploaded_file_path, 'r') as zipf:
                    zipf.extractall(extract_dir)
            except zipfile.BadZipFile:
                return jsonify({"success": False, "error": "Invalid ZIP file format"}), 400
            
            # Validate backup structure
            metadata_path = os.path.join(extract_dir, "metadata.json")
            if not os.path.exists(metadata_path):
                return jsonify({"success": False, "error": "Invalid backup file - missing metadata"}), 400
            
            # Read and validate metadata
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Basic validation
                required_fields = ['backup_id', 'user_id', 'timestamp']
                if not all(field in metadata for field in required_fields):
                    return jsonify({"success": False, "error": "Invalid backup metadata"}), 400
                
            except (json.JSONDecodeError, Exception):
                return jsonify({"success": False, "error": "Invalid metadata format"}), 400
            
            # Store backup in permanent location
            backup_manager = BackupManager()
            backup_name = f"restored_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            permanent_backup_path = os.path.join(backup_manager.backup_dir, backup_name)
            
            # Copy extracted files to permanent location
            import shutil
            shutil.copytree(extract_dir, permanent_backup_path)
            
            # Update metadata with upload info
            metadata['uploaded_by'] = current_user.id
            metadata['upload_timestamp'] = datetime.utcnow().isoformat()
            metadata['original_filename'] = file.filename
            
            # Save updated metadata
            with open(os.path.join(permanent_backup_path, "metadata.json"), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            log_security_event(
                "backup_uploaded_successfully",
                {
                    "user_id": current_user.id,
                    "backup_id": metadata.get('backup_id'),
                    "backup_path": backup_name,
                    "timestamp": datetime.utcnow().isoformat()
                },
            )
            
            return jsonify({
                "success": True,
                "message": "Backup uploaded successfully",
                "backup_info": {
                    "backup_id": metadata.get('backup_id'),
                    "original_timestamp": metadata.get('datetime'),
                    "original_user": metadata.get('user_id'),
                    "path": backup_name
                }
            })
    
    except Exception as e:
        log_security_event(
            "backup_upload_failed",
            {
                "user_id": current_user.id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        return jsonify({"success": False, "error": "Failed to upload backup"}), 500


@backup_api_bp.route("/restore", methods=["POST"])
@login_required
@monitor_performance
def restore_backup():
    """
    Restore data from an uploaded backup
    """
    try:
        from flask import request
        
        data = request.get_json()
        if not data or 'backup_path' not in data:
            return jsonify({"success": False, "error": "Backup path is required"}), 400
        
        backup_path = data['backup_path']
        
        # Log restore attempt
        log_security_event(
            "backup_restore_attempted",
            {"user_id": current_user.id, "backup_path": backup_path, "timestamp": datetime.utcnow().isoformat()},
        )
        
        # Perform restoration
        backup_manager = BackupManager()
        full_backup_path = os.path.join(backup_manager.backup_dir, backup_path)
        
        if not os.path.exists(full_backup_path):
            return jsonify({"success": False, "error": "Backup not found"}), 404
        
        # Restore the backup (with user verification)
        result = backup_manager.restore_backup(full_backup_path, user_id=current_user.id)
        
        if result['status'] == 'success':
            log_security_event(
                "backup_restored_successfully",
                {
                    "user_id": current_user.id,
                    "backup_path": backup_path,
                    "restored_records": result.get('database_restore', {}).get('total_restored', 0),
                    "restored_files": result.get('file_restore', {}).get('restored_files', 0),
                    "timestamp": datetime.utcnow().isoformat()
                },
            )
            
            return jsonify({
                "success": True,
                "message": "Backup restored successfully",
                "details": result
            })
        else:
            log_security_event(
                "backup_restore_failed",
                {
                    "user_id": current_user.id,
                    "backup_path": backup_path,
                    "error": result.get('message', 'Unknown error'),
                    "timestamp": datetime.utcnow().isoformat()
                },
            )
            
            return jsonify({
                "success": False,
                "error": result.get('message', 'Restore failed'),
                "details": result
            }), 400
    
    except Exception as e:
        log_security_event(
            "backup_restore_error",
            {
                "user_id": current_user.id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        return jsonify({"success": False, "error": "Failed to restore backup"}), 500

"""
Backup blueprint for managing local data backups.
"""

import os

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required

from ..utils.backup_manager import BackupManager

backup_bp = Blueprint("backup", __name__, url_prefix="/backup")


@backup_bp.route("/")
@login_required
def index():
    """Backup management page"""
    # Initialize backup manager
    backup_manager = BackupManager()

    # Get list of available backups for the current user
    backups = backup_manager.list_backups(current_user.id)

    return render_template("backup/index.html", backups=backups)


@backup_bp.route("/create", methods=["POST"])
@login_required
def create_backup():
    """Create a new backup"""
    # Get backup options from form
    include_files = request.form.get("include_files", "yes") == "yes"

    # Initialize backup manager
    backup_manager = BackupManager()

    try:
        # Create the backup
        backup_path = backup_manager.create_backup(
            user_id=current_user.id, include_files=include_files
        )

        # Get the backup name from the path
        backup_name = os.path.basename(backup_path)

        flash(f"Backup created successfully: {backup_name}", "success")
    except Exception as e:
        flash(f"Error creating backup: {e!s}", "danger")

    return redirect(url_for("backup.index"))


@backup_bp.route("/restore/<backup_id>", methods=["POST"])
@login_required
def restore_backup(backup_id):
    """Restore from a backup"""
    # Initialize backup manager
    backup_manager = BackupManager()

    # Find the backup by ID
    backups = backup_manager.list_backups(current_user.id)
    selected_backup = None

    for backup in backups:
        if backup.get("backup_id") == backup_id:
            selected_backup = backup
            break

    if not selected_backup:
        flash("Backup not found.", "danger")
        return redirect(url_for("backup.index"))

    try:
        # Restore the backup
        result = backup_manager.restore_backup(
            backup_path=selected_backup["path"], user_id=current_user.id
        )

        if result["status"] == "success":
            flash("Backup restored successfully.", "success")
        elif result["status"] == "partial":
            flash(
                "Backup partially restored. Some items could not be restored.",
                "warning",
            )
        else:
            flash(
                f"Error restoring backup: {result.get('message', 'Unknown error')}",
                "danger",
            )
    except Exception as e:
        flash(f"Error restoring backup: {e!s}", "danger")

    return redirect(url_for("backup.index"))


@backup_bp.route("/delete/<backup_id>", methods=["POST"])
@login_required
def delete_backup(backup_id):
    """Delete a backup"""
    # Initialize backup manager
    backup_manager = BackupManager()

    # Find the backup by ID
    backups = backup_manager.list_backups(current_user.id)
    selected_backup = None

    for backup in backups:
        if backup.get("backup_id") == backup_id:
            selected_backup = backup
            break

    if not selected_backup:
        flash("Backup not found.", "danger")
        return redirect(url_for("backup.index"))

    try:
        # Delete the backup
        result = backup_manager.delete_backup(
            backup_path=selected_backup["path"], user_id=current_user.id
        )

        if result["status"] == "success":
            flash("Backup deleted successfully.", "success")
        else:
            flash(
                f"Error deleting backup: {result.get('message', 'Unknown error')}",
                "danger",
            )
    except Exception as e:
        flash(f"Error deleting backup: {e!s}", "danger")

    return redirect(url_for("backup.index"))


@backup_bp.route("/download/<backup_id>", methods=["GET"])
@login_required
def download_backup(backup_id):
    """Download a backup archive"""
    # Initialize backup manager
    backup_manager = BackupManager()

    # Find the backup by ID
    backups = backup_manager.list_backups(current_user.id)
    selected_backup = None

    for backup in backups:
        if backup.get("backup_id") == backup_id:
            selected_backup = backup
            break

    if not selected_backup:
        flash("Backup not found.", "danger")
        return redirect(url_for("backup.index"))

    # Create a zip archive of the backup
    # This would typically involve compressing the backup directory
    # For now, we'll assume the backup path is the path to download

    try:
        # Send the backup directory as a download
        # In a production environment, you'd want to create a zip file first
        return send_file(
            selected_backup["path"],
            as_attachment=True,
            download_name=f"backup_{backup_id}.zip",
        )
    except Exception as e:
        flash(f"Error downloading backup: {e!s}", "danger")
        return redirect(url_for("backup.index"))

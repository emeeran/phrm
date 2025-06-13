"""
File Routes Module

This module contains route handlers for file upload and download operations.
"""

import mimetypes
import os

from flask import Blueprint, abort, current_app, send_from_directory
from flask_login import current_user, login_required

from ... import limiter
from ...models import Document, HealthRecord
from ...utils.shared import log_security_event, monitor_performance

file_routes = Blueprint("file_routes", __name__)


@file_routes.route("/uploads/<int:record_id>/<filename>")
@login_required
@limiter.limit("30 per minute")  # Rate limit file access
@monitor_performance
def serve_upload(record_id, filename):
    """Securely serve uploaded files"""
    try:
        # Validate filename security
        if not _validate_filename_security(filename, record_id):
            abort(404)

        # Get the record to check permissions
        record = HealthRecord.query.get_or_404(record_id)

        # Check file access permissions
        if not _check_file_access_permission(record):
            _handle_unauthorized_file_access(record_id, filename, record)

        # Verify document belongs to record
        if not _verify_document_belongs_to_record(record_id, filename):
            abort(404)

        # Check if file exists on disk
        file_directory = os.path.join(
            current_app.config["UPLOAD_FOLDER"], str(record_id)
        )
        file_path = os.path.join(file_directory, filename)

        # Validate file path security
        if not _validate_file_path_security(
            file_path, file_directory, record_id, filename
        ):
            abort(404)

        if not os.path.exists(file_path):
            current_app.logger.error(f"File not found on disk: {file_path}")
            abort(404)

        # Determine MIME type
        mimetype = _determine_file_mimetype(filename)

        # Log successful file access
        log_security_event(
            "file_accessed",
            {
                "user_id": current_user.id,
                "record_id": record_id,
                "filename": filename,
                "file_size": os.path.getsize(file_path),
            },
        )

        try:
            return send_from_directory(
                directory=file_directory,
                path=filename,
                mimetype=mimetype,
                as_attachment=False,  # Display inline for images and PDFs
            )
        except Exception as e:
            current_app.logger.error(f"Error serving file {file_path}: {e}")
            abort(404)

    except Exception as e:
        current_app.logger.error(f"Error in serve_upload: {e}")
        abort(404)


# Helper functions for file operations


def _validate_filename_security(filename, record_id):
    """Validate filename for security issues"""
    if not filename or ".." in filename or "/" in filename or "\\" in filename:
        log_security_event(
            "file_access_path_traversal_attempt",
            {
                "user_id": current_user.id,
                "filename": filename,
                "record_id": record_id,
            },
        )
        return False
    return True


def _check_file_access_permission(record):
    """Check if current user has permission to access files from this record"""
    if record.user_id == current_user.id:
        return True
    if record.family_member_id and record.family_member in current_user.family_members:
        return True
    return False


def _handle_unauthorized_file_access(record_id, filename, record):
    """Handle unauthorized file access attempt"""
    log_security_event(
        "unauthorized_file_access_attempt",
        {
            "user_id": current_user.id,
            "record_id": record_id,
            "filename": filename,
            "record_owner_id": record.user_id,
            "record_family_member_id": record.family_member_id,
        },
    )
    abort(404)  # Return 404 instead of 403 to avoid information disclosure


def _verify_document_belongs_to_record(record_id, filename):
    """Verify that the requested file belongs to this record"""
    document = (
        Document.query.filter_by(health_record_id=record_id)
        .filter(Document.file_path.endswith(filename))
        .first()
    )

    if not document:
        log_security_event(
            "file_access_invalid_document",
            {
                "user_id": current_user.id,
                "record_id": record_id,
                "filename": filename,
            },
        )
        return False
    return True


def _validate_file_path_security(file_path, file_directory, record_id, filename):
    """Validate file path for directory traversal attacks"""
    real_file_path = os.path.realpath(file_path)
    real_upload_dir = os.path.realpath(file_directory)

    if not real_file_path.startswith(real_upload_dir):
        log_security_event(
            "file_access_directory_traversal",
            {
                "user_id": current_user.id,
                "record_id": record_id,
                "filename": filename,
                "attempted_path": file_path,
            },
        )
        return False
    return True


def _determine_file_mimetype(filename):
    """Determine appropriate MIME type for file"""
    mimetype = mimetypes.guess_type(filename)[0]
    if not mimetype:
        if filename.lower().endswith(".pdf"):
            mimetype = "application/pdf"
        elif filename.lower().endswith((".jpg", ".jpeg")):
            mimetype = "image/jpeg"
        elif filename.lower().endswith(".png"):
            mimetype = "image/png"
        else:
            mimetype = "application/octet-stream"
    return mimetype

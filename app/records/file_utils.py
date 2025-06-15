"""
File Utilities Module

This module contains file handling utilities for the records module.
"""

import mimetypes
import os
import uuid
from typing import Any

from flask import current_app
from flask_login import current_user

from ..utils.ai_utils import extract_text_from_pdf
from ..utils.shared import (
    log_security_event,
    monitor_performance,
    secure_filename_enhanced,
    validate_file_type,
)


def _validate_and_secure_file(file) -> str:
    """Validate file and create secure filename"""
    if not file or not file.filename:
        raise ValueError("No file provided")

    if not validate_file_type(file.filename):
        raise ValueError("Invalid file type")

    # Create secure filename with unique prefix
    filename = secure_filename_enhanced(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"

    return unique_filename


def _create_upload_directory(record_id: int) -> str:
    """Create and secure upload directory"""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    record_folder = os.path.join(upload_folder, str(record_id))

    os.makedirs(record_folder, exist_ok=True)

    return record_folder


def _save_and_validate_file_size(file, file_path: str) -> int:
    """Save file and validate size constraints"""
    file.save(file_path)

    # Check file size
    file_size = os.path.getsize(file_path)
    max_file_size = current_app.config.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)

    if file_size > max_file_size:
        os.remove(file_path)
        raise ValueError(
            f"File too large. Maximum size is {max_file_size // (1024 * 1024)}MB"
        )

    return file_size


def _validate_saved_file_content(file_path: str, filename: str) -> None:
    """Validate saved file content for security"""
    # Additional security check after save
    if not validate_file_type(filename):
        os.remove(file_path)
        raise ValueError("File content validation failed")


def _extract_text_if_pdf(file_path: str, file_type: str, filename: str) -> str:
    """Extract text from PDF files if applicable"""
    extracted_text = ""

    if file_type.lower() == "pdf":
        try:
            extracted_text = extract_text_from_pdf(file_path)
        except Exception as e:
            current_app.logger.warning(
                f"Could not extract text from PDF {filename}: {e}"
            )

    return extracted_text


@monitor_performance
def save_document(file, record_id: int) -> dict[str, Any]:
    """Save an uploaded document and return file information"""
    try:
        # Validate and secure the file
        unique_filename = _validate_and_secure_file(file)

        # Create upload directory
        record_folder = _create_upload_directory(record_id)
        file_path = os.path.join(record_folder, unique_filename)

        # Save and validate file size
        file_size = _save_and_validate_file_size(file, file_path)

        # Determine file extension and MIME type
        file_extension = os.path.splitext(unique_filename)[1].lower().replace(".", "")
        content_type = _determine_file_mimetype(unique_filename)

        # Validate saved file content
        _validate_saved_file_content(file_path, unique_filename)

        # Extract text if PDF
        extracted_text = _extract_text_if_pdf(
            file_path, file_extension, unique_filename
        )

        return {
            "filename": unique_filename,
            "file_path": unique_filename,  # Store only filename, not full path
            "file_type": content_type,  # Return MIME type as file_type for compatibility
            "file_size": file_size,
            "extracted_text": extracted_text,
        }

    except Exception as e:
        current_app.logger.error(f"Error saving document: {e}")
        raise


def _determine_file_mimetype(filename: str) -> str:
    """Determine appropriate MIME type for file"""
    mimetype, _ = mimetypes.guess_type(filename)

    if not mimetype:
        # Default MIME types for common file extensions
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            mimetype = "application/pdf"
        elif ext in [".jpg", ".jpeg"]:
            mimetype = "image/jpeg"
        elif ext == ".png":
            mimetype = "image/png"
        else:
            mimetype = "application/octet-stream"

    return mimetype


def _validate_filename_security(filename: str, record_id: int) -> bool:
    """Validate filename for security issues"""
    # Check for directory traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename:
        log_security_event(
            "suspicious_filename",
            {
                "filename": filename,
                "record_id": record_id,
                "user_id": getattr(current_user, "id", None),
            },
        )
        return False

    return True


def _validate_file_path_security(
    file_path: str, file_directory: str, record_id: int, filename: str
) -> bool:
    """Validate file path for directory traversal attacks"""
    # Ensure the file path is within the expected directory
    try:
        real_file_path = os.path.realpath(file_path)
        real_directory = os.path.realpath(file_directory)

        if not real_file_path.startswith(real_directory):
            log_security_event(
                "directory_traversal_attempt",
                {
                    "attempted_path": file_path,
                    "record_id": record_id,
                    "filename": filename,
                    "user_id": getattr(current_user, "id", None),
                },
            )
            return False
    except Exception as e:
        current_app.logger.error(f"Error validating file path: {e}")
        return False

    return True

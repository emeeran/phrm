import hashlib
import mimetypes
import os
import uuid
from datetime import datetime

from flask import current_app

# Constants for magic values
HTTP_SUCCESS = 200
HTTP_NOT_FOUND = 404
HTTP_FORBIDDEN = 403
HTTP_SERVICE_UNAVAILABLE = 503

# Performance thresholds
SLOW_QUERY_THRESHOLD = 0.1  # 100ms
CACHE_HIT_THRESHOLD = 0.7  # 70%
MEMORY_WARNING_THRESHOLD = 80  # 80%
CPU_WARNING_THRESHOLD = 80  # 80%
RECOMMENDED_QUERY_THRESHOLD = 0.05  # 50ms

# Cache and monitoring limits
MAX_PERFORMANCE_ENTRIES = 100
MAX_QUERY_ENTRIES = 200
MAX_TEMPLATE_ENTRIES = 100
MIN_CACHE_HIT_RATE = 50
MIN_REQUESTS_FOR_ALERT = 100

# Content validation
MAX_CONTENT_LENGTH = 10000  # 10KB
MIN_CONTENT_LENGTH = 10
DEFAULT_AUTH_PARTS_COUNT = 2

# File size constants
BYTES_PER_KB = 1024


def get_file_hash(file_path):
    """Calculate SHA-256 hash of a file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def get_file_mime_type(file_path):
    """Get MIME type of a file"""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


def generate_unique_filename(original_filename):
    """Generate a unique filename to prevent collisions"""
    _, ext = os.path.splitext(original_filename)
    return f"{uuid.uuid4().hex}{ext}"


def format_datetime(dt):
    """Format datetime object for display"""
    if not dt:
        return ""
    return dt.strftime("%B %d, %Y %I:%M %p")


def format_date(dt):
    """Format date object for display"""
    if not dt:
        return ""
    return dt.strftime("%B %d, %Y")


def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    BYTES_PER_KB = 1024
    BYTES_PER_MB = BYTES_PER_KB * 1024
    BYTES_PER_GB = BYTES_PER_MB * 1024

    if size_bytes < BYTES_PER_KB:
        return f"{size_bytes} bytes"
    elif size_bytes < BYTES_PER_MB:
        return f"{size_bytes / BYTES_PER_KB:.1f} KB"
    elif size_bytes < BYTES_PER_GB:
        return f"{size_bytes / BYTES_PER_MB:.1f} MB"
    else:
        return f"{size_bytes / BYTES_PER_GB:.1f} GB"


def is_safe_file_type(filename):
    """Check if the file type is safe to upload"""
    allowed_extensions = {"pdf", "jpg", "jpeg", "png", "txt", "doc", "docx"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def get_records_by_type(user, record_type=None, limit=None):
    """Get health records filtered by type"""
    from ..models import HealthRecord

    query = HealthRecord.query.filter_by(user_id=user.id)

    if record_type:
        query = query.filter_by(record_type=record_type)

    query = query.order_by(HealthRecord.date.desc())

    if limit:
        query = query.limit(limit)

    return query.all()


def get_family_records(user, family_member_id=None, record_type=None, limit=None):
    """Get health records for family members"""
    from ..models import HealthRecord

    # Get all family member IDs
    if family_member_id:
        family_member_ids = [family_member_id]
    else:
        family_member_ids = [fm.id for fm in user.family_members]

    if not family_member_ids:
        return []

    query = HealthRecord.query.filter(
        HealthRecord.family_member_id.in_(family_member_ids)
    )

    if record_type:
        query = query.filter_by(record_type=record_type)

    query = query.order_by(HealthRecord.date.desc())

    if limit:
        query = query.limit(limit)

    return query.all()

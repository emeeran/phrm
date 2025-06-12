import hashlib
import mimetypes
import os
import uuid
from datetime import datetime

from flask import current_app


def get_file_hash(file_path):
    """Calculate SHA-256 hash of a file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def get_file_mime_type(file_path):
    """Get MIME type of a file"""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'

def generate_unique_filename(original_filename):
    """Generate a unique filename to prevent collisions"""
    _, ext = os.path.splitext(original_filename)
    return f"{uuid.uuid4().hex}{ext}"

def format_datetime(dt):
    """Format datetime object for display"""
    if not dt:
        return ""
    return dt.strftime('%B %d, %Y %I:%M %p')

def format_date(dt):
    """Format date object for display"""
    if not dt:
        return ""
    return dt.strftime('%B %d, %Y')

def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def is_safe_file_type(filename):
    """Check if the file type is safe to upload"""
    allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'txt', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

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

    query = HealthRecord.query.filter(HealthRecord.family_member_id.in_(family_member_ids))

    if record_type:
        query = query.filter_by(record_type=record_type)

    query = query.order_by(HealthRecord.date.desc())

    if limit:
        query = query.limit(limit)

    return query.all()

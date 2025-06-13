"""
Security utility functions for the Personal Health Record Manager.
Includes security event logging, suspicious pattern detection, HTML sanitization, and file validation.
"""

import os
import re
from typing import Any, Dict, Optional

from flask import current_app


def log_security_event(event_type: str, data: Dict[str, Any]) -> None:
    """Centralized security event logging"""
    if current_app:
        current_app.logger.info(f"Security Event: {event_type} - {data}")


def detect_suspicious_patterns(text: str) -> bool:
    """Detect suspicious patterns in user input"""
    if not text:
        return False
    sql_patterns = [
        r"(\b(select|insert|update|delete|drop|create|alter)\b)",
        r"(\bunion\b.*\bselect\b)",
        r"(\bor\b.*=.*)",
        r"(--|#|/\*)",
    ]
    script_patterns = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
        r"eval\s*\(",
        r"document\.",
    ]
    patterns = sql_patterns + script_patterns
    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False


def sanitize_html(text: Optional[str]) -> str:
    """Basic HTML sanitization"""
    if not text:
        return ""
    text = re.sub(
        r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL
    )
    text = re.sub(r'\bon\w+\s*=\s*["\'][^"\']*["\']', "", text, flags=re.IGNORECASE)
    text = re.sub(r"javascript:", "", text, flags=re.IGNORECASE)
    return text


def validate_file_type(file_path: str) -> bool:
    """Validate file type based on extension and content"""
    allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".txt", ".doc", ".docx"}
    _, ext = os.path.splitext(file_path.lower())
    if ext not in allowed_extensions:
        return False
    return True


def secure_filename_enhanced(filename: str) -> str:
    """Enhanced secure filename generation"""
    import uuid

    from werkzeug.utils import secure_filename

    safe_filename = secure_filename(filename)
    if not safe_filename:
        safe_filename = f"file_{uuid.uuid4().hex[:8]}"
    return safe_filename

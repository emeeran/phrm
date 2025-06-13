"""
Response and security headers utilities for the Personal Health Record Manager.
Includes security headers and audit logging.
"""

from typing import Any, Optional

from flask import current_app, request
from flask_login import current_user


def security_headers(response: Any) -> Any:
    """Add security headers to response"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com fonts.googleapis.com; font-src 'self' fonts.gstatic.com cdnjs.cloudflare.com; img-src 'self' data:;"
    )
    return response


def audit_log(action: str, details: Optional[dict[str, Any]] = None) -> None:
    """Log audit events for security tracking"""
    user_id = (
        current_user.id
        if current_user and current_user.is_authenticated
        else "anonymous"
    )
    ip_address = request.remote_addr if request else "unknown"
    if current_app:
        current_app.logger.info(
            f"AUDIT: {action} by user {user_id} from {ip_address} - Details: {details or {}}"
        )

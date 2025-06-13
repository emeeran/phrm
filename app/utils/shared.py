"""
Shared utility functions and decorators for the Personal Health Record Manager.
This module consolidates common functionality to eliminate redundancy.
"""

from typing import Any, Optional

from flask import current_app, jsonify, request
from flask_login import current_user

# Import functions to re-export for other modules
from .ai_security_stubs import (
    AISecurityManager,
    ai_audit_required,
    ai_security_required,
    secure_ai_response_headers,
)
from .auth_decorators import api_login_required, require_admin
from .email_utils import send_password_reset_email
from .performance_monitor import monitor_performance
from .security_utils import (
    detect_suspicious_patterns,
    log_security_event,
    sanitize_html,
    secure_filename_enhanced,
    validate_file_type,
)

# Explicitly define what this module exports
__all__ = [
    "AISecurityManager",
    # AI security
    "ai_audit_required",
    "ai_security_required",
    # Authentication
    "api_login_required",
    # Security functions
    "detect_suspicious_patterns",
    # Shared utility functions defined in this module
    "get_user_context",
    "log_security_event",
    # Performance monitoring
    "monitor_performance",
    "require_admin",
    "safe_jsonify",
    "sanitize_html",
    "secure_ai_response_headers",
    "secure_filename_enhanced",
    # Email utilities
    "send_password_reset_email",
    "validate_file_type",
]

# ============================================================================
# SHARED UTILITY FUNCTIONS
# ============================================================================


def get_user_context():
    """Get current user context for logging and security"""
    if current_user and current_user.is_authenticated:
        return {
            "user_id": current_user.id,
            "email": current_user.email,
            "is_admin": getattr(current_user, "is_admin", False),
        }
    return {"user_id": None, "email": "anonymous", "is_admin": False}


def safe_jsonify(data: dict[str, Any], status_code: int = 200) -> tuple:
    """Safely create JSON response with error handling"""
    try:
        return jsonify(data), status_code
    except Exception as e:
        current_app.logger.error(f"JSON serialization error: {e}")
        return jsonify({"error": "Internal server error"}), 500


def log_user_action(action: str, details: Optional[dict[str, Any]] = None):
    """Log user actions with context"""
    user_context = get_user_context()
    ip_address = request.remote_addr if request else "unknown"

    log_data = {
        "action": action,
        "user_context": user_context,
        "ip_address": ip_address,
        "endpoint": request.endpoint if request else "unknown",
        "details": details or {},
    }

    if current_app:
        current_app.logger.info(f"USER_ACTION: {log_data}")

    # Also use the security logging if available
    try:
        log_security_event(action, log_data)
    except Exception:
        pass  # Fallback logging already done above

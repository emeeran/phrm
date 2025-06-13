"""
Shared utility functions and decorators for the Personal Health Record Manager.
This module consolidates common functionality to eliminate redundancy.
"""

from typing import Any, Dict, Optional

from flask import current_app, jsonify, request
from flask_login import current_user

from .security_utils import log_security_event

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


def safe_jsonify(data: Dict[str, Any], status_code: int = 200) -> tuple:
    """Safely create JSON response with error handling"""
    try:
        return jsonify(data), status_code
    except Exception as e:
        current_app.logger.error(f"JSON serialization error: {e}")
        return jsonify({"error": "Internal server error"}), 500


def log_user_action(action: str, details: Optional[Dict[str, Any]] = None):
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

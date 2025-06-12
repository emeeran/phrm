"""
Shared utility functions and decorators for the Personal Health Record Manager.
This module consolidates common functionality to eliminate redundancy.
"""

import re
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional

from flask import current_app, jsonify, request
from flask_login import current_user

# ============================================================================
# SECURITY UTILITIES
# ============================================================================


def log_security_event(event_type: str, data: Dict[str, Any]) -> None:
    """Centralized security event logging"""
    if current_app:
        current_app.logger.info(f"Security Event: {event_type} - {data}")


def detect_suspicious_patterns(text: str) -> bool:
    """Detect suspicious patterns in user input"""
    if not text:
        return False

    # Common SQL injection patterns
    sql_patterns = [
        r"(\b(select|insert|update|delete|drop|create|alter)\b)",
        r"(\bunion\b.*\bselect\b)",
        r"(\bor\b.*=.*)",
        r"(--|#|/\*)",
    ]

    # Script injection patterns
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

    # Remove potentially dangerous tags and attributes
    import re

    # Remove script tags
    text = re.sub(
        r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL
    )

    # Remove dangerous attributes
    text = re.sub(r'\bon\w+\s*=\s*["\'][^"\']*["\']', "", text, flags=re.IGNORECASE)

    # Remove javascript: protocols
    text = re.sub(r"javascript:", "", text, flags=re.IGNORECASE)

    return text


def validate_file_type(file_path: str) -> bool:
    """Validate file type based on extension and content"""
    import os

    allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".txt", ".doc", ".docx"}

    # Check file extension
    _, ext = os.path.splitext(file_path.lower())
    if ext not in allowed_extensions:
        return False

    # Additional validation could be added here (file magic numbers, etc.)

    return True


def secure_filename_enhanced(filename: str) -> str:
    """Enhanced secure filename generation"""
    import uuid

    from werkzeug.utils import secure_filename

    # Use werkzeug's secure_filename as base
    safe_filename = secure_filename(filename)

    # If filename becomes empty after sanitization, generate a random one
    if not safe_filename:
        safe_filename = f"file_{uuid.uuid4().hex[:8]}"

    return safe_filename


# ============================================================================
# AUTHENTICATION & AUTHORIZATION DECORATORS
# ============================================================================


def api_login_required(view_function: Callable) -> Callable:
    """Unified API authentication decorator"""

    @wraps(view_function)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        user_ip = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)

        try:
            # Validate authorization header
            auth_result = _validate_authorization_header(user_ip)
            if auth_result:
                return auth_result

            # Parse and validate credentials
            credentials_result = _parse_and_validate_credentials(user_ip)
            if isinstance(credentials_result, tuple):  # Error response
                return credentials_result

            email, password = credentials_result

            # Authenticate user
            user = _authenticate_user(email, password, user_ip)
            if not user:
                return jsonify({"error": "Invalid credentials"}), 401

            # Log success and continue
            _log_successful_authentication(user, user_ip, start_time)
            kwargs["api_user"] = user
            return view_function(*args, **kwargs)

        except Exception as e:
            current_app.logger.error(f"API authentication error: {e}")
            log_security_event(
                "api_authentication_error",
                {"endpoint": request.endpoint, "ip_address": user_ip, "error": str(e)},
            )
            return jsonify({"error": "Authentication failed"}), 401

    return decorated_function


def _validate_authorization_header(user_ip):
    """Validate the Authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        log_security_event(
            "api_unauthorized_access",
            {
                "endpoint": request.endpoint,
                "ip_address": user_ip,
                "reason": "missing_authorization_header",
            },
        )
        return jsonify({"error": "Authorization header is required"}), 401
    return None


def _parse_and_validate_credentials(user_ip):
    """Parse and validate credentials from Authorization header"""
    auth_header = request.headers.get("Authorization")
    auth_parts = auth_header.split(" ", 1)

    # Import constant from utils
    from . import DEFAULT_AUTH_PARTS_COUNT

    if len(auth_parts) != DEFAULT_AUTH_PARTS_COUNT or auth_parts[0].lower() != "basic":
        log_security_event(
            "api_invalid_auth_format",
            {"endpoint": request.endpoint, "ip_address": user_ip},
        )
        return jsonify({"error": "Basic authorization is required"}), 401

    # Decode credentials
    import base64

    try:
        decoded = base64.b64decode(auth_parts[1]).decode("utf-8")
        if ":" not in decoded:
            raise ValueError("Invalid format")
        email, password = decoded.split(":", 1)
    except Exception:
        log_security_event(
            "api_invalid_credentials_format",
            {"endpoint": request.endpoint, "ip_address": user_ip},
        )
        return jsonify({"error": "Invalid credentials format"}), 401

    # Validate email and credentials
    if not _validate_email_and_security(email, password, user_ip):
        return jsonify({"error": "Invalid credentials"}), 401

    return email, password


def _validate_email_and_security(email, password, user_ip):
    """Validate email format and check for suspicious patterns"""
    email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    if not email_pattern.match(email):
        log_security_event(
            "api_invalid_email_format",
            {"endpoint": request.endpoint, "ip_address": user_ip},
        )
        return False

    if detect_suspicious_patterns(email) or detect_suspicious_patterns(password):
        log_security_event(
            "api_suspicious_credentials",
            {"endpoint": request.endpoint, "ip_address": user_ip},
        )
        return False

    return True


def _authenticate_user(email, password, user_ip):
    """Authenticate user with email and password"""
    from ..models import User

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        log_security_event(
            "api_invalid_credentials",
            {
                "endpoint": request.endpoint,
                "ip_address": user_ip,
                "email": email,
            },
        )
        return None
    return user


def _log_successful_authentication(user, user_ip, start_time):
    """Log successful authentication"""
    log_security_event(
        "api_authentication_success",
        {
            "user_id": user.id,
            "endpoint": request.endpoint,
            "ip_address": user_ip,
            "response_time": round((time.time() - start_time) * 1000, 2),
        },
    )


def require_admin(func: Callable) -> Callable:
    """Require admin privileges"""

    @wraps(func)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not current_user.is_authenticated or not current_user.is_admin:
            log_security_event(
                "admin_access_denied",
                {
                    "user_id": (
                        current_user.id if current_user.is_authenticated else None
                    ),
                    "endpoint": request.endpoint,
                },
            )
            return jsonify({"error": "Admin privileges required"}), 403
        return func(*args, **kwargs)

    return decorated_function


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================


def monitor_performance(func: Callable) -> Callable:
    """Performance monitoring decorator"""

    @wraps(func)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Log slow operations (> 1 second)
            if execution_time > 1.0:
                current_app.logger.warning(
                    f"Slow operation: {func.__name__} took {execution_time:.2f}s"
                )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            current_app.logger.error(
                f"Error in {func.__name__} after {execution_time:.2f}s: {e}"
            )
            raise

    return decorated_function


# ============================================================================
# RESPONSE AND SECURITY HEADERS
# ============================================================================


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


def audit_log(action: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Log audit events for security tracking"""
    user_id = (
        current_user.id
        if current_user and current_user.is_authenticated
        else "anonymous"
    )
    ip_address = request.remote_addr if request else "unknown"

    # Log audit entry
    if current_app:
        current_app.logger.info(
            f"AUDIT: {action} by user {user_id} from {ip_address} - Details: {details or {}}"
        )


def sanitize_input(data: str) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    if not data:
        return ""

    # Basic HTML escape
    import html

    sanitized = html.escape(data)

    # Additional sanitization
    sanitized = re.sub(r'[<>"\']', "", sanitized)

    return sanitized.strip()


# ============================================================================
# AI SECURITY STUBS (for future implementation)
# ============================================================================


def ai_security_required(*args: Any, **_kwargs: Any) -> Any:
    """Stub decorator for AI security (future implementation)"""

    def decorator(func: Callable) -> Callable:
        return func

    if len(args) == 1 and callable(args[0]):
        return args[0]
    return decorator


def secure_ai_response_headers(*args: Any, **_kwargs: Any) -> Any:
    """Stub decorator for secure AI response headers (future implementation)"""

    def decorator(func: Callable) -> Callable:
        return func

    if len(args) == 1 and callable(args[0]):
        return args[0]
    return decorator


def validate_medical_context_access(*args: Any, **_kwargs: Any) -> Any:
    """Stub decorator for medical context access validation (future implementation)"""

    def decorator(func: Callable) -> Callable:
        return func

    if len(args) == 1 and callable(args[0]):
        return args[0]
    return decorator


def ai_audit_required(*args: Any, **_kwargs: Any) -> Any:
    """Stub decorator for AI audit (future implementation)"""

    def decorator(func: Callable) -> Callable:
        return func

    if len(args) == 1 and callable(args[0]):
        return args[0]
    return decorator


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def send_password_reset_email(user: Any) -> bool:
    """Send password reset email (stub for future implementation)"""
    print(f"Would send password reset email to {user.email}")
    return True


class AISecurityManager:
    """Stub class for AI security management (future implementation)"""

    @staticmethod
    def validate_request(_data: Any) -> bool:
        return True

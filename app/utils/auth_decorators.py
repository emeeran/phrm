"""
Authentication and authorization decorators for the Personal Health Record Manager.
Includes API login, admin requirement, and related helpers.
"""

import base64
import re
import time
from functools import wraps
from typing import Any, Callable

from flask import current_app, jsonify, request
from flask_login import current_user

from ..models import User
from . import DEFAULT_AUTH_PARTS_COUNT
from .security_utils import detect_suspicious_patterns, log_security_event


def api_login_required(view_function: Callable) -> Callable:
    """Unified API authentication decorator"""

    @wraps(view_function)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        user_ip = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
        try:
            auth_result = _validate_authorization_header(user_ip)
            if auth_result:
                return auth_result
            credentials_result = _parse_and_validate_credentials(user_ip)
            if isinstance(credentials_result, tuple):
                return credentials_result
            email, password = credentials_result
            user = _authenticate_user(email, password, user_ip)
            if not user:
                return jsonify({"error": "Invalid credentials"}), 401
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
    auth_header = request.headers.get("Authorization")
    auth_parts = auth_header.split(" ", 1)
    if len(auth_parts) != DEFAULT_AUTH_PARTS_COUNT or auth_parts[0].lower() != "basic":
        log_security_event(
            "api_invalid_auth_format",
            {"endpoint": request.endpoint, "ip_address": user_ip},
        )
        return jsonify({"error": "Basic authorization is required"}), 401
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
    if not _validate_email_and_security(email, password, user_ip):
        return jsonify({"error": "Invalid credentials"}), 401
    return email, password


def _validate_email_and_security(email, password, user_ip):
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
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        log_security_event(
            "api_invalid_credentials",
            {"endpoint": request.endpoint, "ip_address": user_ip, "email": email},
        )
        return None
    return user


def _log_successful_authentication(user, user_ip, start_time):
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

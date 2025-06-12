"""
Centralized stub functions for missing utilities.
This module consolidates all stub functions to eliminate redundancy across the application.
"""
from typing import Any, Callable, Dict, Optional


def log_security_event(event_type: str, data: Dict[str, Any]) -> None:
    """Stub function for security event logging"""
    pass


def detect_suspicious_patterns(text: str) -> bool:
    """Stub function for suspicious pattern detection"""
    return False


def sanitize_html(text: Optional[str]) -> str:
    """Stub function for HTML sanitization"""
    return text if text else ""


def validate_file_type(file_path: str) -> bool:
    """Stub function for file type validation"""
    return True


def secure_filename_enhanced(filename: str) -> str:
    """Stub function for enhanced secure filename"""
    from werkzeug.utils import secure_filename
    return secure_filename(filename)


def send_password_reset_email(user: Any) -> bool:
    """Stub function for sending password reset emails"""
    print(f"Would send password reset email to {user.email}")
    return True


def require_admin(func: Callable) -> Callable:
    """Stub decorator for admin requirement"""
    return func


def monitor_performance(func: Callable) -> Callable:
    """Stub decorator for performance monitoring"""
    return func


def create_security_decorator(decorator_name: str) -> Callable:
    """Factory function to create security decorators"""
    def decorator(*args, **kwargs):
        def wrapper(func: Callable) -> Callable:
            return func

        if len(args) == 1 and callable(args[0]):
            return args[0]
        return wrapper

    return decorator


# Create all security decorators using the factory
ai_security_required = create_security_decorator("ai_security_required")
secure_ai_response_headers = create_security_decorator("secure_ai_response_headers")
validate_medical_context_access = create_security_decorator("validate_medical_context_access")
ai_audit_required = create_security_decorator("ai_audit_required")


class AISecurityManager:
    """Stub class for AI security management"""

    @staticmethod
    def validate_request(data: Dict[str, Any]) -> bool:
        return True


class PerformanceDashboard:
    """Stub class for performance dashboard"""

    @staticmethod
    def monitor_performance(*args, **kwargs) -> Callable:
        """Stub decorator for performance monitoring"""
        def decorator(func: Callable) -> Callable:
            return func

        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

    @staticmethod
    def handle_errors(*args, **kwargs) -> Callable:
        """Stub decorator for error handling"""
        def decorator(func: Callable) -> Callable:
            return func

        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

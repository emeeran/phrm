"""
Email utility functions for the Personal Health Record Manager.
Includes password reset email stub.
"""

from typing import Any


def send_password_reset_email(user: Any) -> bool:
    """Send password reset email (stub for future implementation)"""
    print(f"Would send password reset email to {user.email}")
    return True

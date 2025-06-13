"""
Email utility functions for the Personal Health Record Manager.
Includes password reset email functionality.
"""

from datetime import datetime
from typing import Any

from flask import current_app, url_for


def send_password_reset_email(user: Any) -> bool:
    """Send password reset email with reset token"""
    try:
        # Generate reset token
        reset_token = user.generate_reset_token()

        # Generate reset URL - handle both request context and standalone usage
        try:
            reset_url = url_for(
                "auth.reset_password", token=reset_token, _external=True
            )
        except RuntimeError:
            # Fallback for when no request context is available
            server_name = current_app.config.get("SERVER_NAME") or "localhost:5002"
            scheme = current_app.config.get("PREFERRED_URL_SCHEME", "http")
            reset_url = f"{scheme}://{server_name}/auth/reset-password/{reset_token}"

        # Email content
        subject = "Password Reset Request - Personal Health Record Manager"

        # For now, we'll print to console (in production, use proper email service)
        current_app.logger.info(f"Password reset email would be sent to {user.email}")
        current_app.logger.info(f"Reset URL: {reset_url}")

        print(f"\n{'=' * 80}")
        print("🔐 PASSWORD RESET EMAIL SENT")
        print(f"{'=' * 80}")
        print(f"📧 To: {user.email}")
        print(f"📋 Subject: {subject}")
        print(f"🔗 Reset URL: {reset_url}")
        print(f"⏰ Expires: {user.reset_token_expiry}")
        print(f"{'=' * 80}\n")

        # Also write to a file for easier debugging
        try:
            with open("password_reset_emails.log", "a") as f:
                f.write(f"\n[{datetime.now()}] Password Reset Email\n")
                f.write(f"To: {user.email}\n")
                f.write(f"Reset URL: {reset_url}\n")
                f.write(f"Expires: {user.reset_token_expiry}\n")
                f.write("-" * 50 + "\n")
        except Exception:
            pass  # Don't fail if we can't write to file

        # In production, replace this with actual email sending logic:
        # send_email(user.email, subject, text_body, html_body)

        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {e!s}")
        return False


def send_email(to_email: str, subject: str, _text_body: str, _html_body: str) -> bool:
    """
    Send email using configured email service.
    This is a placeholder for actual email implementation.
    """
    # TODO: Implement actual email sending using:
    # - Flask-Mail
    # - SendGrid
    # - AWS SES
    # - Or other email service

    print(f"Would send email to {to_email} with subject: {subject}")
    return True
    return True

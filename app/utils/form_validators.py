"""
Consolidated form validation utilities for the Personal Health Record Manager.
Provides common validation functions and form mixins to eliminate code duplication.
"""

from wtforms.validators import ValidationError

from ..models import User
from .shared import detect_suspicious_patterns

# ============================================================================
# BASE VALIDATION MIXINS
# ============================================================================


class ValidationMixin:
    """Base mixin for common validation functionality"""

    def validate_against_patterns(self, field, patterns=None):
        """Validate field against suspicious patterns"""
        if detect_suspicious_patterns(field.data):
            raise ValidationError("Input contains invalid characters.")


class EmailValidationMixin:
    """Mixin for email validation"""

    def validate_email(self, email):
        """Validate email uniqueness and format"""
        if detect_suspicious_patterns(email.data):
            raise ValidationError("Email contains invalid characters.")

        # Check uniqueness if this isn't the current user's email
        query = User.query.filter_by(email=email.data)

        # For profile forms, exclude current user
        if hasattr(self, "original_email") and self.original_email:
            if email.data != self.original_email:
                user = query.first()
                if user is not None:
                    raise ValidationError("Please use a different email address.")
        else:
            # For registration forms
            user = query.first()
            if user is not None:
                raise ValidationError("Please use a different email address.")


class SecurityValidationMixin:
    """Mixin for forms requiring security validation"""

    def validate_username(self, username):
        """Validate username for security and uniqueness"""
        if detect_suspicious_patterns(username.data):
            raise ValidationError("Username contains invalid characters.")

        # Check uniqueness if this isn't the current user's username
        query = User.query.filter_by(username=username.data)

        # For profile forms, exclude current user
        if hasattr(self, "original_username") and self.original_username:
            if username.data != self.original_username:
                user = query.first()
                if user is not None:
                    raise ValidationError("Please use a different username.")
        else:
            # For registration forms
            user = query.first()
            if user is not None:
                raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        """Validate email for security and uniqueness"""
        if detect_suspicious_patterns(email.data):
            raise ValidationError("Invalid email format.")

        # Check uniqueness if this isn't the current user's email
        query = User.query.filter_by(email=email.data)

        # For profile forms, exclude current user
        if hasattr(self, "original_email") and self.original_email:
            if email.data != self.original_email:
                user = query.first()
                if user is not None:
                    raise ValidationError("Please use a different email address.")
        else:
            # For registration forms
            user = query.first()
            if user is not None:
                raise ValidationError("Please use a different email address.")

    def validate_first_name(self, first_name):
        """Validate first name for security"""
        if detect_suspicious_patterns(first_name.data):
            raise ValidationError("First name contains invalid characters.")

    def validate_last_name(self, last_name):
        """Validate last name for security"""
        if detect_suspicious_patterns(last_name.data):
            raise ValidationError("Last name contains invalid characters.")

    def validate_password(self, password):
        """Validate password for security (for login forms)"""
        if detect_suspicious_patterns(password.data):
            raise ValidationError("Invalid password format.")


class PasswordValidationMixin:
    """Mixin for forms requiring password validation"""

    def validate_current_password(self, current_password):
        """Validate current password matches user's password"""
        from flask_login import current_user

        if not current_user.check_password(current_password.data):
            raise ValidationError("Current password is incorrect.")

    def validate_confirmation(self, confirmation):
        """Validate deletion confirmation"""
        if confirmation.data != "DELETE":
            raise ValidationError('You must type "DELETE" to confirm account deletion.')


def validate_record_content(content):
    """Validate health record content"""
    if not content or not content.strip():
        raise ValidationError("Content cannot be empty.")

    if detect_suspicious_patterns(content):
        raise ValidationError("Content contains invalid characters.")

    # Import constant from utils
    from . import MAX_CONTENT_LENGTH

    if len(content) > MAX_CONTENT_LENGTH:  # 10KB limit
        raise ValidationError("Content is too long. Maximum 10,000 characters allowed.")


def validate_file_upload(form_field):
    """Validate uploaded files"""
    from .shared import validate_file_type

    if not form_field.data:
        return

    file = form_field.data

    # Check file size (16MB limit)
    MAX_FILE_SIZE = 16 * 1024 * 1024
    if hasattr(file, "content_length") and file.content_length > MAX_FILE_SIZE:
        raise ValidationError("File size exceeds 16MB limit.")

    # Check file type
    if not validate_file_type(file.filename):
        raise ValidationError(
            "Invalid file type. Only PDF, JPG, PNG, TXT, DOC, and DOCX files are allowed."
        )


def validate_medical_data(data):
    """Validate medical-related data fields"""
    if detect_suspicious_patterns(data):
        raise ValidationError("Invalid characters detected in medical data.")

    # Additional medical data validation could be added here
    return True

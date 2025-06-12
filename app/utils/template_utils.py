"""
Template utilities for the Personal Health R    # Calculate basic age
    age = today.year - birth_date.year

    # Adjust if birthday hasn't occurred this year
    if today < birth_date.replace(year=today.year):
        age -= 1

    return int(age)nager.
Consolidates common template functions and filters.
"""
from datetime import datetime
from typing import Optional, Any, Dict

# ============================================================================
# TEMPLATE UTILITY FUNCTIONS
# ============================================================================

def get_record_badge_class(record_type: str) -> str:
    """Get the appropriate badge class for a record type"""
    badge_classes = {
        'complaint': 'bg-danger',
        'doctor_visit': 'bg-primary',
        'investigation': 'bg-purple',
        'prescription': 'bg-success',
        'lab_report': 'bg-warning',
        'note': 'bg-secondary'
    }
    return badge_classes.get(record_type, 'bg-info')


def get_record_icon(record_type: str) -> str:
    """Get the appropriate icon for a record type"""
    icons = {
        'complaint': 'fa-face-frown',
        'doctor_visit': 'fa-user-doctor',
        'investigation': 'fa-microscope',
        'prescription': 'fa-prescription',
        'lab_report': 'fa-flask',
        'note': 'fa-clipboard'
    }
    return icons.get(record_type, 'fa-file-medical')


def calculate_age(birth_date: Any) -> Optional[int]:
    """Calculate age in years from a birth date"""
    if birth_date is None:
        return None

    today = datetime.now().date()

    # Convert birth_date to date if it's a datetime object
    if hasattr(birth_date, 'date'):
        birth_date = birth_date.date()

    # Calculate age  
    age: int = today.year - birth_date.year

    # Adjust if birthday hasn't occurred this year
    if today < birth_date.replace(year=today.year):
        age -= 1

    return age


def format_date(value: Any, format_str: str = '%b %d, %Y') -> str:
    """Format date for display"""
    if value is None:
        return ''
    return str(value.strftime(format_str))


def nl2br(value: Optional[str]) -> str:
    """Convert newlines to HTML line breaks"""
    if value is None:
        return ''
    return value.replace('\n', '<br>')


def format_file_size(bytes_size: int) -> str:
    """Format file size in human readable format"""
    if bytes_size == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    size = float(bytes_size)
    i = 0

    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f} {size_names[i]}"


# ============================================================================
# TEMPLATE CONTEXT PROCESSORS
# ============================================================================

def get_template_utilities() -> Dict[str, Any]:
    """Get all template utility functions for injection into templates"""
    return {
        'now': datetime.now(),
        'get_record_badge_class': get_record_badge_class,
        'get_record_icon': get_record_icon,
        'calculate_age': calculate_age,
        'format_file_size': format_file_size
    }


def get_template_filters() -> Dict[str, Any]:
    """Get all template filters for registration with Jinja2"""
    return {
        'format_date': format_date,
        'nl2br': nl2br,
        'format_file_size': format_file_size
    }


# ============================================================================
# ADDITIONAL HELPER FUNCTIONS
# ============================================================================

def get_health_record_badge_class(record_type: str) -> str:
    """Get the appropriate badge class for a health record type (alias for get_record_badge_class)"""
    return get_record_badge_class(record_type)

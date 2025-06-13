"""
Input sanitization utilities for the Personal Health Record Manager.
Includes sanitize_input and related helpers.
"""

import html
import re


def sanitize_input(data: str) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    if not data:
        return ""
    sanitized = html.escape(data)
    sanitized = re.sub(r'[<>"]', "", sanitized)
    return sanitized.strip()

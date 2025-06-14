"""
Routes Module - Streamlined route initialization
"""

from .dashboard import dashboard_routes
from .family_members import family_member_routes
from .files import file_routes
from .medical_conditions import medical_conditions_routes
from .records import health_records_routes

__all__ = [
    "dashboard_routes",
    "family_member_routes",
    "file_routes",
    "health_records_routes",
    "medical_conditions_routes",
]

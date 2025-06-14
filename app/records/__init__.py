"""
Records Module - Streamlined health record management
"""

from flask import Blueprint

from .routes import (
    dashboard_routes,
    family_member_routes,
    file_routes,
    health_records_routes,
    medical_conditions_routes,
)

# Create main blueprint
records_bp = Blueprint("records", __name__, url_prefix="/records")

# Register route blueprints
records_bp.register_blueprint(dashboard_routes)
records_bp.register_blueprint(health_records_routes)
records_bp.register_blueprint(family_member_routes)
records_bp.register_blueprint(file_routes)
records_bp.register_blueprint(medical_conditions_routes)

__all__ = ["records_bp"]

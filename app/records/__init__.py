"""
Records Module

This module provides health record management functionality for the Personal Health Record Manager.
It includes health record CRUD operations, family member management, file handling, and dashboard views.

The module is organized into the following submodules:
- forms: Form definitions for health records and family members
- services: Business logic services for record operations
- file_utils: File upload and validation utilities
- routes: Route handlers organized by functionality
  - dashboard: Dashboard and overview functionality
  - records: Health record CRUD operations
  - family_members: Family member management
  - files: File upload/download operations
"""

from flask import Blueprint
from flask import Blueprint as _Blueprint

# Explicitly export only the main blueprint
__all__ = ["records_bp"]

# Import route modules
from .routes import (
    dashboard_routes,
    family_member_routes,
    file_routes,
    health_records_routes,
)

# Create main blueprint
records_bp: _Blueprint = Blueprint("records", __name__, url_prefix="/records")

# Register all route blueprints
records_bp.register_blueprint(dashboard_routes)
records_bp.register_blueprint(health_records_routes)
records_bp.register_blueprint(family_member_routes)
records_bp.register_blueprint(file_routes)

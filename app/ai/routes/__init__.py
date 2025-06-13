"""
AI Routes Package

This package contains Flask route handlers for AI-related endpoints.
"""

# Import and expose route blueprints
from .summarization import summarization_bp as summarization_routes

__all__ = ["summarization_routes"]

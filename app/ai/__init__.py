"""
AI Module

This module provides AI-powered features for the Personal Health Record Manager, including summarization, chat, and provider integrations.

Submodules:
- providers: Integrations for HuggingFace, GROQ, DeepSeek, OpenAI, etc.
- summarization: Summarization logic and helpers
- routes: Flask route handlers for AI endpoints
- utils: Shared AI utilities
"""

from flask import Blueprint

from .routes.chat import ai_chat_bp
from .routes.summarization import summarization_bp

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")
ai_bp.register_blueprint(summarization_bp)
ai_bp.register_blueprint(ai_chat_bp)

"""
AI Chat Routes

Main chat interface for AI-powered health assistance.
Uses modular components for response processing and provider management.
"""

import logging

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from ...models import HealthRecord

# Import modular components
from ..chat_handlers import (
    build_chat_context,
    clean_user_query,
    process_chat_response,
    validate_chat_request,
)
from ..chat_providers import (
    estimate_provider_availability,
    get_system_message_for_chat,
    try_ai_providers_for_chat,
)

logger = logging.getLogger(__name__)

# Constants
CHAT_CONTEXT_PREVIEW_LENGTH = 200

ai_chat_bp = Blueprint("ai_chat", __name__)


@ai_chat_bp.route("/")
@login_required
def chat_interface():
    """Render the main chat interface"""
    try:
        # Get user's recent health records for context
        recent_records = (
            HealthRecord.query.filter_by(user_id=current_user.id)
            .order_by(HealthRecord.date.desc())
            .limit(5)
            .all()
        )

        # Check AI provider availability
        provider_status = estimate_provider_availability()

        return render_template(
            "ai/chat.html",
            recent_records=recent_records,
            provider_status=provider_status,
            title="AI Health Assistant",
        )
    except Exception as e:
        logger.error(f"Error loading chat interface: {e}")
        return render_template("errors/500.html"), 500


@ai_chat_bp.route("/ask", methods=["POST"])
@login_required
def ask_ai():
    """Handle AI chat requests"""
    try:
        # Validate request
        data = request.get_json()
        is_valid, error_msg = validate_chat_request(data)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        # Clean and process user query
        user_query = clean_user_query(data.get("query", ""))
        conversation_context = data.get("context", "")

        # Get user's health records for context
        user_records = (
            HealthRecord.query.filter_by(user_id=current_user.id)
            .order_by(HealthRecord.date.desc())
            .limit(3)
            .all()
        )

        # Build chat context
        chat_context = build_chat_context(user_records, conversation_context)

        # Process the medical query with enhanced context from web search only
        try:
            from ...utils.web_search import search_web_for_medical_info, format_web_results_for_context, get_web_citations
            
            web_results = search_web_for_medical_info(user_query, max_results=3)
            enhanced_context = chat_context
            if web_results:
                web_context = format_web_results_for_context(web_results)
                enhanced_context += f"\n\nAdditional Context:\n{web_context}"
                search_citations = get_web_citations(web_results)
            else:
                search_citations = []
        except Exception as e:
            logger.warning(f"Web search failed, using basic context: {e}")
            enhanced_context = chat_context
            search_citations = []

        # Build the final prompt
        system_message = get_system_message_for_chat()

        user_prompt = f"""User Query: {user_query}

Health Context:
{chat_context}

Additional Medical Knowledge:
{enhanced_context}

Please provide a helpful, accurate response based on the available information."""

        # Get AI response
        ai_response = try_ai_providers_for_chat(system_message, user_prompt)

        if not ai_response:
            return (
                jsonify(
                    {"error": "Unable to generate response. Please try again later."}
                ),
                503,
            )

        # Process response with citations
        processed_response = process_chat_response(ai_response, search_citations)

        # Build response data
        response_data = {
            "response": processed_response,
            "has_context": bool(chat_context),
            "citation_count": len(search_citations) if search_citations else 0,
            "processing_time": "< 1s",  # Could be enhanced with actual timing
        }

        logger.info(f"Successfully processed chat query for user {current_user.id}")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        return (
            jsonify(
                {
                    "error": "An error occurred while processing your request. Please try again."
                }
            ),
            500,
        )


@ai_chat_bp.route("/status")
@login_required
def get_ai_status():
    """Get current AI provider status"""
    try:
        provider_status = estimate_provider_availability()

        return jsonify(
            {
                "providers": [
                    {"name": name, "available": available, "status": status}
                    for name, available, status in provider_status
                ],
                "timestamp": "now",  # Could use actual timestamp
            }
        )
    except Exception as e:
        logger.error(f"Error checking AI status: {e}")
        return jsonify({"error": "Unable to check AI status"}), 500


@ai_chat_bp.route("/context")
@login_required
def get_user_context():
    """Get user's health context for chat"""
    try:
        # Get recent health records
        recent_records = (
            HealthRecord.query.filter_by(user_id=current_user.id)
            .order_by(HealthRecord.date.desc())
            .limit(5)
            .all()
        )

        # Build context summary
        context_summary = []
        for record in recent_records:
            summary = {
                "id": record.id,
                "date": record.date.isoformat() if record.date else None,
                "chief_complaint": (
                    record.chief_complaint[:CHAT_CONTEXT_PREVIEW_LENGTH]
                    if record.chief_complaint
                    else None
                ),
                "diagnosis": (
                    record.diagnosis[:CHAT_CONTEXT_PREVIEW_LENGTH]
                    if record.diagnosis
                    else None
                ),
            }
            context_summary.append(summary)

        return jsonify(
            {
                "recent_records": context_summary,
                "record_count": len(recent_records),
                "has_health_data": len(recent_records) > 0,
            }
        )

    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        return jsonify({"error": "Unable to retrieve context"}), 500

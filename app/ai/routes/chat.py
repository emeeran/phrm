import logging

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user, login_required

from ...models import FamilyMember, HealthRecord
from ...utils.ai_helpers import (
    call_deepseek_api,
    call_groq_api,
    call_huggingface_api,
    call_medgemma_api,
)

logger = logging.getLogger(__name__)

ai_chat_bp = Blueprint("ai_chat", __name__)


def get_user_context(mode, patient_id=None):
    """Get user health context based on mode and patient selection"""
    if mode == "public":
        return ""

    try:
        if patient_id == "self" or not patient_id:
            return _get_user_records_context()
        else:
            return _get_family_member_records_context(patient_id)
    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        return ""


def _get_user_records_context():
    """Get current user's health records context"""
    records = (
        HealthRecord.query.filter_by(user_id=current_user.id)
        .order_by(HealthRecord.date.desc())
        .limit(10)
        .all()
    )

    if not records:
        return ""

    context = "User's recent health records:\n"
    for record in records[:5]:  # Limit to avoid token overflow
        context += _format_record_context(record)
    return context


def _get_family_member_records_context(patient_id):
    """Get family member's health records context"""
    family_member = FamilyMember.query.filter_by(
        id=patient_id, user_id=current_user.id
    ).first()

    if not family_member:
        return ""

    records = (
        HealthRecord.query.filter_by(family_member_id=family_member.id)
        .order_by(HealthRecord.date.desc())
        .limit(10)
        .all()
    )

    if not records:
        return ""

    context = f"{family_member.first_name}'s recent health records:\n"
    for record in records[:5]:
        context += _format_record_context(record)
    return context


def _format_record_context(record):
    """Format a single health record for context"""
    context = f"- {record.date}: {record.chief_complaint}"
    if record.diagnosis:
        context += f" | Diagnosis: {record.diagnosis}"
    if record.prescription:
        context += f" | Prescription: {record.prescription}"
    context += "\n"
    return context


def call_ai_with_fallback(
    system_message, user_message, temperature=0.3, max_tokens=2000
):
    """Call AI providers with fallback logic"""

    # Try MedGemma first (primary provider)
    try:
        logger.info("Attempting MedGemma API call...")
        response = call_medgemma_api(
            system_message, user_message, temperature, max_tokens
        )
        if response:
            logger.info("MedGemma API call successful")
            return response, "MedGemma"
    except Exception as e:
        logger.warning(f"MedGemma API failed: {e}")

    # Try HuggingFace general API
    try:
        logger.info("Attempting HuggingFace API call...")
        response = call_huggingface_api(
            system_message, user_message, temperature, max_tokens
        )
        if response:
            logger.info("HuggingFace API call successful")
            return response, "HuggingFace"
    except Exception as e:
        logger.warning(f"HuggingFace API failed: {e}")

    # Try GROQ as fallback
    try:
        logger.info("Attempting GROQ API call...")
        response = call_groq_api(system_message, user_message, temperature, max_tokens)
        if response:
            logger.info("GROQ API call successful")
            return response, "GROQ"
    except Exception as e:
        logger.warning(f"GROQ API failed: {e}")

    # Try DeepSeek as final fallback
    try:
        logger.info("Attempting DeepSeek API call...")
        response = call_deepseek_api(
            system_message, user_message, temperature, max_tokens
        )
        if response:
            logger.info("DeepSeek API call successful")
            return response, "DeepSeek"
    except Exception as e:
        logger.warning(f"DeepSeek API failed: {e}")

    return None, None


@ai_chat_bp.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    if request.method == "GET":
        return _handle_chat_get_request()

    if request.is_json:
        return _handle_chat_json_request()

    # Handle legacy form-based requests
    return _handle_chat_form_request()


def _handle_chat_get_request():
    """Handle GET request for chat interface"""
    family_members = current_user.family_members
    return render_template("ai/chatbot.html", family_members=family_members)


def _handle_chat_json_request():
    """Handle JSON request for chat API"""
    data = request.get_json()
    user_message = data.get("message", "").strip()
    mode = data.get("mode", "private")  # public or private
    patient_id = data.get("patient", "self")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    try:
        system_message = _build_system_message(mode, patient_id)
        ai_response = _get_ai_response(system_message, user_message)

        if ai_response:
            return jsonify(
                {"response": ai_response, "mode": mode, "patient": patient_id}
            )
        else:
            return jsonify({"error": "AI service unavailable"}), 503

    except Exception as e:
        current_app.logger.error(f"Chat error: {e}")
        return jsonify({"error": "Chat service error"}), 500


def _handle_chat_form_request():
    """Handle legacy form-based chat request"""
    # ...existing code...
    pass


def _build_system_message(mode, patient_id):
    """Build system message based on chat mode and patient selection"""
    if mode == "public":
        return """You are a helpful medical AI assistant. Provide general health information and guidance.
        Always remind users to consult with healthcare professionals for personalized medical advice.
        Do not provide specific diagnoses or treatment recommendations. Keep responses informative but not overly technical."""
    else:
        # Private mode - include user context
        user_context = get_user_context(mode, patient_id)
        if user_context:
            return f"""You are a personal health AI assistant with access to the user's medical records.
            Provide personalized health insights based on their history. Always remind users to consult with healthcare professionals.

            Medical History Context:
            {user_context}

            Use this context to provide more relevant and personalized responses."""
        else:
            return """You are a personal health AI assistant. Provide personalized health guidance and insights.
            Always remind users to consult with healthcare professionals for medical decisions."""


def _get_ai_response(system_message, user_message):
    """Get AI response with fallback logic"""
    ai_response, model_used = call_ai_with_fallback(system_message, user_message)
    return ai_response


def _handle_chat_form_request():
    """Handle legacy form-based chat request"""
    user_message = request.form.get("message")
    if user_message:
        try:
            system_message = """You are a helpful medical AI assistant. Provide general health information and guidance.
            Always remind users to consult with healthcare professionals for personalized medical advice."""

            ai_response, model_used = call_ai_with_fallback(
                system_message, user_message
            )
            if not ai_response:
                ai_response = "I'm sorry, I'm experiencing technical difficulties. Please try again later."
        except Exception as e:
            logger.error(f"Form chat error: {e}")
            ai_response = (
                "I encountered an error processing your request. Please try again."
            )
    else:
        ai_response = None

    family_members = current_user.family_members
    return render_template(
        "ai/chat.html",
        user_message=user_message,
        ai_response=ai_response,
        family_members=family_members,
    )

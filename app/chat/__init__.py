"""
Medical chat blueprint for public and private mode chat functionality.
"""

import uuid
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..models import db
from ..models.core.chat_message import ChatMessage
from ..models.core.family_member import FamilyMember

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.route("/")
@login_required
def index():
    """Chat interface main page"""
    # Get member_id from query params if specified
    member_id = request.args.get("member_id", "self")
    conversation_id = request.args.get("conversation_id")

    # Load family members for dropdown selector
    family_members = current_user.family_members

    # Set selected member
    selected_member = None
    if member_id != "self" and member_id.isdigit():
        selected_member = FamilyMember.query.filter_by(id=int(member_id)).first_or_404()
        # Security check
        if selected_member not in current_user.family_members:
            flash("You don't have access to this family member's chat.", "danger")
            return redirect(url_for("chat.index"))

    # Load conversation history
    conversations = ChatMessage.get_conversation_history(current_user.id)

    # Load messages for selected conversation
    messages = []
    if conversation_id:
        messages = ChatMessage.get_conversation(conversation_id, current_user.id)

    # Default mode is private
    chat_mode = request.args.get("mode", "private")

    return render_template(
        "chat/index.html",
        family_members=family_members,
        selected_member=selected_member,
        conversations=conversations,
        conversation_id=conversation_id,
        messages=messages,
        chat_mode=chat_mode,
    )


@chat_bp.route("/send", methods=["POST"])
@login_required
def send_message():
    """Send a new message and get AI response"""
    # Get message content
    content = request.form.get("content")
    if not content or content.strip() == "":
        return jsonify({"error": "Message content is required"}), 400

    # Get or create conversation ID
    conversation_id = request.form.get("conversation_id")
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    # Get chat mode
    is_private = request.form.get("mode", "private") == "private"

    # Get family member if specified
    family_member_id = request.form.get("member_id")
    family_member = None
    if family_member_id and family_member_id != "self" and family_member_id.isdigit():
        family_member = FamilyMember.query.filter_by(id=int(family_member_id)).first()
        # Security check
        if family_member and family_member not in current_user.family_members:
            return (
                jsonify(
                    {"error": "You don't have access to this family member's chat"}
                ),
                403,
            )

    # Create and save user message
    user_message = ChatMessage(
        user_id=current_user.id,
        family_member_id=family_member.id if family_member else None,
        content=content,
        is_from_user=True,
        is_private=is_private,
        conversation_id=conversation_id,
    )
    db.session.add(user_message)
    db.session.commit()

    # Get AI response (this would connect to your AI service)
    ai_response = _get_ai_response(content, is_private, family_member)

    # Create and save AI message
    ai_message = ChatMessage(
        user_id=current_user.id,
        family_member_id=family_member.id if family_member else None,
        content=ai_response["message"],
        is_from_user=False,
        is_private=is_private,
        conversation_id=conversation_id,
        message_type=ai_response["type"],
        response_source=ai_response["source"],
        response_time_ms=ai_response["time_ms"],
        parent_message_id=user_message.id,
    )
    db.session.add(ai_message)
    db.session.commit()

    return jsonify(
        {
            "conversation_id": conversation_id,
            "user_message": user_message.to_dict(),
            "ai_message": ai_message.to_dict(),
        }
    )


@chat_bp.route("/history")
@login_required
def conversation_history():
    """Get conversation history"""
    conversations = ChatMessage.get_conversation_history(current_user.id)
    return jsonify(conversations)


@chat_bp.route("/conversation/<conversation_id>")
@login_required
def get_conversation(conversation_id):
    """Get messages for a specific conversation"""
    messages = ChatMessage.get_conversation(conversation_id, current_user.id)
    return jsonify([msg.to_dict() for msg in messages])


@chat_bp.route("/settings")
@login_required
def settings():
    """Chat settings page"""
    return render_template("chat/settings.html")


def _get_ai_response(query, is_private, family_member=None):
    """
    Get AI response to user query

    Args:
        query: User's message
        is_private: Whether the chat is in private mode
        family_member: Optional family member object

    Returns:
        AI response with metadata
    """
    # In a real implementation, this would connect to your AI service
    # For now, return a placeholder response

    # Simple response logic
    if "hello" in query.lower() or "hi" in query.lower():
        message = "Hello! How can I help with your health questions today?"
    elif (
        "medicine" in query.lower()
        or "medication" in query.lower()
        or "drug" in query.lower()
    ):
        message = "If you have questions about medications, I can provide general information. For specific medical advice, please consult your healthcare provider."
    elif "appointment" in query.lower() or "schedule" in query.lower():
        message = "You can schedule a new appointment by going to the Appointments section and clicking 'Schedule New'."
    elif (
        "symptom" in query.lower() or "pain" in query.lower() or "feel" in query.lower()
    ):
        message = "I notice you're mentioning symptoms. While I can provide general information, please consult a healthcare professional for proper medical advice."
    else:
        message = "I'm your medical chat assistant. Please let me know how I can help with your health records or medical questions."

    # Add family member context if relevant
    if family_member:
        message = f"[Regarding {family_member.first_name}] " + message

    # Add privacy notice for public mode
    if not is_private:
        message += "\n\nNOTE: You are currently in PUBLIC chat mode. Do not share sensitive personal health information."

    return {
        "message": message,
        "type": "text",
        "source": "rule_based_system",
        "time_ms": 150,
    }

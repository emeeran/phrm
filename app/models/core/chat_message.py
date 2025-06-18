"""
Chat message model for the medical chat functionality with dual public/private mode.
"""

from datetime import datetime

from .base import db


class ChatMessage(db.Model):
    """Model for chat messages in the medical chat system"""

    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)

    # Message ownership and relationships
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    family_member_id = db.Column(
        db.Integer, db.ForeignKey("family_members.id"), nullable=True
    )

    # Message content
    content = db.Column(db.Text, nullable=False)

    # Message metadata
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_from_user = db.Column(
        db.Boolean, default=True
    )  # True if user sent, False if AI response

    # Chat mode
    is_private = db.Column(db.Boolean, default=True)  # Private or public mode

    # Message type
    message_type = db.Column(
        db.String(20),
        nullable=False,
        default="text",  # text, medicine_interaction, health_advice, etc.
    )

    # Conversation tracking
    conversation_id = db.Column(
        db.String(64), nullable=False
    )  # UUID for grouping conversations
    parent_message_id = db.Column(
        db.Integer, db.ForeignKey("chat_messages.id"), nullable=True
    )

    # Response metadata
    response_source = db.Column(
        db.String(50), nullable=True
    )  # Model name or source of information
    response_time_ms = db.Column(db.Integer, nullable=True)  # Response generation time

    # Health context
    related_health_record_id = db.Column(
        db.Integer, db.ForeignKey("health_records.id"), nullable=True
    )
    related_medication_id = db.Column(
        db.Integer, db.ForeignKey("current_medications.id"), nullable=True
    )
    related_condition_id = db.Column(
        db.Integer, db.ForeignKey("medical_conditions.id"), nullable=True
    )

    # Relationships
    user = db.relationship("User", backref=db.backref("chat_messages", lazy=True))
    family_member = db.relationship(
        "FamilyMember", backref=db.backref("chat_messages", lazy=True)
    )
    parent_message = db.relationship("ChatMessage", remote_side=[id], backref="replies")
    health_record = db.relationship(
        "HealthRecord", backref=db.backref("chat_references", lazy=True)
    )
    medication = db.relationship(
        "CurrentMedication", backref=db.backref("chat_references", lazy=True)
    )
    medical_condition = db.relationship(
        "MedicalCondition", backref=db.backref("chat_references", lazy=True)
    )

    def __repr__(self) -> str:
        sender = "User" if self.is_from_user else "AI"
        privacy = "Private" if self.is_private else "Public"
        return f"<ChatMessage {self.id} - {sender} - {privacy}>"

    def to_dict(self) -> dict:
        """Convert chat message to dictionary for API responses"""
        return {
            "id": self.id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "is_from_user": self.is_from_user,
            "is_private": self.is_private,
            "message_type": self.message_type,
            "conversation_id": self.conversation_id,
            "sender": self.user.username if self.is_from_user else "AI Assistant",
            "related_to_family_member": bool(self.family_member_id),
            "family_member_name": (
                f"{self.family_member.first_name} {self.family_member.last_name}"
                if self.family_member
                else None
            ),
        }

    @classmethod
    def get_conversation(cls, conversation_id, user_id):
        """Retrieve a full conversation by its ID"""
        return (
            cls.query.filter_by(conversation_id=conversation_id, user_id=user_id)
            .order_by(cls.timestamp)
            .all()
        )

    @classmethod
    def get_conversation_history(cls, user_id, limit=10):
        """Get list of recent conversations"""
        # Get unique conversation IDs ordered by most recent message
        query = (
            db.session.query(
                cls.conversation_id, db.func.max(cls.timestamp).label("last_message")
            )
            .filter_by(user_id=user_id)
            .group_by(cls.conversation_id)
            .order_by(db.desc("last_message"))
            .limit(limit)
        )

        conversation_ids = [row[0] for row in query.all()]

        # For each conversation, get the first message (usually the user query)
        conversations = []
        for conv_id in conversation_ids:
            first_msg = (
                cls.query.filter_by(conversation_id=conv_id, user_id=user_id)
                .order_by(cls.timestamp)
                .first()
            )

            if first_msg:
                conversations.append(
                    {
                        "conversation_id": conv_id,
                        "preview": (
                            first_msg.content[:50] + "..."
                            if len(first_msg.content) > 50
                            else first_msg.content
                        ),
                        "timestamp": first_msg.timestamp.isoformat(),
                        "is_private": first_msg.is_private,
                        "family_member_name": (
                            f"{first_msg.family_member.first_name}"
                            if first_msg.family_member
                            else "Self"
                        ),
                        "message_count": cls.query.filter_by(
                            conversation_id=conv_id, user_id=user_id
                        ).count(),
                    }
                )

        return conversations

"""
Personal Health Record Manager - Models

Modular model structure for maintainability and clear separation of concerns.
"""

# Import AI audit and compliance models
from .ai_audit import AIAuditLog, AIComplianceReport, AIDataAccess, AIOperationMetrics

# Import database instance and core models
from .core.base import db, user_family
from .core.health_record import AISummary, Document, HealthRecord
from .core.medical_condition import ConditionProgressNote, MedicalCondition
from .core.user import FamilyMember, User

# Import security models
from .security import AISecurityEvent

# Export all models for backward compatibility
__all__ = [
    # AI audit models
    "AIAuditLog",
    "AIComplianceReport",
    "AIDataAccess",
    "AIOperationMetrics",
    # Security models
    "AISecurityEvent",
    # Core models
    "AISummary",
    "ConditionProgressNote",
    "Document",
    "FamilyMember",
    "HealthRecord",
    "MedicalCondition",
    "User",
    # Database
    "db",
    "user_family",
]

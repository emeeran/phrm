"""
Health Metrics and Scoring Utilities

Provides health score calculations and wellness metrics for users.
"""

from datetime import datetime, timedelta

from ..models import HealthRecord, MedicalCondition


class HealthScoreCalculator:
    """Calculate comprehensive health scores for users"""

    # Scoring weights
    WEIGHTS = {
        "recent_activity": 0.3,
        "condition_management": 0.25,
        "medication_adherence": 0.2,
        "preventive_care": 0.15,
        "lifestyle_factors": 0.1,
    }

    def calculate_health_score(self, user_id: int) -> dict:
        """Calculate overall health score for a user"""
        scores = {
            "recent_activity": self._score_recent_activity(user_id),
            "condition_management": self._score_condition_management(user_id),
            "medication_adherence": self._score_medication_adherence(user_id),
            "preventive_care": self._score_preventive_care(user_id),
            "lifestyle_factors": self._score_lifestyle_factors(user_id),
        }

        # Calculate weighted total
        total_score = sum(
            scores[category] * self.WEIGHTS[category] for category in scores
        )

        return {
            "overall_score": round(total_score, 1),
            "category_scores": scores,
            "score_interpretation": self._interpret_score(total_score),
            "recommendations": self._generate_recommendations(scores),
        }

    def _score_recent_activity(self, user_id: int) -> float:
        """Score based on recent medical activity"""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_records = HealthRecord.query.filter(
            HealthRecord.user_id == user_id, HealthRecord.date >= thirty_days_ago
        ).count()

        # Score based on appropriate medical engagement
        if recent_records == 0:
            return 85.0  # Good - no recent issues
        elif recent_records <= 2:
            return 75.0  # Moderate activity
        else:
            return 60.0  # High activity might indicate health issues

    def _score_condition_management(self, user_id: int) -> float:
        """Score based on chronic condition management"""
        conditions = MedicalCondition.query.filter(
            MedicalCondition.user_id == user_id
        ).all()

        if not conditions:
            return 90.0  # No chronic conditions

        managed_conditions = sum(
            1
            for condition in conditions
            if condition.current_status in ["stable", "improving"]
        )

        if len(conditions) == 0:
            return 90.0

        management_ratio = managed_conditions / len(conditions)
        return 50.0 + (management_ratio * 40.0)  # 50-90 range

    def _score_medication_adherence(self, user_id: int) -> float:
        """Score based on medication adherence indicators"""
        # This is a simplified calculation - in reality, you'd track actual adherence
        recent_records = HealthRecord.query.filter(
            HealthRecord.user_id == user_id,
            HealthRecord.date >= datetime.now() - timedelta(days=90),
        ).all()

        prescription_records = [r for r in recent_records if r.prescription_entries]

        if not prescription_records:
            return 85.0  # No medications needed

        # Simple heuristic: regular check-ins suggest good adherence
        if len(prescription_records) >= 2:
            return 80.0
        else:
            return 70.0

    def _score_preventive_care(self, user_id: int) -> float:
        """Score based on preventive care activities"""
        one_year_ago = datetime.now() - timedelta(days=365)
        preventive_records = HealthRecord.query.filter(
            HealthRecord.user_id == user_id,
            HealthRecord.date >= one_year_ago,
            HealthRecord.appointment_type.in_(["routine", "preventive"]),
        ).count()

        if preventive_records >= 2:
            return 90.0
        elif preventive_records == 1:
            return 75.0
        else:
            return 60.0

    def _score_lifestyle_factors(self, user_id: int) -> float:
        """Score based on lifestyle indicators from records"""
        # This could be expanded with actual lifestyle data
        # For now, use a baseline score
        return 75.0

    def _interpret_score(self, score: float) -> str:
        """Interpret the health score"""
        if score >= 85:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 65:
            return "Fair"
        else:
            return "Needs Attention"

    def _generate_recommendations(self, scores: dict) -> list[str]:
        """Generate health recommendations based on scores"""
        recommendations = []

        if scores["recent_activity"] < 70:
            recommendations.append("Consider scheduling a routine check-up")

        if scores["condition_management"] < 70:
            recommendations.append("Review chronic condition management plan")

        if scores["medication_adherence"] < 70:
            recommendations.append("Discuss medication adherence with your doctor")

        if scores["preventive_care"] < 70:
            recommendations.append("Schedule preventive care appointments")

        if scores["lifestyle_factors"] < 70:
            recommendations.append("Consider lifestyle improvements")

        if not recommendations:
            recommendations.append(
                "Keep up the great work with your health management!"
            )

        return recommendations


def get_health_alerts(user_id: int) -> list[dict]:
    """Get health alerts for a user"""
    alerts = []

    # Check for overdue appointments
    six_months_ago = datetime.now() - timedelta(days=180)
    recent_routine = HealthRecord.query.filter(
        HealthRecord.user_id == user_id,
        HealthRecord.date >= six_months_ago,
        HealthRecord.appointment_type == "routine",
    ).first()

    if not recent_routine:
        alerts.append(
            {
                "type": "warning",
                "title": "Routine Check-up Overdue",
                "message": "Consider scheduling a routine health check-up",
                "action": "Schedule Appointment",
            }
        )

    # Check for medication follow-ups
    conditions = MedicalCondition.query.filter(
        MedicalCondition.user_id == user_id,
        MedicalCondition.current_status.in_(["active", "monitoring"]),
    ).all()

    for condition in conditions:
        if condition.condition_category == "chronic":
            last_update = condition.updated_at
            if last_update < datetime.now() - timedelta(days=90):
                alerts.append(
                    {
                        "type": "info",
                        "title": f"{condition.condition_name} Follow-up",
                        "message": "Consider updating condition status",
                        "action": "Update Condition",
                    }
                )

    return alerts


def get_health_trends(user_id: int) -> dict:
    """Get health trends for a user"""
    thirty_days_ago = datetime.now() - timedelta(days=30)
    sixty_days_ago = datetime.now() - timedelta(days=60)

    recent_records = HealthRecord.query.filter(
        HealthRecord.user_id == user_id, HealthRecord.date >= thirty_days_ago
    ).count()

    previous_records = HealthRecord.query.filter(
        HealthRecord.user_id == user_id,
        HealthRecord.date >= sixty_days_ago,
        HealthRecord.date < thirty_days_ago,
    ).count()

    trend = "stable"
    if recent_records > previous_records:
        trend = "increasing"
    elif recent_records < previous_records:
        trend = "decreasing"

    return {
        "record_activity": {
            "trend": trend,
            "recent_count": recent_records,
            "previous_count": previous_records,
        }
    }

"""
Notification System

Provides notification functionality for health reminders and alerts.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from ..models import HealthRecord, User


class NotificationType(Enum):
    """Types of notifications"""

    MEDICATION_REMINDER = "medication_reminder"
    APPOINTMENT_REMINDER = "appointment_reminder"
    HEALTH_CHECK = "health_check"
    INTERACTION_ALERT = "interaction_alert"
    SYSTEM_UPDATE = "system_update"


class NotificationPriority(Enum):
    """Notification priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    """Represents a notification"""

    id: str
    user_id: int
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    read_at: Optional[datetime] = None
    action_url: Optional[str] = None
    data: Optional[dict] = None

    @property
    def is_read(self) -> bool:
        return self.read_at is not None

    @property
    def is_overdue(self) -> bool:
        if not self.scheduled_for:
            return False
        return datetime.now() > self.scheduled_for


class NotificationManager:
    """Manages notifications for users"""

    def __init__(self):
        self.notifications: dict[int, list[Notification]] = {}

    def create_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        scheduled_for: Optional[datetime] = None,
        action_url: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(
            id=f"{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            created_at=datetime.now(),
            scheduled_for=scheduled_for,
            action_url=action_url,
            data=data or {},
        )

        # Add to user's notifications
        if user_id not in self.notifications:
            self.notifications[user_id] = []

        self.notifications[user_id].append(notification)
        return notification

    def get_user_notifications(
        self, user_id: int, unread_only: bool = False, limit: Optional[int] = None
    ) -> list[Notification]:
        """Get notifications for a user"""
        user_notifications = self.notifications.get(user_id, [])

        if unread_only:
            user_notifications = [n for n in user_notifications if not n.is_read]

        # Sort by priority and creation time
        priority_order = {
            NotificationPriority.URGENT: 0,
            NotificationPriority.HIGH: 1,
            NotificationPriority.MEDIUM: 2,
            NotificationPriority.LOW: 3,
        }

        user_notifications.sort(
            key=lambda n: (priority_order[n.priority], n.created_at), reverse=True
        )

        if limit:
            user_notifications = user_notifications[:limit]

        return user_notifications

    def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read"""
        for user_notifications in self.notifications.values():
            for notification in user_notifications:
                if notification.id == notification_id:
                    notification.read_at = datetime.now()
                    return True
        return False

    def generate_medication_reminders(self, user: User) -> list[Notification]:
        """Generate medication reminder notifications"""
        notifications = []

        # Get user's current medications from recent records
        recent_records = (
            HealthRecord.query.filter_by(user_id=user.id)
            .order_by(HealthRecord.date.desc())
            .limit(10)
            .all()
        )

        current_medications = []
        for record in recent_records:
            if record.current_medications:
                for med in record.current_medications:
                    if med.medication_name and med.frequency:
                        current_medications.append(med)

        # Create reminders for medications that need regular doses
        for medication in current_medications:
            if self._should_remind_medication(medication):
                notification = self.create_notification(
                    user_id=user.id,
                    notification_type=NotificationType.MEDICATION_REMINDER,
                    title=f"Medication Reminder: {medication.medication_name}",
                    message=f"Time to take your {medication.medication_name} ({medication.dosage})",
                    priority=NotificationPriority.HIGH,
                    scheduled_for=self._calculate_next_dose_time(medication),
                    action_url="/records/medications",
                    data={"medication_id": medication.id},
                )
                notifications.append(notification)

        return notifications

    def generate_health_check_reminders(self, user: User) -> list[Notification]:
        """Generate health check reminder notifications"""
        notifications = []

        # Check when user last had a checkup
        last_checkup = (
            HealthRecord.query.filter_by(user_id=user.id)
            .filter(
                HealthRecord.record_type.in_(
                    ["Physical Exam", "Annual Checkup", "Routine Visit"]
                )
            )
            .order_by(HealthRecord.date.desc())
            .first()
        )

        if not last_checkup or (datetime.now() - last_checkup.date).days > 365:
            notification = self.create_notification(
                user_id=user.id,
                notification_type=NotificationType.HEALTH_CHECK,
                title="Annual Health Checkup Due",
                message="It's been over a year since your last health checkup. Consider scheduling an appointment.",
                priority=NotificationPriority.MEDIUM,
                action_url="/records/create",
                data={"reminder_type": "annual_checkup"},
            )
            notifications.append(notification)

        return notifications

    def generate_interaction_alerts(
        self, user: User, medications: list[str]
    ) -> list[Notification]:
        """Generate medication interaction alerts"""
        from .medication_interactions import check_medication_interactions

        notifications = []
        interaction_summary = check_medication_interactions(medications)

        if interaction_summary["major_interactions"] > 0:
            notification = self.create_notification(
                user_id=user.id,
                notification_type=NotificationType.INTERACTION_ALERT,
                title="Major Medication Interaction Alert",
                message=f"Found {interaction_summary['major_interactions']} major medication interactions. Please consult your healthcare provider.",
                priority=NotificationPriority.URGENT,
                action_url="/records/medications",
                data={"interactions": interaction_summary["interactions"]},
            )
            notifications.append(notification)

        elif interaction_summary["moderate_interactions"] > 0:
            notification = self.create_notification(
                user_id=user.id,
                notification_type=NotificationType.INTERACTION_ALERT,
                title="Medication Interaction Notice",
                message=f"Found {interaction_summary['moderate_interactions']} moderate medication interactions. Please review with your healthcare provider.",
                priority=NotificationPriority.HIGH,
                action_url="/records/medications",
                data={"interactions": interaction_summary["interactions"]},
            )
            notifications.append(notification)

        return notifications

    def _should_remind_medication(self, medication) -> bool:
        """Determine if medication needs a reminder"""
        # Simple logic - could be enhanced with user preferences
        if not medication.frequency:
            return False

        frequency_lower = medication.frequency.lower()
        daily_keywords = ["daily", "once a day", "every day", "daily basis"]

        return any(keyword in frequency_lower for keyword in daily_keywords)

    def _calculate_next_dose_time(self, medication) -> datetime:
        """Calculate when the next dose should be taken"""
        # Simple calculation - could be enhanced with user's medication schedule
        now = datetime.now()

        # Default to next morning (8 AM) for daily medications
        next_dose = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if next_dose <= now:
            next_dose += timedelta(days=1)

        return next_dose

    def get_notification_summary(self, user_id: int) -> dict:
        """Get summary of user's notifications"""
        notifications = self.get_user_notifications(user_id)

        summary = {
            "total": len(notifications),
            "unread": len([n for n in notifications if not n.is_read]),
            "urgent": len(
                [n for n in notifications if n.priority == NotificationPriority.URGENT]
            ),
            "overdue": len([n for n in notifications if n.is_overdue]),
            "by_type": {},
        }

        for notification in notifications:
            type_name = notification.type.value
            if type_name not in summary["by_type"]:
                summary["by_type"][type_name] = 0
            summary["by_type"][type_name] += 1

        return summary


# Global notification manager instance
notification_manager = NotificationManager()


def get_user_notifications(user_id: int, **kwargs) -> list[Notification]:
    """Convenience function to get user notifications"""
    return notification_manager.get_user_notifications(user_id, **kwargs)


def create_notification(user_id: int, **kwargs) -> Notification:
    """Convenience function to create a notification"""
    return notification_manager.create_notification(user_id, **kwargs)

"""
Health status analyzer for individuals.

This module provides functionality to generate health status reports based on
medical records, conditions, and medications.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..models.core.current_medication import CurrentMedication
from ..models.core.health_record import HealthRecord
from ..models.core.medical_condition import MedicalCondition


class HealthStatusAnalyzer:
    """Utility for analyzing and reporting individual health status"""

    def __init__(
        self, user_id: Optional[int] = None, family_member_id: Optional[int] = None
    ):
        """
        Initialize the health status analyzer

        Args:
            user_id: ID of the user (if analyzing self)
            family_member_id: ID of the family member (if analyzing family member)
        """
        self.user_id = user_id
        self.family_member_id = family_member_id

    def generate_status_report(self) -> Dict:
        """
        Generate a comprehensive health status report

        Returns:
            Dictionary containing various health status metrics
        """
        record_summary = self._analyze_health_records()
        conditions = self._analyze_medical_conditions()
        medications = self._analyze_current_medications()
        upcoming_appointments = self._get_upcoming_appointments()
        recent_vitals = self._extract_recent_vitals()

        return {
            "record_summary": record_summary,
            "active_conditions": conditions["active"],
            "managed_conditions": conditions["managed"],
            "resolved_conditions": conditions["resolved"],
            "current_medications": medications,
            "upcoming_appointments": upcoming_appointments,
            "recent_vitals": recent_vitals,
            "last_checkup": self._get_last_checkup_date(),
            "next_recommended_checkup": self._calculate_next_checkup_date(),
            "alerts": self._generate_health_alerts(),
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _analyze_health_records(self) -> Dict:
        """Analyze health records to extract summary statistics"""
        # Query for records
        query = HealthRecord.query

        if self.family_member_id:
            query = query.filter_by(family_member_id=self.family_member_id)
        elif self.user_id:
            query = query.filter_by(user_id=self.user_id)

        records = query.order_by(HealthRecord.date.desc()).all()

        # Calculate summary statistics
        total_records = len(records)
        records_last_year = sum(
            1 for r in records if r.date >= datetime.utcnow() - timedelta(days=365)
        )

        # Get unique doctors visited
        unique_doctors = set()
        for record in records:
            if record.doctor:
                unique_doctors.add(record.doctor.lower())

        # Get doctor specialties
        specialties = {}
        for record in records:
            if record.doctor_specialty:
                specialty = record.doctor_specialty.lower()
                if specialty in specialties:
                    specialties[specialty] += 1
                else:
                    specialties[specialty] = 1

        # Recent records
        recent_records = []
        for record in records[:5]:  # Get 5 most recent records
            recent_records.append(
                {
                    "id": record.id,
                    "date": record.date.isoformat(),
                    "diagnosis": record.diagnosis,
                    "doctor": record.doctor,
                    "specialty": record.doctor_specialty,
                }
            )

        return {
            "total_records": total_records,
            "records_last_year": records_last_year,
            "unique_doctors": len(unique_doctors),
            "most_visited_specialties": sorted(
                specialties.items(), key=lambda x: x[1], reverse=True
            )[:3],
            "recent_records": recent_records,
        }

    def _analyze_medical_conditions(self) -> Dict:
        """Analyze medical conditions by status"""
        # Query for conditions
        query = MedicalCondition.query

        if self.family_member_id:
            query = query.filter_by(family_member_id=self.family_member_id)
        elif self.user_id:
            query = query.filter_by(user_id=self.user_id)

        conditions = query.all()

        # Categorize by status
        active = []
        managed = []
        resolved = []

        for condition in conditions:
            condition_data = {
                "id": condition.id,
                "name": condition.condition_name,
                "category": condition.condition_category,
                "diagnosed_date": (
                    condition.diagnosed_date.isoformat()
                    if condition.diagnosed_date
                    else None
                ),
                "severity": condition.severity,
                "current_treatments": condition.current_treatments,
            }

            if condition.current_status == "active":
                active.append(condition_data)
            elif condition.current_status == "managed":
                managed.append(condition_data)
            elif condition.current_status in ["resolved", "cured"]:
                resolved.append(condition_data)

        return {"active": active, "managed": managed, "resolved": resolved}

    def _analyze_current_medications(self) -> List[Dict]:
        """Analyze current medications"""
        # Query for medications
        query = CurrentMedication.query

        if self.family_member_id:
            query = query.filter_by(family_member_id=self.family_member_id)
        else:
            # For user, we need to get through health records
            return []  # TODO: Implement for user's own medications

        medications = query.all()

        # Format medication data
        med_data = []
        for med in medications:
            med_data.append(
                {
                    "id": med.id,
                    "medicine": med.medicine,
                    "strength": med.strength,
                    "schedule": {
                        "morning": med.morning,
                        "noon": med.noon,
                        "evening": med.evening,
                        "bedtime": med.bedtime,
                    },
                    "duration": med.duration,
                    "notes": med.notes,
                    "dosage_summary": med.dosage_summary,
                }
            )

        return med_data

    def _get_upcoming_appointments(self) -> List[Dict]:
        """Get upcoming appointments"""
        # This functionality will be implemented after creating the appointment routes
        # For now, return empty list as a placeholder
        return []

    def _extract_recent_vitals(self) -> Dict:
        """Extract recent vital signs from health records"""
        # In a real implementation, this would extract vital signs from records
        # For now, return placeholder data
        return {
            "blood_pressure": None,
            "heart_rate": None,
            "temperature": None,
            "respiratory_rate": None,
            "oxygen_saturation": None,
            "weight": None,
            "bmi": None,
            "last_updated": None,
        }

    def _get_last_checkup_date(self) -> Optional[str]:
        """Get the date of the last general checkup"""
        # Query for records that might be checkups
        query = HealthRecord.query

        if self.family_member_id:
            query = query.filter_by(family_member_id=self.family_member_id)
        elif self.user_id:
            query = query.filter_by(user_id=self.user_id)

        # Look for records that are likely checkups (by type or keywords)
        checkup_records = (
            query.filter(
                (HealthRecord.appointment_type.contains("checkup"))
                | (HealthRecord.appointment_type.contains("annual"))
                | (HealthRecord.appointment_type.contains("routine"))
            )
            .order_by(HealthRecord.date.desc())
            .first()
        )

        if checkup_records:
            return checkup_records.date.isoformat()

        return None

    def _calculate_next_checkup_date(self) -> Optional[str]:
        """Calculate when the next checkup should be scheduled"""
        last_checkup = self._get_last_checkup_date()

        if not last_checkup:
            return datetime.utcnow().isoformat()  # Recommend checkup now if none found

        last_date = datetime.fromisoformat(last_checkup)
        next_date = last_date + timedelta(days=365)  # Default to annual checkups

        if next_date < datetime.utcnow():
            return datetime.utcnow().isoformat()  # Checkup is overdue

        return next_date.isoformat()

    def _generate_health_alerts(self) -> List[Dict]:
        """Generate health alerts based on conditions, medications, and records"""
        alerts = []

        # Check for overdue checkup
        last_checkup = self._get_last_checkup_date()
        if not last_checkup or datetime.fromisoformat(
            last_checkup
        ) < datetime.utcnow() - timedelta(days=365):
            alerts.append(
                {
                    "type": "checkup",
                    "severity": "medium",
                    "message": "Annual checkup is overdue",
                }
            )

        # Check for active medical conditions
        conditions = self._analyze_medical_conditions()
        if conditions["active"]:
            for condition in conditions["active"]:
                if condition.get("severity") == "severe":
                    alerts.append(
                        {
                            "type": "condition",
                            "severity": "high",
                            "message": f"Active severe condition: {condition['name']}",
                        }
                    )

        return alerts

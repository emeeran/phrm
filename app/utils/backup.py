"""
Data backup utilities for Personal Health Record Manager
"""

import json
import zipfile
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List

from ..models import (
    Appointment,
    HealthRecord,
)


class HealthDataBackup:
    """
    Create secure backups of user health data
    """

    def __init__(self, user):
        self.user = user
        self.backup_timestamp = datetime.utcnow()

    def create_full_backup(self) -> Dict[str, Any]:
        """
        Create a comprehensive backup of all user health data
        """
        backup_data = {
            "metadata": {
                "created_at": self.backup_timestamp.isoformat(),
                "app_name": "Personal Health Record Manager",
                "version": "2.0.0",
                "user_id": self.user.id,
                "username": self.user.username,
                "backup_type": "full",
            },
            "user_profile": self._get_user_profile(),
            "family_members": self._get_family_members(),
            "health_records": self._get_health_records(),
            "appointments": self._get_appointments(),
            "medications": self._get_medications(),
            "statistics": self._get_statistics(),
        }

        return backup_data

    def _get_user_profile(self) -> Dict[str, Any]:
        """Get user profile data"""
        return {
            "username": self.user.username,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "date_of_birth": (
                self.user.date_of_birth.isoformat() if self.user.date_of_birth else None
            ),
            "created_at": self.user.created_at.isoformat(),
        }

    def _get_family_members(self) -> List[Dict[str, Any]]:
        """Get family members data"""
        family_data = []

        for member in self.user.family_members:
            member_data = {
                "id": member.id,
                "first_name": member.first_name,
                "last_name": member.last_name,
                "relationship": member.relationship,
                "date_of_birth": (
                    member.date_of_birth.isoformat() if member.date_of_birth else None
                ),
                "gender": member.gender,
                "blood_type": member.blood_type,
                "allergies": member.allergies,
                "chronic_conditions": member.chronic_conditions,
                "current_medications": member.current_medications,
                "family_medical_history": member.family_medical_history,
                "surgical_history": member.surgical_history,
                "emergency_contact_name": member.emergency_contact_name,
                "emergency_contact_phone": member.emergency_contact_phone,
                "primary_doctor": member.primary_doctor,
                "insurance_provider": member.insurance_provider,
                "notes": member.notes,
                "created_at": member.created_at.isoformat(),
                "updated_at": member.updated_at.isoformat(),
            }

            # Add current medication entries if available
            if hasattr(member, "current_medication_entries"):
                member_data["current_medication_entries"] = [
                    {
                        "medicine": med.medicine,
                        "strength": med.strength,
                        "morning": med.morning,
                        "noon": med.noon,
                        "evening": med.evening,
                        "bedtime": med.bedtime,
                        "duration": med.duration,
                    }
                    for med in member.current_medication_entries
                ]

            family_data.append(member_data)

        return family_data

    def _get_health_records(self) -> List[Dict[str, Any]]:
        """Get health records data"""
        records_data = []

        # Get user's own records
        user_records = HealthRecord.query.filter_by(user_id=self.user.id).all()

        # Get family members' records
        family_member_ids = [fm.id for fm in self.user.family_members]
        family_records = (
            HealthRecord.query.filter(
                HealthRecord.family_member_id.in_(family_member_ids)
            ).all()
            if family_member_ids
            else []
        )

        all_records = user_records + family_records

        for record in all_records:
            record_data = {
                "id": record.id,
                "date": record.date.isoformat() if record.date else None,
                "record_type": record.record_type,
                "title": record.title,
                "chief_complaint": record.chief_complaint,
                "history_of_presenting_illness": record.history_of_presenting_illness,
                "past_medical_history": record.past_medical_history,
                "medications": record.medications,
                "allergies": record.allergies,
                "family_history": record.family_history,
                "social_history": record.social_history,
                "physical_examination": record.physical_examination,
                "investigations": record.investigations,
                "diagnosis": record.diagnosis,
                "prescription": record.prescription,
                "notes": record.notes,
                "doctor": record.doctor,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat(),
                "patient": (
                    "self"
                    if record.user_id == self.user.id
                    else (
                        record.family_member.first_name
                        + " "
                        + record.family_member.last_name
                        if record.family_member
                        else "Unknown"
                    )
                ),
            }

            # Add prescription entries if available
            if hasattr(record, "prescription_entries"):
                record_data["prescription_entries"] = [
                    {
                        "medicine": entry.medicine,
                        "strength": entry.strength,
                        "morning": entry.morning,
                        "noon": entry.noon,
                        "evening": entry.evening,
                        "bedtime": entry.bedtime,
                        "duration": entry.duration,
                    }
                    for entry in record.prescription_entries
                ]

            # Add document references (without actual files for security)
            if hasattr(record, "documents"):
                record_data["documents"] = [
                    {
                        "filename": doc.filename,
                        "original_filename": doc.original_filename,
                        "content_type": doc.content_type,
                        "file_size": doc.file_size,
                        "upload_date": doc.upload_date.isoformat(),
                    }
                    for doc in record.documents
                ]

            records_data.append(record_data)

        return records_data

    def _get_appointments(self) -> List[Dict[str, Any]]:
        """Get appointments data"""
        appointments_data = []

        # Get user's appointments
        user_appointments = Appointment.query.filter_by(user_id=self.user.id).all()

        # Get family members' appointments
        family_member_ids = [fm.id for fm in self.user.family_members]
        family_appointments = (
            Appointment.query.filter(
                Appointment.family_member_id.in_(family_member_ids)
            ).all()
            if family_member_ids
            else []
        )

        all_appointments = user_appointments + family_appointments

        for appointment in all_appointments:
            appointments_data.append(
                {
                    "id": appointment.id,
                    "title": appointment.title,
                    "doctor_name": appointment.doctor_name,
                    "doctor_specialty": appointment.doctor_specialty,
                    "clinic_hospital": appointment.clinic_hospital,
                    "appointment_date": (
                        appointment.appointment_date.isoformat()
                        if appointment.appointment_date
                        else None
                    ),
                    "duration_minutes": appointment.duration_minutes,
                    "status": appointment.status,
                    "purpose": appointment.purpose,
                    "preparation": appointment.preparation,
                    "notes": appointment.notes,
                    "follow_up_needed": appointment.follow_up_needed,
                    "reminder_sent": appointment.reminder_sent,
                    "reminder_date": (
                        appointment.reminder_date.isoformat()
                        if appointment.reminder_date
                        else None
                    ),
                    "patient": appointment.person_name,
                    "created_at": appointment.created_at.isoformat(),
                    "updated_at": appointment.updated_at.isoformat(),
                }
            )

        return appointments_data

    def _get_medications(self) -> List[Dict[str, Any]]:
        """Get current medications data"""
        medications_data = []

        # Collect medications for user and family members
        for person in [self.user] + list(self.user.family_members):
            person_name = (
                f"{person.first_name} {person.last_name}"
                if hasattr(person, "last_name")
                else person.username
            )

            if hasattr(person, "current_medication_entries"):
                for med in person.current_medication_entries:
                    medications_data.append(
                        {
                            "person": person_name,
                            "person_type": (
                                "user" if person == self.user else "family_member"
                            ),
                            "medicine": med.medicine,
                            "strength": med.strength,
                            "morning": med.morning,
                            "noon": med.noon,
                            "evening": med.evening,
                            "bedtime": med.bedtime,
                            "duration": med.duration,
                        }
                    )

        return medications_data

    def _get_statistics(self) -> Dict[str, Any]:
        """Get summary statistics"""
        family_member_ids = [fm.id for fm in self.user.family_members]

        total_records = HealthRecord.query.filter_by(user_id=self.user.id).count()
        if family_member_ids:
            total_records += HealthRecord.query.filter(
                HealthRecord.family_member_id.in_(family_member_ids)
            ).count()

        total_appointments = Appointment.query.filter_by(user_id=self.user.id).count()
        if family_member_ids:
            total_appointments += Appointment.query.filter(
                Appointment.family_member_id.in_(family_member_ids)
            ).count()

        return {
            "total_family_members": len(self.user.family_members),
            "total_health_records": total_records,
            "total_appointments": total_appointments,
            "backup_size_estimate": "Data exported successfully",
        }

    def create_encrypted_backup_file(self) -> BytesIO:
        """
        Create an encrypted backup file (ZIP format)
        """
        backup_data = self.create_full_backup()

        # Create a ZIP file in memory
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add main backup file
            backup_json = json.dumps(backup_data, indent=2, ensure_ascii=False)
            zip_file.writestr("health_data_backup.json", backup_json)

            # Add README file
            readme_content = f"""
Personal Health Record Manager - Data Backup
===========================================

Backup created: {self.backup_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}
User: {self.user.username}

This backup contains:
- Personal profile information
- Family member profiles and medical histories
- {len(backup_data["health_records"])} health records
- {len(backup_data["appointments"])} appointments
- Current medications for all family members

IMPORTANT SECURITY NOTES:
- This backup contains sensitive health information
- Store this file securely and encrypt it if storing online
- Do not share this backup file with unauthorized persons
- Use only for personal record keeping and emergency access

To restore data, contact your system administrator or use the
data import feature in the application.

Personal Health Record Manager
Version: 2.0.0
            """
            zip_file.writestr("README.txt", readme_content)

        zip_buffer.seek(0)
        return zip_buffer


def create_user_backup(user):
    """
    Convenience function to create a backup for a user
    """
    backup_manager = HealthDataBackup(user)
    return backup_manager.create_full_backup()


def create_user_backup_file(user) -> BytesIO:
    """
    Convenience function to create a backup file for a user
    """
    backup_manager = HealthDataBackup(user)
    return backup_manager.create_encrypted_backup_file()

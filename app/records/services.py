"""
Records Services Module

This module contains business logic and service functions for records management.
It provides a clean interface for health record CRUD operations, file handling,
and family member management.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from flask import current_app, flash
from flask_login import current_user
from sqlalchemy.orm import Query
from werkzeug.datastructures import FileStorage

from ..models import Document, FamilyMember, HealthRecord, db
from ..utils.shared import (
    log_security_event,
    sanitize_html,
)
from .file_utils import save_document


class RecordService:
    """
    Service class for health record operations.

    This class provides methods for creating, updating, querying, and deleting
    health records, along with related document management functionality.
    """

    @staticmethod
    def create_record(form_data: dict[str, Any]) -> HealthRecord:
        """
        Create a new health record from form data.

        Args:
            form_data: Dictionary containing form field values

        Returns:
            HealthRecord: The created health record instance

        Raises:
            ValueError: If required fields are missing or invalid
            SecurityError: If suspicious patterns are detected in input
        """
        # Sanitize all text inputs
        chief_complaint = (
            sanitize_html(form_data["chief_complaint"])
            if form_data.get("chief_complaint")
            else None
        )
        doctor = sanitize_html(form_data["doctor"]) if form_data.get("doctor") else None
        investigations = (
            sanitize_html(form_data["investigations"])
            if form_data.get("investigations")
            else None
        )
        diagnosis = (
            sanitize_html(form_data["diagnosis"])
            if form_data.get("diagnosis")
            else None
        )
        prescription = (
            sanitize_html(form_data["prescription"])
            if form_data.get("prescription")
            else None
        )
        notes = sanitize_html(form_data["notes"]) if form_data.get("notes") else None
        review_followup = (
            sanitize_html(form_data["review_followup"])
            if form_data.get("review_followup")
            else None
        )

        # Create new health record
        record = HealthRecord(
            date=form_data["date"],
            chief_complaint=chief_complaint,
            doctor=doctor,
            investigations=investigations,
            diagnosis=diagnosis,
            prescription=prescription,
            notes=notes,
            review_followup=review_followup,
        )

        # Assign to user or family member
        if form_data["family_member"] == 0:
            record.user_id = current_user.id
        else:
            # Verify family member belongs to current user
            family_member = FamilyMember.query.get(form_data["family_member"])
            if family_member and family_member in current_user.family_members:
                record.family_member_id = family_member.id
            else:
                log_security_event(
                    "invalid_family_member_assignment",
                    {
                        "user_id": current_user.id,
                        "attempted_family_member_id": form_data["family_member"],
                    },
                )
                raise ValueError("Invalid family member selection")

        return record

    @staticmethod
    def update_record(record: HealthRecord, form_data: dict[str, Any]) -> HealthRecord:
        """
        Update an existing health record with new data.

        Args:
            record: The health record instance to update
            form_data: Dictionary containing updated field values

        Returns:
            HealthRecord: The updated health record instance

        Raises:
            ValueError: If form data is invalid
            SecurityError: If suspicious patterns are detected
        """
        # Sanitize and update all fields
        record.date = form_data["date"]
        record.chief_complaint = (
            sanitize_html(form_data["chief_complaint"])
            if form_data.get("chief_complaint")
            else None
        )
        record.doctor = (
            sanitize_html(form_data["doctor"]) if form_data.get("doctor") else None
        )
        record.investigations = (
            sanitize_html(form_data["investigations"])
            if form_data.get("investigations")
            else None
        )
        record.diagnosis = (
            sanitize_html(form_data["diagnosis"])
            if form_data.get("diagnosis")
            else None
        )
        record.prescription = (
            sanitize_html(form_data["prescription"])
            if form_data.get("prescription")
            else None
        )
        record.notes = (
            sanitize_html(form_data["notes"]) if form_data.get("notes") else None
        )
        record.review_followup = (
            sanitize_html(form_data["review_followup"])
            if form_data.get("review_followup")
            else None
        )

        return record

    @staticmethod
    def handle_document_uploads(record: HealthRecord, files: list[FileStorage]) -> int:
        """
        Handle multiple document uploads for a health record.

        Args:
            record: The health record to attach documents to
            files: List of uploaded file objects

        Returns:
            int: Number of successfully uploaded documents

        Raises:
            ValueError: If file validation fails
            IOError: If file save operation fails
        """
        if not files:
            return 0

        upload_count = 0
        for file in files:
            if file and file.filename:  # Check if file is not empty
                try:
                    file_info = save_document(file, record.id)

                    # Create document record
                    document = Document(
                        filename=file_info["filename"],
                        file_path=file_info["file_path"],
                        file_type=file_info["file_type"],
                        file_size=file_info["file_size"],
                        extracted_text=file_info["extracted_text"],
                        health_record_id=record.id,
                    )
                    db.session.add(document)
                    upload_count += 1
                except Exception as e:
                    current_app.logger.error(
                        f"Error uploading file {file.filename}: {e}"
                    )
                    flash(f"Error uploading file {file.filename}: {e!s}", "warning")

        return upload_count

    @staticmethod
    def check_record_permission(record: HealthRecord) -> bool:
        """Check if current user has permission to access the record"""
        if record.user_id and record.user_id == current_user.id:
            return True
        if record.family_member and record.family_member in current_user.family_members:
            return True
        return False


class FamilyMemberService:
    """Service class for family member operations"""

    @staticmethod
    def create_family_member(form_data: dict[str, Any]) -> FamilyMember:
        """Create a new family member from form data"""
        # Sanitize all inputs
        first_name = sanitize_html(form_data["first_name"].strip())
        last_name = sanitize_html(form_data["last_name"].strip())
        relationship = (
            sanitize_html(form_data["relationship"].strip())
            if form_data.get("relationship")
            else None
        )
        gender = (
            sanitize_html(form_data["gender"].strip())
            if form_data.get("gender")
            else None
        )
        blood_type = (
            sanitize_html(form_data["blood_type"].strip())
            if form_data.get("blood_type")
            else None
        )

        # Sanitize medical history fields
        family_medical_history = (
            sanitize_html(form_data["family_medical_history"])
            if form_data.get("family_medical_history")
            else None
        )
        surgical_history = (
            sanitize_html(form_data["surgical_history"])
            if form_data.get("surgical_history")
            else None
        )
        current_medications = (
            sanitize_html(form_data["current_medications"])
            if form_data.get("current_medications")
            else None
        )
        allergies = (
            sanitize_html(form_data["allergies"])
            if form_data.get("allergies")
            else None
        )
        chronic_conditions = (
            sanitize_html(form_data["chronic_conditions"])
            if form_data.get("chronic_conditions")
            else None
        )
        notes = sanitize_html(form_data["notes"]) if form_data.get("notes") else None

        family_member = FamilyMember(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=form_data.get("date_of_birth"),
            relationship=relationship,
            gender=gender,
            blood_type=blood_type,
            height=form_data.get("height"),
            weight=form_data.get("weight"),
            family_medical_history=family_medical_history,
            surgical_history=surgical_history,
            current_medications=current_medications,
            allergies=allergies,
            chronic_conditions=chronic_conditions,
            notes=notes,
        )

        return family_member

    @staticmethod
    def create_initial_medical_records(
        family_member: FamilyMember,
    ) -> list[HealthRecord]:
        """Create initial medical history records for a family member"""
        records_to_create = []

        if family_member.family_medical_history:
            records_to_create.append(
                HealthRecord(
                    title="Family Medical History",
                    record_type="note",
                    description=family_member.family_medical_history,
                    date=datetime.now(timezone.utc),
                    family_member_id=family_member.id,
                )
            )

        if family_member.surgical_history:
            records_to_create.append(
                HealthRecord(
                    title="Surgical History",
                    record_type="note",
                    description=family_member.surgical_history,
                    date=datetime.now(timezone.utc),
                    family_member_id=family_member.id,
                )
            )

        if family_member.current_medications:
            records_to_create.append(
                HealthRecord(
                    title="Current Medications",
                    record_type="prescription",
                    description=family_member.current_medications,
                    date=datetime.now(timezone.utc),
                    family_member_id=family_member.id,
                )
            )

        if family_member.allergies:
            records_to_create.append(
                HealthRecord(
                    title="Known Allergies",
                    record_type="note",
                    description=family_member.allergies,
                    date=datetime.now(timezone.utc),
                    family_member_id=family_member.id,
                )
            )

        if family_member.chronic_conditions:
            records_to_create.append(
                HealthRecord(
                    title="Chronic Conditions",
                    record_type="note",
                    description=family_member.chronic_conditions,
                    date=datetime.now(timezone.utc),
                    family_member_id=family_member.id,
                )
            )

        return records_to_create


class RecordQueryService:
    """Service class for record querying and filtering"""

    @staticmethod
    def build_records_query(
        family_member_id: Optional[int] = None,
        record_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Query:
        """Build a query for health records with filters"""
        query = HealthRecord.query

        # Apply family member filter
        if family_member_id is not None:
            if family_member_id == 0:
                # Show user's own records
                query = query.filter_by(user_id=current_user.id)
            else:
                # Verify family member belongs to current user and filter
                family_member = FamilyMember.query.get(family_member_id)
                if family_member and family_member in current_user.family_members:
                    query = query.filter_by(family_member_id=family_member_id)
                else:
                    # Return empty query for security
                    query = query.filter(False)
        else:
            # Show all user's records and family member records
            family_member_ids = [fm.id for fm in current_user.family_members]
            query = query.filter(
                (HealthRecord.user_id == current_user.id)
                | (HealthRecord.family_member_id.in_(family_member_ids))
            )

        # Apply record type filter
        if record_type:
            query = query.filter_by(record_type=record_type)

        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (HealthRecord.title.ilike(search_term))
                | (HealthRecord.description.ilike(search_term))
                | (HealthRecord.chief_complaint.ilike(search_term))
                | (HealthRecord.diagnosis.ilike(search_term))
                | (HealthRecord.notes.ilike(search_term))
            )

        return query.order_by(HealthRecord.date.desc())

    @staticmethod
    def get_dashboard_stats() -> dict[str, int]:
        """Get dashboard statistics for the current user"""
        # Count user's own records
        user_records_count = HealthRecord.query.filter_by(
            user_id=current_user.id
        ).count()

        # Count family member records
        family_member_ids = [fm.id for fm in current_user.family_members]
        family_records_count = (
            HealthRecord.query.filter(
                HealthRecord.family_member_id.in_(family_member_ids)
            ).count()
            if family_member_ids
            else 0
        )

        # Count family members
        family_members_count = len(current_user.family_members)

        # Count total documents
        all_record_ids = [
            r.id
            for r in HealthRecord.query.filter(
                (HealthRecord.user_id == current_user.id)
                | (HealthRecord.family_member_id.in_(family_member_ids))
            ).all()
        ]

        documents_count = (
            Document.query.filter(Document.health_record_id.in_(all_record_ids)).count()
            if all_record_ids
            else 0
        )

        return {
            "total_records": user_records_count + family_records_count,
            "user_records": user_records_count,
            "family_records": family_records_count,
            "family_members": family_members_count,
            "documents": documents_count,
        }

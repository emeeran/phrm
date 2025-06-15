"""
Export Routes Module

This module contains route handlers for data export and backup functionality.
"""

import json
from datetime import datetime
from io import BytesIO

from flask import (
    Blueprint,
    current_app,
    jsonify,
    send_file,
)
from flask_login import current_user, login_required
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from ... import limiter
from ...models import FamilyMember, HealthRecord
from ...utils.performance_monitor import monitor_performance
from ...utils.security_utils import log_security_event

export_routes = Blueprint("export_routes", __name__)


@export_routes.route("/export/pdf")
@login_required
@limiter.limit("5 per minute")
@monitor_performance
def export_pdf():
    """Export user's health records as PDF"""
    try:
        # Get user's records
        records = (
            HealthRecord.query.filter_by(user_id=current_user.id)
            .order_by(HealthRecord.date.desc())
            .all()
        )

        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Add title
        title = Paragraph(
            f"Health Records for {current_user.first_name} {current_user.last_name}",
            styles["Title"],
        )
        story.append(title)
        story.append(Spacer(1, 12))

        # Add export date
        export_date = Paragraph(
            f"Exported on: {datetime.now().strftime('%B %d, %Y')}", styles["Normal"]
        )
        story.append(export_date)
        story.append(Spacer(1, 24))

        # Add records
        for record in records:
            # Record header
            record_title = Paragraph(
                f"Record Date: {record.date.strftime('%B %d, %Y')}", styles["Heading2"]
            )
            story.append(record_title)

            # Record details
            if record.chief_complaint:
                story.append(
                    Paragraph(
                        f"<b>Chief Complaint:</b> {record.chief_complaint}",
                        styles["Normal"],
                    )
                )
            if record.doctor:
                story.append(
                    Paragraph(f"<b>Doctor:</b> {record.doctor}", styles["Normal"])
                )
            if record.diagnosis:
                story.append(
                    Paragraph(f"<b>Diagnosis:</b> {record.diagnosis}", styles["Normal"])
                )
            if record.prescription:
                story.append(
                    Paragraph(
                        f"<b>Prescription:</b> {record.prescription}", styles["Normal"]
                    )
                )
            if record.notes:
                story.append(
                    Paragraph(f"<b>Notes:</b> {record.notes}", styles["Normal"])
                )

            story.append(Spacer(1, 12))

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        # Log export
        log_security_event(
            "data_export",
            {"user_id": current_user.id, "type": "pdf", "records_count": len(records)},
        )

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"health_records_{current_user.id}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mimetype="application/pdf",
        )

    except Exception as e:
        current_app.logger.error(f"PDF export error: {e}")
        return jsonify({"error": "Export failed"}), 500


@export_routes.route("/export/json")
@login_required
@limiter.limit("5 per minute")
@monitor_performance
def export_json():
    """Export user's health records as JSON"""
    try:
        # Get user's records
        records = (
            HealthRecord.query.filter_by(user_id=current_user.id)
            .order_by(HealthRecord.date.desc())
            .all()
        )

        # Convert to JSON
        export_data = {
            "user": {
                "name": f"{current_user.first_name} {current_user.last_name}",
                "email": current_user.email,
                "export_date": datetime.now().isoformat(),
            },
            "records": [],
        }

        for record in records:
            record_data = {
                "id": record.id,
                "date": record.date.isoformat(),
                "chief_complaint": record.chief_complaint,
                "doctor": record.doctor,
                "diagnosis": record.diagnosis,
                "prescription": record.prescription,
                "notes": record.notes,
                "created_at": (
                    record.created_at.isoformat() if record.created_at else None
                ),
            }
            export_data["records"].append(record_data)

        # Create JSON file
        json_data = json.dumps(export_data, indent=2)
        buffer = BytesIO(json_data.encode("utf-8"))

        # Log export
        log_security_event(
            "data_export",
            {"user_id": current_user.id, "type": "json", "records_count": len(records)},
        )

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"health_records_{current_user.id}_{datetime.now().strftime('%Y%m%d')}.json",
            mimetype="application/json",
        )

    except Exception as e:
        current_app.logger.error(f"JSON export error: {e}")
        return jsonify({"error": "Export failed"}), 500


@export_routes.route("/backup/create")
@login_required
@limiter.limit("2 per hour")
@monitor_performance
def create_backup():
    """Create a complete backup of user's data"""
    try:
        # Get all user data
        records = HealthRecord.query.filter_by(user_id=current_user.id).all()
        family_members = FamilyMember.query.filter_by(user_id=current_user.id).all()

        backup_data = {
            "backup_info": {
                "user_id": current_user.id,
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
            },
            "user_profile": {
                "username": current_user.username,
                "email": current_user.email,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "date_of_birth": (
                    current_user.date_of_birth.isoformat()
                    if current_user.date_of_birth
                    else None
                ),
            },
            "health_records": [],
            "family_members": [],
        }

        # Add health records
        for record in records:
            record_data = {
                "id": record.id,
                "date": record.date.isoformat(),
                "chief_complaint": record.chief_complaint,
                "doctor": record.doctor,
                "diagnosis": record.diagnosis,
                "prescription": record.prescription,
                "notes": record.notes,
                "family_member_id": record.family_member_id,
                "created_at": (
                    record.created_at.isoformat() if record.created_at else None
                ),
            }
            backup_data["health_records"].append(record_data)

        # Add family members
        for member in family_members:
            member_data = {
                "id": member.id,
                "first_name": member.first_name,
                "last_name": member.last_name,
                "relationship": member.relationship,
                "date_of_birth": (
                    member.date_of_birth.isoformat() if member.date_of_birth else None
                ),
                "medical_history": member.medical_history,
                "allergies": member.allergies,
                "chronic_conditions": member.chronic_conditions,
                "created_at": (
                    member.created_at.isoformat() if member.created_at else None
                ),
            }
            backup_data["family_members"].append(member_data)

        # Create backup file
        json_data = json.dumps(backup_data, indent=2)
        buffer = BytesIO(json_data.encode("utf-8"))

        # Log backup creation
        log_security_event(
            "data_backup",
            {
                "user_id": current_user.id,
                "records_count": len(records),
                "family_members_count": len(family_members),
            },
        )

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"phrm_backup_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mimetype="application/json",
        )

    except Exception as e:
        current_app.logger.error(f"Backup creation error: {e}")
        return jsonify({"error": "Backup creation failed"}), 500

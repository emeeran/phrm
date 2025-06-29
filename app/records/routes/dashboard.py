"""
Dashboard Routes Module

This module contains route handlers for the dashboard functionality.
"""

from datetime import datetime, timedelta

from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import and_

from ...models import Appointment, HealthRecord
from ...utils.shared import monitor_performance

dashboard_routes = Blueprint("dashboard_routes", __name__)


@dashboard_routes.route("/dashboard")
@login_required
@monitor_performance
def dashboard():
    """Enhanced dashboard showing comprehensive health overview"""
    # Get latest records
    own_records = (
        HealthRecord.query.filter_by(user_id=current_user.id)
        .order_by(HealthRecord.date.desc())
        .limit(5)
        .all()
    )

    # Get family members
    family_members = current_user.family_members

    # Get family records if there are family members
    family_records = []
    if family_members:
        family_member_ids = [fm.id for fm in family_members]
        family_records = (
            HealthRecord.query.filter(
                HealthRecord.family_member_id.in_(family_member_ids)
            )
            .order_by(HealthRecord.date.desc())
            .limit(5)
            .all()
        )

    # Get upcoming appointments (next 30 days)
    today = datetime.utcnow()
    upcoming_appointments = (
        Appointment.query.filter(
            and_(
                Appointment.appointment_date >= today,
                Appointment.appointment_date <= today + timedelta(days=30),
                Appointment.status == "scheduled",
            )
        )
        .filter(
            (Appointment.user_id == current_user.id)
            | (
                Appointment.family_member_id.in_([fm.id for fm in family_members])
                if family_members
                else False
            )
        )
        .order_by(Appointment.appointment_date.asc())
        .limit(10)
        .all()
    )

    # Get today's appointments
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    today_appointments = (
        Appointment.query.filter(
            and_(
                Appointment.appointment_date >= today_start,
                Appointment.appointment_date < today_end,
                Appointment.status == "scheduled",
            )
        )
        .filter(
            (Appointment.user_id == current_user.id)
            | (
                Appointment.family_member_id.in_([fm.id for fm in family_members])
                if family_members
                else False
            )
        )
        .all()
    )

    # Get current medications for user and family
    current_medications = []

    # Only family members have current medications (not the user directly)
    for member in family_members:
        if hasattr(member, "current_medication_entries"):
            for med in member.current_medication_entries:
                current_medications.append(
                    {
                        "person": f"{member.first_name} {member.last_name}",
                        "medicine": med.medicine,
                        "strength": med.strength,
                        "morning": med.morning,
                        "noon": med.noon,
                        "evening": med.evening,
                        "bedtime": med.bedtime,
                        "duration": med.duration,
                    }
                )

    # Calculate dashboard statistics
    total_records = len(own_records) + len(family_records)
    total_members = len(family_members)
    upcoming_count = len(upcoming_appointments)
    medications_count = len(current_medications)

    # RAG system has been removed - provide empty status
    rag_status = {
        "available": False,
        "chromadb_available": False,
        "processed_files_count": 0,
        "reason": "RAG system removed"
    }

    return render_template(
        "records/enhanced_dashboard.html",
        title="Health Dashboard",
        own_records=own_records,
        family_records=family_records,
        family_members=family_members,
        upcoming_appointments=upcoming_appointments,
        today_appointments=today_appointments,
        current_medications=current_medications,
        # Statistics
        total_records=total_records,
        total_members=total_members,
        upcoming_count=upcoming_count,
        medications_count=medications_count,
        rag_status=rag_status,
    )

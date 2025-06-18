"""
Main blueprint for the application home page and dashboard.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from ..models import db
from ..models.core.appointment import Appointment
from ..models.core.current_medication import CurrentMedication
from ..models.core.family_member import FamilyMember
from ..models.core.health_record import HealthRecord
from ..utils.health_status import HealthStatusAnalyzer

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Application home page and dashboard for authenticated users"""
    if not current_user.is_authenticated:
        # Show landing page for unauthenticated users
        return render_template("index.html")

    # Get selected family member from query params
    member_id = request.args.get("member_id", "self")

    # Load family members for dropdown selector
    family_members = current_user.family_members

    # Set selected member
    selected_member = None

    if member_id != "self" and member_id.isdigit():
        # Find the selected family member
        selected_member = FamilyMember.query.filter_by(id=int(member_id)).first_or_404()

        # Make sure the family member belongs to the current user
        if selected_member not in current_user.family_members:
            abort(403)  # Forbidden

    # Get dashboard statistics
    stats = _get_dashboard_stats(selected_member)

    # Get health status
    health_status = None
    health_analyzer = HealthStatusAnalyzer(
        user_id=current_user.id if member_id == "self" else None,
        family_member_id=selected_member.id if selected_member else None,
    )
    health_status = health_analyzer.generate_status_report()

    # Get medications for selected person
    medications = []
    if selected_member:
        medications = CurrentMedication.query.filter_by(
            family_member_id=selected_member.id
        ).all()
    # TODO: Add user's medications if needed in the future

    # Get upcoming appointments for selected person or all if self
    upcoming_appointments = []
    if selected_member:
        upcoming_appointments = (
            Appointment.query.filter_by(
                family_member_id=selected_member.id, status="scheduled"
            )
            .filter(Appointment.appointment_date >= datetime.utcnow())
            .order_by(Appointment.appointment_date)
            .limit(5)
            .all()
        )
    else:
        # Get upcoming appointments for all family members and self
        upcoming_appointments = (
            Appointment.query.filter_by(user_id=current_user.id, status="scheduled")
            .filter(Appointment.appointment_date >= datetime.utcnow())
            .order_by(Appointment.appointment_date)
            .limit(5)
            .all()
        )

    # Get recent medical records for selected person or all if self
    recent_records = []
    if selected_member:
        recent_records = (
            HealthRecord.query.filter_by(family_member_id=selected_member.id)
            .order_by(HealthRecord.date.desc())
            .limit(5)
            .all()
        )
    else:
        recent_records = (
            HealthRecord.query.filter_by(user_id=current_user.id)
            .order_by(HealthRecord.date.desc())
            .limit(5)
            .all()
        )

    next_appointment = upcoming_appointments[0] if upcoming_appointments else None

    return render_template(
        "index.html",
        family_members=family_members,
        selected_member=selected_member,
        stats=stats,
        health_status=health_status,
        medications=medications,
        upcoming_appointments=upcoming_appointments,
        recent_records=recent_records,
        next_appointment=next_appointment,
    )


def _get_dashboard_stats(selected_member: Optional[FamilyMember] = None) -> Dict:
    """
    Generate statistics for the dashboard

    Args:
        selected_member: The selected family member or None for self

    Returns:
        Dictionary of statistics
    """
    # Count family members
    total_members = len(current_user.family_members)

    # Count medical records
    if selected_member:
        total_records = HealthRecord.query.filter_by(
            family_member_id=selected_member.id
        ).count()
    else:
        total_records = HealthRecord.query.filter_by(user_id=current_user.id).count()

    # Count upcoming appointments
    if selected_member:
        upcoming_appointments = (
            Appointment.query.filter_by(
                family_member_id=selected_member.id, status="scheduled"
            )
            .filter(Appointment.appointment_date >= datetime.utcnow())
            .count()
        )
    else:
        upcoming_appointments = (
            Appointment.query.filter_by(user_id=current_user.id, status="scheduled")
            .filter(Appointment.appointment_date >= datetime.utcnow())
            .count()
        )

    # Count current medications
    current_medications = 0
    if selected_member:
        current_medications = CurrentMedication.query.filter_by(
            family_member_id=selected_member.id
        ).count()
    # TODO: Add user's own medication count if implemented

    return {
        "total_members": total_members,
        "total_records": total_records,
        "upcoming_appointments": upcoming_appointments,
        "current_medications": current_medications,
    }

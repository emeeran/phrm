"""
Dashboard Routes Module

This module contains route handlers for the dashboard functionality.
"""

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from ...models import HealthRecord
from ...utils.local_rag import get_rag_status
from ...utils.shared import monitor_performance

dashboard_routes = Blueprint("dashboard_routes", __name__)


@dashboard_routes.route("/dashboard")
@login_required
@monitor_performance
def dashboard():
    """Main dashboard showing recent records and stats"""
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

    # Get RAG system status and available references
    rag_status = get_rag_status()

    return render_template(
        "records/dashboard.html",
        title="Dashboard",
        own_records=own_records,
        family_records=family_records,
        family_members=family_members,
        rag_status=rag_status,
    )

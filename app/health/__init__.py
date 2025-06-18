"""
Health blueprint for managing health status and reports.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..models.core.family_member import FamilyMember
from ..utils.health_status import HealthStatusAnalyzer

health_bp = Blueprint("health", __name__, url_prefix="/health")


@health_bp.route("/status")
@login_required
def view_status():
    """View health status report"""
    # Get member_id from query params
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
            flash(
                "You don't have access to this family member's health status.", "danger"
            )
            return redirect(url_for("health.view_status"))

    # Initialize health status analyzer
    analyzer = HealthStatusAnalyzer(
        user_id=current_user.id if member_id == "self" else None,
        family_member_id=selected_member.id if selected_member else None,
    )

    # Generate health status report
    health_status = analyzer.generate_status_report()

    return render_template(
        "health/status.html",
        health_status=health_status,
        family_members=family_members,
        selected_member=selected_member,
    )


@health_bp.route("/generate")
@login_required
def generate_status():
    """Generate a new health status report"""
    # Get member_id from query params
    member_id = request.args.get("member_id", "self")

    # Initialize health status analyzer
    analyzer = None

    if member_id == "self":
        analyzer = HealthStatusAnalyzer(user_id=current_user.id)
    elif member_id.isdigit():
        # Find the selected family member
        selected_member = FamilyMember.query.filter_by(id=int(member_id)).first_or_404()

        # Make sure the family member belongs to the current user
        if selected_member not in current_user.family_members:
            flash(
                "You don't have access to this family member's health status.", "danger"
            )
            return redirect(url_for("main.index"))

        analyzer = HealthStatusAnalyzer(family_member_id=selected_member.id)

    if analyzer:
        # Generate health status report
        analyzer.generate_status_report()
        flash("Health status report generated successfully.", "success")
    else:
        flash("Could not generate health status report.", "danger")

    # Redirect to view status
    return redirect(url_for("health.view_status", member_id=member_id))


@health_bp.route("/vitals")
@login_required
def vitals_history():
    """View vital signs history"""
    # This would show historical vital signs data
    return render_template("health/vitals.html")


@health_bp.route("/report")
@login_required
def health_report():
    """Generate a comprehensive health report"""
    # This would generate a printable/exportable health report
    return render_template("health/report.html")

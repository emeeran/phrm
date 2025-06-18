"""
Family members blueprint for managing family member profiles.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..models import db
from ..models.core.current_medication import CurrentMedication
from ..models.core.family_member import FamilyMember
from ..models.core.health_record import HealthRecord
from ..models.core.medical_condition import MedicalCondition

members_bp = Blueprint("members", __name__, url_prefix="/members")


@members_bp.route("/")
@login_required
def list_members():
    """List all family members"""
    members = current_user.family_members

    # For each member, get summary stats
    member_stats = {}
    for member in members:
        member_stats[member.id] = {
            "records_count": HealthRecord.query.filter_by(
                family_member_id=member.id
            ).count(),
            "conditions_count": MedicalCondition.query.filter_by(
                family_member_id=member.id
            ).count(),
            "medications_count": CurrentMedication.query.filter_by(
                family_member_id=member.id
            ).count(),
        }

    return render_template(
        "members/list.html", members=members, member_stats=member_stats
    )


@members_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_member():
    """Add a new family member"""
    # This will be implemented in a separate file or as part of the forms module
    return render_template("members/add.html")


@members_bp.route("/<int:member_id>")
@login_required
def view_member(member_id):
    """View family member details"""
    member = FamilyMember.query.get_or_404(member_id)

    # Security check - make sure the family member belongs to the current user
    if member not in current_user.family_members:
        flash("You don't have access to this family member's profile.", "danger")
        return redirect(url_for("members.list_members"))

    # Get health records
    records = (
        HealthRecord.query.filter_by(family_member_id=member.id)
        .order_by(HealthRecord.date.desc())
        .all()
    )

    # Get medical conditions
    conditions = MedicalCondition.query.filter_by(family_member_id=member.id).all()

    # Get current medications
    medications = CurrentMedication.query.filter_by(family_member_id=member.id).all()

    return render_template(
        "members/view.html",
        member=member,
        records=records,
        conditions=conditions,
        medications=medications,
    )


@members_bp.route("/<int:member_id>/edit", methods=["GET", "POST"])
@login_required
def edit_member(member_id):
    """Edit an existing family member"""
    # This will be implemented in a separate file or as part of the forms module
    return render_template("members/edit.html")


@members_bp.route("/<int:member_id>/delete", methods=["POST"])
@login_required
def delete_member(member_id):
    """Delete a family member"""
    member = FamilyMember.query.get_or_404(member_id)

    # Security check - make sure the family member belongs to the current user
    if member not in current_user.family_members:
        flash("You don't have access to this family member's profile.", "danger")
        return redirect(url_for("members.list_members"))

    # This would typically involve checking for related records and possibly
    # prompting for confirmation before deletion or handling cascading deletes

    db.session.delete(member)
    db.session.commit()

    flash("Family member deleted successfully.", "success")
    return redirect(url_for("members.list_members"))

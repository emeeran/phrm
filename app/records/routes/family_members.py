"""
Family Member Routes Module

This module contains route handlers for family member management operations.
"""

import os

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from ... import limiter
from ...models import Document, FamilyMember, HealthRecord, db
from ...utils.shared import log_security_event, monitor_performance, sanitize_html
from ..forms import FamilyMemberForm

family_member_routes = Blueprint("family_member_routes", __name__)


@family_member_routes.route("/family")
@login_required
@monitor_performance
def list_family():
    """List all family members"""
    family_members = current_user.family_members
    return render_template(
        "records/family_list.html",
        title="Family Members",
        family_members=family_members,
    )


@family_member_routes.route("/family/add", methods=["GET", "POST"])
@login_required
@limiter.limit("5 per hour")  # Rate limit family member creation
@monitor_performance
def add_family_member():
    """Add a new family member with complete medical history"""
    form = FamilyMemberForm()

    if form.validate_on_submit():
        try:
            # Sanitize all inputs
            first_name = sanitize_html(form.first_name.data.strip())
            last_name = sanitize_html(form.last_name.data.strip())
            relationship = (
                sanitize_html(form.relationship.data.strip())
                if form.relationship.data
                else None
            )
            gender = (
                sanitize_html(form.gender.data.strip()) if form.gender.data else None
            )
            blood_type = (
                sanitize_html(form.blood_type.data.strip())
                if form.blood_type.data
                else None
            )

            # Sanitize medical history fields
            family_medical_history = (
                sanitize_html(form.family_medical_history.data)
                if form.family_medical_history.data
                else None
            )
            surgical_history = (
                sanitize_html(form.surgical_history.data)
                if form.surgical_history.data
                else None
            )
            current_medications = (
                sanitize_html(form.current_medications.data)
                if form.current_medications.data
                else None
            )
            allergies = (
                sanitize_html(form.allergies.data) if form.allergies.data else None
            )
            chronic_conditions = (
                sanitize_html(form.chronic_conditions.data)
                if form.chronic_conditions.data
                else None
            )
            notes = sanitize_html(form.notes.data) if form.notes.data else None

            # Create new family member
            family_member = FamilyMember(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=form.date_of_birth.data,
                relationship=relationship,
                gender=gender,
                blood_type=blood_type,
                height=form.height.data,
                weight=form.weight.data,
                family_medical_history=family_medical_history,
                surgical_history=surgical_history,
                current_medications=current_medications,
                allergies=allergies,
                chronic_conditions=chronic_conditions,
                notes=notes,
                user_id=current_user.id,
            )

            db.session.add(family_member)
            db.session.commit()

            # Log successful family member creation
            log_security_event(
                "family_member_created",
                {
                    "user_id": current_user.id,
                    "family_member_id": family_member.id,
                    "family_member_name": f"{first_name} {last_name}",
                },
            )

            flash(
                f"Family member {first_name} {last_name} added successfully!",
                "success",
            )
            return redirect(url_for("records.list_family"))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating family member: {e}")
            flash(
                "An error occurred while adding the family member. Please try again.",
                "danger",
            )

    return render_template(
        "records/family_form.html", title="Add Family Member", form=form
    )


@family_member_routes.route(
    "/family/<int:family_member_id>/edit", methods=["GET", "POST"]
)
@login_required
@monitor_performance
def edit_family_member(family_member_id):
    """Edit an existing family member"""
    family_member = FamilyMember.query.get_or_404(family_member_id)

    # Check if the family member belongs to the current user
    if family_member not in current_user.family_members:
        log_security_event(
            "unauthorized_family_member_edit_attempt",
            {
                "user_id": current_user.id,
                "family_member_id": family_member_id,
            },
        )
        flash("You do not have permission to edit this family member", "danger")
        return redirect(url_for("records.list_family"))

    form = FamilyMemberForm()

    if form.validate_on_submit():
        try:
            # Update family member information with sanitized data
            family_member.first_name = sanitize_html(form.first_name.data.strip())
            family_member.last_name = sanitize_html(form.last_name.data.strip())
            family_member.date_of_birth = form.date_of_birth.data
            family_member.relationship = (
                sanitize_html(form.relationship.data.strip())
                if form.relationship.data
                else None
            )
            family_member.gender = (
                sanitize_html(form.gender.data.strip()) if form.gender.data else None
            )
            family_member.blood_type = (
                sanitize_html(form.blood_type.data.strip())
                if form.blood_type.data
                else None
            )
            family_member.height = form.height.data
            family_member.weight = form.weight.data
            family_member.family_medical_history = (
                sanitize_html(form.family_medical_history.data)
                if form.family_medical_history.data
                else None
            )
            family_member.surgical_history = (
                sanitize_html(form.surgical_history.data)
                if form.surgical_history.data
                else None
            )
            family_member.current_medications = (
                sanitize_html(form.current_medications.data)
                if form.current_medications.data
                else None
            )
            family_member.allergies = (
                sanitize_html(form.allergies.data) if form.allergies.data else None
            )
            family_member.chronic_conditions = (
                sanitize_html(form.chronic_conditions.data)
                if form.chronic_conditions.data
                else None
            )
            family_member.notes = (
                sanitize_html(form.notes.data) if form.notes.data else None
            )

            db.session.commit()

            # Log successful family member update
            log_security_event(
                "family_member_updated",
                {
                    "user_id": current_user.id,
                    "family_member_id": family_member.id,
                    "family_member_name": f"{family_member.first_name} {family_member.last_name}",
                },
            )

            flash(
                f"Family member {family_member.first_name} {family_member.last_name} updated successfully!",
                "success",
            )
            return redirect(url_for("records.list_family"))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Error updating family member {family_member_id}: {e}"
            )
            flash(
                "An error occurred while updating the family member. Please try again.",
                "danger",
            )

    elif request.method == "GET":
        # Populate form with existing family member data
        _populate_family_member_form(form, family_member)

    return render_template(
        "records/family_form.html",
        title=f"Edit {family_member.first_name} {family_member.last_name}",
        form=form,
        family_member=family_member,
    )


@family_member_routes.route("/family/<int:family_member_id>/delete", methods=["POST"])
@login_required
@limiter.limit("3 per minute")  # Strict rate limit for deletions
@monitor_performance
def delete_family_member(family_member_id):
    """Delete a family member and all associated records"""
    try:
        family_member = FamilyMember.query.get_or_404(family_member_id)

        # Check if the family member belongs to the current user
        if family_member not in current_user.family_members:
            log_security_event(
                "unauthorized_family_member_delete_attempt",
                {
                    "user_id": current_user.id,
                    "family_member_id": family_member_id,
                },
            )
            flash("You do not have permission to delete this family member", "danger")
            return redirect(url_for("records.list_family"))

        # Get family member name for flash message
        member_name = f"{family_member.first_name} {family_member.last_name}"

        # Get associated health records to delete documents
        associated_records = HealthRecord.query.filter_by(
            family_member_id=family_member.id
        ).all()

        # Delete files associated with health records
        deleted_files = []
        for record in associated_records:
            documents = Document.query.filter_by(health_record_id=record.id).all()
            for doc in documents:
                try:
                    if os.path.exists(doc.file_path):
                        os.remove(doc.file_path)
                        deleted_files.append(doc.filename)
                    else:
                        current_app.logger.warning(
                            f"File not found on disk: {doc.file_path}"
                        )
                except (FileNotFoundError, PermissionError) as e:
                    current_app.logger.error(
                        f"Error deleting file {doc.file_path}: {e}"
                    )

        # Delete family member (cascade will delete associated records and documents)
        db.session.delete(family_member)
        db.session.commit()

        # Log successful family member deletion
        log_security_event(
            "family_member_deleted",
            {
                "user_id": current_user.id,
                "family_member_id": family_member_id,
                "family_member_name": member_name,
                "deleted_files": deleted_files,
                "associated_records_count": len(associated_records),
            },
        )

        flash(
            f"Family member {member_name} and all associated records have been deleted successfully",
            "success",
        )
        return redirect(url_for("records.list_family"))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error deleting family member {family_member_id}: {e}"
        )
        flash("An error occurred while deleting the family member", "danger")
        return redirect(url_for("records.list_family"))


@family_member_routes.route("/family/<int:family_member_id>")
@login_required
@monitor_performance
def view_family_member(family_member_id):
    """View a specific family member's details"""
    family_member = FamilyMember.query.get_or_404(family_member_id)

    # Check if the family member belongs to the current user
    if family_member not in current_user.family_members:
        log_security_event(
            "unauthorized_family_member_access_attempt",
            {
                "user_id": current_user.id,
                "family_member_id": family_member_id,
            },
        )
        flash("You do not have permission to view this family member", "danger")
        return redirect(url_for("records.list_family"))

    # Get recent health records for this family member
    recent_records = (
        HealthRecord.query.filter_by(family_member_id=family_member.id)
        .order_by(HealthRecord.date.desc())
        .limit(10)
        .all()
    )

    # Log successful family member access
    log_security_event(
        "family_member_accessed",
        {
            "user_id": current_user.id,
            "family_member_id": family_member_id,
        },
    )

    return render_template(
        "records/family_profile.html",
        title=f"{family_member.first_name} {family_member.last_name}",
        family_member=family_member,
        recent_records=recent_records,
    )


# Helper functions for family member operations


def _populate_family_member_form(form, family_member):
    """Populate form with existing family member data"""
    form.first_name.data = family_member.first_name
    form.last_name.data = family_member.last_name
    form.date_of_birth.data = family_member.date_of_birth
    form.relationship.data = family_member.relationship
    form.gender.data = family_member.gender
    form.blood_type.data = family_member.blood_type
    form.height.data = family_member.height
    form.weight.data = family_member.weight
    form.family_medical_history.data = family_member.family_medical_history
    form.surgical_history.data = family_member.surgical_history
    form.current_medications.data = family_member.current_medications
    form.allergies.data = family_member.allergies
    form.chronic_conditions.data = family_member.chronic_conditions
    form.notes.data = family_member.notes

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
from ...models import CurrentMedication, Document, FamilyMember, HealthRecord, db
from ...utils.shared import log_security_event, monitor_performance, sanitize_html
from ..forms import FamilyMemberForm

# Constants for medical context validation
MIN_MEANINGFUL_CONTEXT_LENGTH = 100

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

            # Sanitize contact and healthcare info
            emergency_contact_name = (
                sanitize_html(form.emergency_contact_name.data.strip())
                if form.emergency_contact_name.data
                else None
            )
            emergency_contact_phone = (
                sanitize_html(form.emergency_contact_phone.data.strip())
                if form.emergency_contact_phone.data
                else None
            )
            primary_doctor = (
                sanitize_html(form.primary_doctor.data.strip())
                if form.primary_doctor.data
                else None
            )
            insurance_provider = (
                sanitize_html(form.insurance_provider.data.strip())
                if form.insurance_provider.data
                else None
            )

            # Create new family member with all fields
            family_member = FamilyMember(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=form.date_of_birth.data,
                relationship=relationship,
                gender=gender,
                blood_type=blood_type,
                family_medical_history=family_medical_history,
                surgical_history=surgical_history,
                current_medications=current_medications,
                allergies=allergies,
                chronic_conditions=chronic_conditions,
                emergency_contact_name=emergency_contact_name,
                emergency_contact_phone=emergency_contact_phone,
                primary_doctor=primary_doctor,
                insurance_provider=insurance_provider,
                notes=notes,
            )

            # Add family member to current user's family
            current_user.family_members.append(family_member)
            db.session.add(family_member)
            db.session.commit()

            # Handle current medication entries
            for entry_form in form.current_medication_entries.data:
                if entry_form and entry_form.get(
                    "medicine"
                ):  # Only create if medicine is specified
                    current_medication = CurrentMedication(
                        family_member_id=family_member.id,
                        medicine=sanitize_html(entry_form["medicine"]),
                        strength=(
                            sanitize_html(entry_form.get("strength", ""))
                            if entry_form.get("strength")
                            else None
                        ),
                        morning=(
                            sanitize_html(entry_form.get("morning", ""))
                            if entry_form.get("morning")
                            else None
                        ),
                        noon=(
                            sanitize_html(entry_form.get("noon", ""))
                            if entry_form.get("noon")
                            else None
                        ),
                        evening=(
                            sanitize_html(entry_form.get("evening", ""))
                            if entry_form.get("evening")
                            else None
                        ),
                        bedtime=(
                            sanitize_html(entry_form.get("bedtime", ""))
                            if entry_form.get("bedtime")
                            else None
                        ),
                        duration=(
                            sanitize_html(entry_form.get("duration", ""))
                            if entry_form.get("duration")
                            else None
                        ),
                    )
                    db.session.add(current_medication)

            # Commit all changes
            db.session.commit()

            # Update AI context with new family member's medical history
            try:
                _update_ai_context_for_new_family_member(family_member)
            except Exception as ai_error:
                current_app.logger.warning(f"Failed to update AI context: {ai_error}")
                # Don't fail the family member creation if AI update fails

            # Log successful family member creation
            log_security_event(
                "family_member_created",
                {
                    "user_id": current_user.id,
                    "family_member_id": family_member.id,
                    "family_member_name": f"{first_name} {last_name}",
                    "has_medical_history": bool(
                        family_medical_history
                        or chronic_conditions
                        or allergies
                        or current_medications
                    ),
                },
            )

            flash(
                f"Family member {first_name} {last_name} added successfully! Their medical history is now available to the AI.",
                "success",
            )
            return redirect(url_for("records.family_member_routes.list_family"))

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
        return redirect(url_for("records.family_member_routes.list_family"))

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
            family_member.emergency_contact_name = (
                sanitize_html(form.emergency_contact_name.data.strip())
                if form.emergency_contact_name.data
                else None
            )
            family_member.emergency_contact_phone = (
                sanitize_html(form.emergency_contact_phone.data.strip())
                if form.emergency_contact_phone.data
                else None
            )
            family_member.primary_doctor = (
                sanitize_html(form.primary_doctor.data.strip())
                if form.primary_doctor.data
                else None
            )
            family_member.insurance_provider = (
                sanitize_html(form.insurance_provider.data.strip())
                if form.insurance_provider.data
                else None
            )
            family_member.notes = (
                sanitize_html(form.notes.data) if form.notes.data else None
            )

            # Handle current medication entries - remove existing ones and add new ones
            # Delete existing current medication entries
            CurrentMedication.query.filter_by(
                family_member_id=family_member.id
            ).delete()

            # Add new current medication entries
            for entry_form in form.current_medication_entries.data:
                if entry_form and entry_form.get(
                    "medicine"
                ):  # Only create if medicine is specified
                    current_medication = CurrentMedication(
                        family_member_id=family_member.id,
                        medicine=sanitize_html(entry_form["medicine"]),
                        strength=(
                            sanitize_html(entry_form.get("strength", ""))
                            if entry_form.get("strength")
                            else None
                        ),
                        morning=(
                            sanitize_html(entry_form.get("morning", ""))
                            if entry_form.get("morning")
                            else None
                        ),
                        noon=(
                            sanitize_html(entry_form.get("noon", ""))
                            if entry_form.get("noon")
                            else None
                        ),
                        evening=(
                            sanitize_html(entry_form.get("evening", ""))
                            if entry_form.get("evening")
                            else None
                        ),
                        bedtime=(
                            sanitize_html(entry_form.get("bedtime", ""))
                            if entry_form.get("bedtime")
                            else None
                        ),
                        duration=(
                            sanitize_html(entry_form.get("duration", ""))
                            if entry_form.get("duration")
                            else None
                        ),
                    )
                    db.session.add(current_medication)

            db.session.commit()

            # Update AI context with updated medical history
            try:
                _update_ai_context_for_new_family_member(family_member)
            except Exception as ai_error:
                current_app.logger.warning(f"Failed to update AI context: {ai_error}")

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
            return redirect(url_for("records.family_member_routes.list_family"))

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
            return redirect(url_for("records.family_member_routes.list_family"))

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

            # Clean up any AI summaries for this health record
            try:
                from ...models.core.health_record import AISummary
                AISummary.query.filter_by(health_record_id=record.id).delete()
            except ImportError:
                current_app.logger.warning("Could not import AISummary model")
            except Exception as e:
                current_app.logger.error(f"Error cleaning up AI summaries: {e}")

        # Clean up any AI audit logs referencing this family member
        try:
            from ...models.ai_audit.audit_log import AIAuditLog
            AIAuditLog.query.filter_by(family_member_id=family_member.id).update(
                {"family_member_id": None}
            )
        except ImportError:
            current_app.logger.warning("Could not import AIAuditLog model")
        except Exception as e:
            current_app.logger.error(f"Error cleaning up AI audit logs: {e}")

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
        return redirect(url_for("records.family_member_routes.list_family"))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error deleting family member {family_member_id}: {e}"
        )
        flash("An error occurred while deleting the family member", "danger")
        return redirect(url_for("records.family_member_routes.list_family"))


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
        return redirect(url_for("records.family_member_routes.list_family"))

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


def _update_ai_context_for_new_family_member(family_member):
    """Update AI context with new family member's complete medical history"""
    try:
        # Import AI services here to avoid circular imports
        from ...ai.summarization import update_family_context

        # Get complete medical context for this family member
        medical_context = family_member.get_complete_medical_context()

        # Update AI context if we have medical information
        if (
            medical_context
            and len(medical_context.strip()) > MIN_MEANINGFUL_CONTEXT_LENGTH
        ):  # Basic check for meaningful content
            update_family_context(current_user.id, family_member.id, medical_context)
            current_app.logger.info(
                f"Updated AI context for family member {family_member.id}"
            )
        else:
            current_app.logger.info(
                f"No significant medical history to add to AI context for family member {family_member.id}"
            )

    except ImportError:
        current_app.logger.warning(
            "AI summarization module not available - skipping context update"
        )
    except Exception as e:
        current_app.logger.error(
            f"Failed to update AI context for family member {family_member.id}: {e}"
        )
        raise


def _populate_family_member_form(form, family_member):
    """Populate form with existing family member data"""
    form.first_name.data = family_member.first_name
    form.last_name.data = family_member.last_name
    form.date_of_birth.data = family_member.date_of_birth
    form.relationship.data = family_member.relationship
    form.gender.data = family_member.gender
    form.blood_type.data = family_member.blood_type
    form.family_medical_history.data = family_member.family_medical_history
    form.surgical_history.data = family_member.surgical_history
    form.current_medications.data = family_member.current_medications
    form.allergies.data = family_member.allergies
    form.chronic_conditions.data = family_member.chronic_conditions
    form.emergency_contact_name.data = family_member.emergency_contact_name
    form.emergency_contact_phone.data = family_member.emergency_contact_phone
    form.primary_doctor.data = family_member.primary_doctor
    form.insurance_provider.data = family_member.insurance_provider
    form.notes.data = family_member.notes

    # Populate current medication entries
    current_medication_entries = family_member.current_medication_entries
    form.current_medication_entries.entries.clear()

    for entry in current_medication_entries:
        entry_form = form.current_medication_entries.append_entry()
        entry_form.medicine.data = entry.medicine
        entry_form.strength.data = entry.strength
        entry_form.morning.data = entry.morning
        entry_form.noon.data = entry.noon
        entry_form.evening.data = entry.evening
        entry_form.bedtime.data = entry.bedtime
        entry_form.duration.data = entry.duration

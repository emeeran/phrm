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
    """List all family members with optional pagination, sorting, and filtering
    
    Query parameters:
    - page: Current page number (default: 1)
    - per_page: Items per page (default: 10)
    - sort: Sort field (name, relationship, records) (default: name)
    - order: Sort order (asc, desc) (default: asc)
    - search: Search term for filtering
    """
    # Get query parameters for pagination and sorting
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    sort = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')
    search = request.args.get('search', '')
    
    # Get family members directly from the current user relationship
    # This is the safest approach that avoids relationship issues
    family_members_query = current_user.family_members
    
    if isinstance(family_members_query, list):
        # If it's already a list (eager loaded), create a query
        member_ids = [m.id for m in family_members_query]
        query = FamilyMember.query.filter(FamilyMember.id.in_(member_ids))
    else:
        # It's already a query
        query = family_members_query
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (FamilyMember.first_name.ilike(search_term)) | 
            (FamilyMember.last_name.ilike(search_term)) |
            (FamilyMember.relationship.ilike(search_term))
        )
        
    # Apply sorting
    if sort == 'name':
        if order == 'desc':
            query = query.order_by(FamilyMember.first_name.desc(), FamilyMember.last_name.desc())
        else:
            query = query.order_by(FamilyMember.first_name.asc(), FamilyMember.last_name.asc())
    elif sort == 'relationship':
        if order == 'desc':
            query = query.order_by(FamilyMember.relationship.desc())
        else:
            query = query.order_by(FamilyMember.relationship.asc())
    
    # We can't directly sort by record count in SQL, so sorting by records is handled in JavaScript
    
    # Get paginated results if API mode, otherwise get all for client-side pagination
    if request.args.get('format') == 'json':
        paginated_members = query.paginate(page=page, per_page=per_page, error_out=False)
        family_members = paginated_members.items
        
        # Prepare response data
        response_data = {
            'items': [],
            'pagination': {
                'page': paginated_members.page,
                'per_page': paginated_members.per_page,
                'total': paginated_members.total,
                'pages': paginated_members.pages,
                'has_next': paginated_members.has_next,
                'has_prev': paginated_members.has_prev,
                'next_num': paginated_members.next_num,
                'prev_num': paginated_members.prev_num
            }
        }
        
        # Add family member data
        for member in family_members:
            response_data['items'].append({
                'id': member.id,
                'first_name': member.first_name,
                'last_name': member.last_name,
                'relationship': member.relationship,
                'date_of_birth': member.date_of_birth.strftime('%Y-%m-%d') if member.date_of_birth else None,
                'record_count': member.records.count()
            })
            
        return response_data
    else:
        # For HTML view, get all members for client-side pagination
        family_members = query.all()
        
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
            # Get sanitized form data
            data = _sanitize_form_data(form)
            
            # Create new family member with sanitized data
            family_member = FamilyMember(**data)
            
            # Add family member to current user's family
            current_user.family_members.append(family_member)
            db.session.add(family_member)
            
            # Flush the session to get the family_member ID without committing
            db.session.flush()
            
            # Process medication entries with the new family_member.id
            medications = _process_medication_entries(form.current_medication_entries.data, family_member.id)
            for medication in medications:
                db.session.add(medication)
                
            # Commit all changes in a single transaction
            db.session.commit()
            
            # Update AI context without failing if there's an error - using the new helper function
            _handle_ai_context_update(family_member)
            
            # Log successful family member creation
            has_medical_history = bool(
                data["family_medical_history"] or 
                data["chronic_conditions"] or 
                data["allergies"] or 
                data["current_medications"]
            )
            
            log_security_event(
                "family_member_created",
                {
                    "user_id": current_user.id,
                    "family_member_id": family_member.id,
                    "family_member_name": f"{data['first_name']} {data['last_name']}",
                    "has_medical_history": has_medical_history,
                },
            )

            flash(
                f"Family member {data['first_name']} {data['last_name']} added successfully! Their medical history is now available to the AI.",
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
            # Get sanitized form data
            data = _sanitize_form_data(form)
            
            # Update family member attributes with sanitized data
            for key, value in data.items():
                setattr(family_member, key, value)

            # Handle current medication entries efficiently
            # First delete existing entries
            CurrentMedication.query.filter_by(
                family_member_id=family_member.id
            ).delete()

            # Then add new processed entries
            medications = _process_medication_entries(form.current_medication_entries.data, family_member.id)
            for medication in medications:
                db.session.add(medication)

            # Commit all changes
            db.session.commit()

            # Update AI context without failing if there's an error
            _handle_ai_context_update(family_member)

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

        # Clean up all AI data efficiently
        _clean_ai_data_for_family_member_deletion(family_member.id, associated_records)

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

    # Get recent health records for this family member - use efficient query
    recent_records = (
        HealthRecord.query
        .filter_by(family_member_id=family_member.id)
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
    
    # Check if JSON format is requested (for quick view)
    if request.args.get('format') == 'json':
        # Prepare a simplified version of data for quick view
        recent_records_data = []
        for record in recent_records:
            recent_records_data.append({
                'id': record.id,
                'date': record.date.strftime('%Y-%m-%d') if record.date else None,
                'chief_complaint': record.chief_complaint[:50] if record.chief_complaint else 'Medical Record',
                'doctor': record.doctor
            })
        
        # Check if family member has medication entries
        has_medications = len(family_member.current_medication_entries) > 0 or bool(family_member.current_medications)
        
        # Prepare the response data
        response_data = {
            'family_member': {
                'id': family_member.id,
                'first_name': family_member.first_name,
                'last_name': family_member.last_name,
                'relationship': family_member.relationship,
                'date_of_birth': family_member.date_of_birth.strftime('%Y-%m-%d') if family_member.date_of_birth else None,
                'gender': family_member.gender,
                'blood_type': family_member.blood_type,
                'allergies': family_member.allergies,
                'chronic_conditions': family_member.chronic_conditions,
                'has_medications': has_medications,
                'primary_doctor': family_member.primary_doctor,
                'insurance_provider': family_member.insurance_provider,
            },
            'recent_records': recent_records_data
        }
        
        return response_data
    
    # Regular HTML response
    return render_template(
        "records/family_profile.html",
        title=f"{family_member.first_name} {family_member.last_name}",
        family_member=family_member,
        recent_records=recent_records,
    )


# Helper functions for family member operations


def _sanitize_form_input(value, strip=True, allow_none=True):
    """Centralized sanitization for form inputs

    Args:
        value: The value to sanitize
        strip: Whether to strip whitespace (for string inputs)
        allow_none: If True, returns None for falsy values, otherwise empty string

    Returns:
        Sanitized value (or None if input is falsy and allow_none is True)
    """
    if not value and allow_none:
        return None
    if not value and not allow_none:
        return ""

    result = sanitize_html(value.strip() if strip and hasattr(value, "strip") else value)
    return result


def _sanitize_form_data(form):
    """Extract and sanitize all common form fields

    Args:
        form: The submitted form with family member data

    Returns:
        Dict containing sanitized form data
    """
    return {
        "first_name": _sanitize_form_input(form.first_name.data, strip=True),
        "last_name": _sanitize_form_input(form.last_name.data, strip=True),
        "relationship": _sanitize_form_input(form.relationship.data, strip=True),
        "gender": _sanitize_form_input(form.gender.data, strip=True),
        "blood_type": _sanitize_form_input(form.blood_type.data, strip=True),
        "family_medical_history": _sanitize_form_input(form.family_medical_history.data, strip=False),
        "surgical_history": _sanitize_form_input(form.surgical_history.data, strip=False),
        "current_medications": _sanitize_form_input(form.current_medications.data, strip=False),
        "allergies": _sanitize_form_input(form.allergies.data, strip=False),
        "chronic_conditions": _sanitize_form_input(form.chronic_conditions.data, strip=False),
        "emergency_contact_name": _sanitize_form_input(form.emergency_contact_name.data, strip=True),
        "emergency_contact_phone": _sanitize_form_input(form.emergency_contact_phone.data, strip=True),
        "primary_doctor": _sanitize_form_input(form.primary_doctor.data, strip=True),
        "insurance_provider": _sanitize_form_input(form.insurance_provider.data, strip=True),
        "notes": _sanitize_form_input(form.notes.data, strip=False),
        "date_of_birth": form.date_of_birth.data  # No sanitization needed for date objects
    }


def _process_medication_entries(entries, family_member_id):
    """Process and sanitize medication entries

    Args:
        entries: Medication form entries
        family_member_id: ID of the family member these medications belong to

    Returns:
        List of CurrentMedication objects ready to be added to the database
    """
    result = []

    for entry in entries:
        if entry and entry.get("medicine"):
            medication = CurrentMedication(
                family_member_id=family_member_id,
                medicine=_sanitize_form_input(entry["medicine"]),
                strength=_sanitize_form_input(entry.get("strength")),
                morning=_sanitize_form_input(entry.get("morning")),
                noon=_sanitize_form_input(entry.get("noon")),
                evening=_sanitize_form_input(entry.get("evening")),
                bedtime=_sanitize_form_input(entry.get("bedtime")),
                duration=_sanitize_form_input(entry.get("duration"))
            )
            result.append(medication)

    return result


def _handle_ai_context_update(family_member):
    """Update AI context safely for a family member

    Args:
        family_member: The FamilyMember object to update AI context for
    """
    try:
        # Import AI services here to avoid circular imports
        from ...ai.summarization import update_family_context

        # Get complete medical context for this family member
        medical_context = family_member.get_complete_medical_context()

        # Update AI context if we have medical information
        if medical_context and len(medical_context.strip()) > MIN_MEANINGFUL_CONTEXT_LENGTH:
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
        # Return exception but don't raise - we don't want to fail the transaction
        return e

    return None


def _populate_family_member_form(form, family_member):
    """Populate form with existing family member data"""
    # Basic fields
    form.first_name.data = family_member.first_name
    form.last_name.data = family_member.last_name
    form.date_of_birth.data = family_member.date_of_birth
    form.relationship.data = family_member.relationship
    form.gender.data = family_member.gender
    form.blood_type.data = family_member.blood_type

    # Medical history fields
    form.family_medical_history.data = family_member.family_medical_history
    form.surgical_history.data = family_member.surgical_history
    form.current_medications.data = family_member.current_medications
    form.allergies.data = family_member.allergies
    form.chronic_conditions.data = family_member.chronic_conditions

    # Contact information
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


def _clean_ai_data_for_family_member_deletion(family_member_id, associated_records):
    """Clean up all AI-related data for a family member being deleted

    Args:
        family_member_id: ID of the family member being deleted
        associated_records: List of associated health records

    Returns:
        True if successful, False if errors occurred
    """
    success = True

    # First clean up any health record AI summaries
    for record in associated_records:
        try:
            from ...models.core.health_record import AISummary
            AISummary.query.filter_by(health_record_id=record.id).delete()
        except ImportError:
            current_app.logger.warning("Could not import AISummary model")
            success = False
        except Exception as e:
            current_app.logger.error(f"Error cleaning up AI summaries: {e}")
            success = False

    # Then clean up any AI audit logs referencing this family member
    try:
        from ...models.ai_audit.audit_log import AIAuditLog
        AIAuditLog.query.filter_by(family_member_id=family_member_id).update(
            {"family_member_id": None}
        )
    except ImportError:
        current_app.logger.warning("Could not import AIAuditLog model")
        success = False
    except Exception as e:
        current_app.logger.error(f"Error cleaning up AI audit logs: {e}")
        success = False

    return success

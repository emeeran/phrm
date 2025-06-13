"""
Health Records Routes Module

This module contains route handlers for health record CRUD operations.
"""

import os
from datetime import datetime, timezone

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
from ...utils.performance_monitor import monitor_performance
from ...utils.security_utils import log_security_event, sanitize_html
from ..file_utils import save_document
from ..forms import RecordForm

# Constants
MAX_SEARCH_LENGTH = 100

health_records_routes = Blueprint("health_records_routes", __name__)


@health_records_routes.route("/list")
@login_required
@monitor_performance
def list_records():
    """List all health records"""
    try:
        # Parse request parameters
        params = _parse_list_parameters()

        # Validate search input
        validation_result = _validate_search_parameters(params)
        if validation_result:
            return validation_result

        # Build and execute query
        query = _build_records_query(params)
        if query is None:  # Error in family member filter
            return redirect(url_for("records.health_records_routes.list_records"))

        records = query.order_by(HealthRecord.date.desc()).paginate(
            page=params["page"], per_page=10
        )

        return render_template(
            "records/list.html",
            title="Health Records",
            records=records,
            record_type=params["record_type"],
            family_member_id=params["family_member_id"],
            search_name=params["search_name"],
        )

    except Exception as e:
        current_app.logger.error(f"Error in list_records: {e}")
        flash("An error occurred while loading records", "danger")
        return redirect(url_for("records.dashboard_routes.dashboard"))


@health_records_routes.route("/create", methods=["GET", "POST"])
@login_required
@limiter.limit("10 per minute")  # Rate limit record creation
@monitor_performance
def create_record():
    """Create a new health record"""
    form = RecordForm()

    # Populate family member choices
    family_members = [(0, "Myself")] + [
        (m.id, f"{m.first_name} {m.last_name}") for m in current_user.family_members
    ]
    form.family_member.choices = family_members

    if form.validate_on_submit():
        try:
            # Sanitize all text inputs
            chief_complaint = (
                sanitize_html(form.chief_complaint.data)
                if form.chief_complaint.data
                else None
            )
            doctor = sanitize_html(form.doctor.data) if form.doctor.data else None
            investigations = (
                sanitize_html(form.investigations.data)
                if form.investigations.data
                else None
            )
            diagnosis = (
                sanitize_html(form.diagnosis.data) if form.diagnosis.data else None
            )
            prescription = (
                sanitize_html(form.prescription.data)
                if form.prescription.data
                else None
            )
            notes = sanitize_html(form.notes.data) if form.notes.data else None
            review_followup = (
                sanitize_html(form.review_followup.data)
                if form.review_followup.data
                else None
            )

            # Create new health record
            record = HealthRecord(
                date=form.date.data,
                chief_complaint=chief_complaint,
                doctor=doctor,
                investigations=investigations,
                diagnosis=diagnosis,
                prescription=prescription,
                notes=notes,
                review_followup=review_followup,
            )

            # Assign to user or family member
            if form.family_member.data == 0:
                record.user_id = current_user.id
            else:
                # Verify family member belongs to current user
                family_member = FamilyMember.query.get(form.family_member.data)
                if family_member and family_member in current_user.family_members:
                    record.family_member_id = family_member.id
                else:
                    log_security_event(
                        "invalid_family_member_assignment",
                        {
                            "user_id": current_user.id,
                            "attempted_family_member_id": form.family_member.data,
                        },
                    )
                    flash("Invalid family member selection", "danger")
                    return redirect(
                        url_for("records.health_records_routes.create_record")
                    )

            # Save record to get an ID
            db.session.add(record)
            db.session.commit()

            # Handle multiple document uploads if provided
            if form.documents.data:
                files = request.files.getlist("documents")
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
                            flash(
                                f"Error uploading file {file.filename}: {e!s}",
                                "warning",
                            )

                if upload_count > 0:
                    db.session.commit()
                    current_app.logger.info(
                        f"Successfully uploaded {upload_count} files for record {record.id}"
                    )

            # Log successful record creation
            log_security_event(
                "health_record_created",
                {
                    "user_id": current_user.id,
                    "record_id": record.id,
                    "family_member_id": record.family_member_id,
                },
            )

            flash("Health record created successfully!", "success")
            return redirect(url_for("records.view_record", record_id=record.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating health record: {e}")
            flash(
                "An error occurred while creating the health record. Please try again.",
                "danger",
            )

    return render_template("records/create.html", title="Create Record", form=form)


@health_records_routes.route("/<int:record_id>")
@login_required
@monitor_performance
def view_record(record_id):
    """View a specific health record"""
    try:
        record = HealthRecord.query.get_or_404(record_id)

        # Check if user has permission to view this record
        has_permission = False
        if record.user_id == current_user.id:
            # This is the user's own record
            has_permission = True
        elif (
            record.family_member_id
            and record.family_member in current_user.family_members
        ):
            # This is a record for a family member of the user
            has_permission = True

        if not has_permission:
            log_security_event(
                "unauthorized_record_access_attempt",
                {
                    "user_id": current_user.id,
                    "record_id": record_id,
                    "record_owner_id": record.user_id,
                    "record_family_member_id": record.family_member_id,
                },
            )
            flash("You do not have permission to view this record", "danger")
            return redirect(url_for("records.dashboard_routes.dashboard"))

        # Log successful record access
        log_security_event(
            "health_record_accessed",
            {"user_id": current_user.id, "record_id": record_id},
        )

        return render_template("records/view.html", title=record.title, record=record)

    except Exception as e:
        current_app.logger.error(f"Error viewing record {record_id}: {e}")
        flash("An error occurred while loading the record", "danger")
        return redirect(url_for("records.dashboard_routes.dashboard"))


@health_records_routes.route("/<int:record_id>/edit", methods=["GET", "POST"])
@login_required
@limiter.limit("5 per minute")  # Rate limit record editing
@monitor_performance
def edit_record(record_id):
    """Edit an existing health record"""
    try:
        record = HealthRecord.query.get_or_404(record_id)

        # Check permissions
        if not _check_edit_permission(record):
            return _handle_unauthorized_edit(record_id, record)

        form = RecordForm()

        # Populate family member choices
        family_members = [(0, "Myself")] + [
            (m.id, f"{m.first_name} {m.last_name}") for m in current_user.family_members
        ]
        form.family_member.choices = family_members

        if form.validate_on_submit():
            try:
                # Update record fields
                _update_record_fields(record, form)

                # Update family member assignment
                if not _update_family_member_assignment(record, form, record_id):
                    return redirect(url_for("records.edit_record", record_id=record.id))

                # Handle document uploads
                _handle_document_uploads(form, record)

                db.session.commit()

                # Log successful record update
                log_security_event(
                    "health_record_updated",
                    {
                        "user_id": current_user.id,
                        "record_id": record_id,
                        "family_member_id": record.family_member_id,
                    },
                )

                flash("Health record updated successfully!", "success")
                return redirect(url_for("records.view_record", record_id=record.id))

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(
                    f"Error updating health record {record_id}: {e}"
                )
                flash(
                    "An error occurred while updating the health record. Please try again.",
                    "danger",
                )

        elif request.method == "GET":
            _populate_form_with_record_data(form, record)

        return render_template(
            "records/edit.html", title="Edit Record", form=form, record=record
        )

    except Exception as e:
        current_app.logger.error(f"Error in edit_record for record {record_id}: {e}")
        flash("An error occurred while loading the record for editing", "danger")
        return redirect(url_for("records.dashboard_routes.dashboard"))


@health_records_routes.route("/<int:record_id>/delete", methods=["POST"])
@login_required
@limiter.limit("3 per minute")  # Strict rate limit for deletions
@monitor_performance
def delete_record(record_id):
    """Delete a health record"""
    try:
        record = HealthRecord.query.get_or_404(record_id)

        # Check if user has permission to delete this record
        has_permission = False
        if record.user_id == current_user.id:
            # This is the user's own record
            has_permission = True
        elif (
            record.family_member_id
            and record.family_member in current_user.family_members
        ):
            # This is a record for a family member of the user
            has_permission = True

        if not has_permission:
            log_security_event(
                "unauthorized_record_delete_attempt",
                {
                    "user_id": current_user.id,
                    "record_id": record_id,
                    "record_owner_id": record.user_id,
                    "record_family_member_id": record.family_member_id,
                },
            )
            flash("You do not have permission to delete this record", "danger")
            return redirect(url_for("records.dashboard_routes.dashboard"))

        # Get associated documents to delete files
        documents = Document.query.filter_by(health_record_id=record.id).all()

        # Delete files from disk
        deleted_files = []
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
                current_app.logger.error(f"Error deleting file {doc.file_path}: {e}")

        # Delete record (cascade will delete associated documents)
        db.session.delete(record)
        db.session.commit()

        # Log successful deletion
        log_security_event(
            "health_record_deleted",
            {
                "user_id": current_user.id,
                "record_id": record_id,
                "deleted_files": deleted_files,
                "family_member_id": record.family_member_id,
            },
        )

        flash("Health record deleted successfully", "success")
        return redirect(url_for("records.health_records_routes.list_records"))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting record {record_id}: {e}")
        flash("An error occurred while deleting the record", "danger")
        return redirect(url_for("records.dashboard_routes.dashboard"))


# Helper functions for health record operations


def _check_edit_permission(record):
    """Check if current user has permission to edit the record"""
    if record.user_id == current_user.id:
        return True
    if record.family_member_id and record.family_member in current_user.family_members:
        return True
    return False


def _handle_unauthorized_edit(record_id, record):
    """Handle unauthorized edit attempt"""
    log_security_event(
        "unauthorized_record_edit_attempt",
        {
            "user_id": current_user.id,
            "record_id": record_id,
            "record_owner_id": record.user_id,
            "record_family_member_id": record.family_member_id,
        },
    )
    flash("You do not have permission to edit this record", "danger")
    return redirect(url_for("records.dashboard_routes.dashboard"))


def _update_record_fields(record, form):
    """Update record fields from form data"""
    record.date = form.date.data
    record.chief_complaint = (
        sanitize_html(form.chief_complaint.data) if form.chief_complaint.data else None
    )
    record.doctor = sanitize_html(form.doctor.data) if form.doctor.data else None
    record.investigations = (
        sanitize_html(form.investigations.data) if form.investigations.data else None
    )
    record.diagnosis = (
        sanitize_html(form.diagnosis.data) if form.diagnosis.data else None
    )
    record.prescription = (
        sanitize_html(form.prescription.data) if form.prescription.data else None
    )
    record.notes = sanitize_html(form.notes.data) if form.notes.data else None
    record.review_followup = (
        sanitize_html(form.review_followup.data) if form.review_followup.data else None
    )
    record.updated_at = datetime.now(timezone.utc)


def _update_family_member_assignment(record, form, record_id):
    """Update family member assignment for record"""
    if form.family_member.data == 0:
        record.user_id = current_user.id
        record.family_member_id = None
        return True

    # Verify family member belongs to current user
    family_member = FamilyMember.query.get(form.family_member.data)
    if family_member and family_member in current_user.family_members:
        record.family_member_id = family_member.id
        record.user_id = None
        return True

    log_security_event(
        "invalid_family_member_assignment",
        {
            "user_id": current_user.id,
            "attempted_family_member_id": form.family_member.data,
            "record_id": record_id,
        },
    )
    flash("Invalid family member selection", "danger")
    return False


def _handle_document_uploads(form, record):
    """Handle document uploads for record"""
    if not form.documents.data:
        return

    files = request.files.getlist("documents")
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
                current_app.logger.error(f"Error uploading file {file.filename}: {e}")
                flash(
                    f"Error uploading file {file.filename}: {e!s}",
                    "warning",
                )


def _populate_form_with_record_data(form, record):
    """Populate form with existing record data"""
    form.date.data = record.date
    form.chief_complaint.data = record.chief_complaint
    form.doctor.data = record.doctor
    form.investigations.data = record.investigations
    form.diagnosis.data = record.diagnosis
    form.prescription.data = record.prescription
    form.notes.data = record.notes
    form.review_followup.data = record.review_followup

    # Set appropriate family member
    if record.user_id:
        form.family_member.data = 0
    else:
        form.family_member.data = record.family_member_id


def _parse_list_parameters():
    """Parse request parameters for list view"""
    page = request.args.get("page", 1, type=int)
    record_type = request.args.get("record_type", "all")
    family_member_id = request.args.get("family_member_id", type=int)
    search_name = request.args.get("search_name", "").strip()

    return {
        "page": page,
        "record_type": record_type,
        "family_member_id": family_member_id,
        "search_name": search_name,
    }


def _validate_search_parameters(params):
    """Validate search parameters for security"""
    if params["search_name"] and len(params["search_name"]) > MAX_SEARCH_LENGTH:
        flash("Search term too long", "danger")
        return redirect(url_for("records.health_records_routes.list_records"))

    if params["search_name"]:
        from ...utils.shared import detect_suspicious_patterns

        if detect_suspicious_patterns(params["search_name"]):
            log_security_event(
                "suspicious_search_attempt",
                {"user_id": current_user.id, "search_term": params["search_name"]},
            )
            flash("Invalid search term", "danger")
            return redirect(url_for("records.health_records_routes.list_records"))

    return None


def _build_records_query(params):
    """Build query for records list based on parameters"""
    if params["record_type"] == "own":
        query = HealthRecord.query.filter_by(user_id=current_user.id)
    elif params["record_type"] == "family":
        family_member_ids = [fm.id for fm in current_user.family_members]
        if family_member_ids:
            query = HealthRecord.query.filter(
                HealthRecord.family_member_id.in_(family_member_ids)
            )
        else:
            query = HealthRecord.query.filter_by(id=None)  # Empty query
    elif params["record_type"] == "family_member" and params["family_member_id"]:
        # Verify user has access to this family member
        family_member = FamilyMember.query.get(params["family_member_id"])
        if family_member and family_member in current_user.family_members:
            query = HealthRecord.query.filter_by(
                family_member_id=params["family_member_id"]
            )
        else:
            return _handle_invalid_family_member_access(params["family_member_id"])
    else:
        # Show all records (own + family)
        query = _filter_all_user_records(HealthRecord.query)

    # Apply search filter if provided
    if params["search_name"]:
        search_term = f"%{params['search_name']}%"
        query = query.filter(
            HealthRecord.chief_complaint.ilike(search_term)
            | HealthRecord.doctor.ilike(search_term)
            | HealthRecord.diagnosis.ilike(search_term)
        )

    return query


def _handle_invalid_family_member_access(family_member_id):
    """Handle invalid family member access attempt"""
    log_security_event(
        "unauthorized_family_member_access",
        {
            "user_id": current_user.id,
            "attempted_family_member_id": family_member_id,
        },
    )
    flash("You do not have access to this family member", "danger")


def _filter_all_user_records(query):
    """Filter to show all user's own records and family member records"""
    family_member_ids = [fm.id for fm in current_user.family_members]
    if family_member_ids:
        return query.filter(
            (HealthRecord.user_id == current_user.id)
            | (HealthRecord.family_member_id.in_(family_member_ids))
        )
    else:
        return query.filter_by(user_id=current_user.id)

"""
Health Records Routes Module

Main route handlers for health record operations.
Uses modular components for query processing and CRUD operations.
"""

import os
from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required

from ...models import Document, HealthRecord, db
from ...utils.export_utils import export_health_records_pdf, export_single_record_pdf
from ...utils.performance_monitor import monitor_performance
from ...utils.security_utils import log_security_event
from ..forms import RecordForm

# Import modular components
from ..query_utils import (
    build_records_query,
    get_record_statistics,
    parse_list_parameters,
    validate_search_parameters,
)
from ..record_operations import (
    create_health_record,
    delete_health_record,
    update_health_record,
    validate_record_ownership,
)

health_records_routes = Blueprint("health_records_routes", __name__)


@health_records_routes.route("/list")
@login_required
@monitor_performance
def list_records():
    """List all health records"""
    try:
        # Parse request parameters
        params = parse_list_parameters()

        # Validate search input
        validation_result = validate_search_parameters(params)
        if validation_result:
            return validation_result

        # Build and execute query
        query = build_records_query(params)
        pagination = query.paginate(
            page=params["page"], per_page=params["per_page"], error_out=False
        )

        # Get statistics
        stats = get_record_statistics()

        return render_template(
            "records/list.html",
            records=pagination.items,
            pagination=pagination,
            search=params["search"],
            sort_by=params["sort_by"],
            order=params["order"],
            stats=stats,
            title="Health Records",
        )

    except Exception as e:
        current_app.logger.error(f"Error listing records: {e}")
        flash("Error loading records. Please try again.", "error")
        return redirect(url_for("main.dashboard"))


@health_records_routes.route("/add", methods=["GET", "POST"])
@login_required
@monitor_performance
def add_record():
    """Add a new health record"""
    form = RecordForm()

    if form.validate_on_submit():
        # Prepare form data
        form_data = {
            "date": form.date.data,
            "chief_complaint": form.chief_complaint.data,
            "doctor": form.doctor.data,
            "investigations": form.investigations.data,
            "diagnosis": form.diagnosis.data,
            "prescription": form.prescription.data,
            "notes": form.notes.data,
            "review_followup": form.review_followup.data,
        }

        # Get uploaded files
        files = request.files.getlist("documents")

        # Create the record
        record = create_health_record(form_data, files)
        if record:
            flash("Health record added successfully!", "success")
            return redirect(url_for("health_records_routes.view_record", id=record.id))

    return render_template("records/add.html", form=form, title="Add Health Record")


@health_records_routes.route("/view/<int:id>")
@login_required
@monitor_performance
def view_record(id):
    """View a specific health record"""
    try:
        record = HealthRecord.query.get_or_404(id)

        # Validate ownership
        if not validate_record_ownership(record):
            log_security_event(
                f"Unauthorized access attempt to record {id} by user {current_user.id}"
            )
            flash("You don't have permission to view this record.", "error")
            return redirect(url_for("health_records_routes.list_records"))

        return render_template(
            "records/view.html", record=record, title=f"Health Record - {record.date}"
        )

    except Exception as e:
        current_app.logger.error(f"Error viewing record {id}: {e}")
        flash("Error loading record. Please try again.", "error")
        return redirect(url_for("health_records_routes.list_records"))


@health_records_routes.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@monitor_performance
def edit_record(id):
    """Edit a health record"""
    try:
        record = HealthRecord.query.get_or_404(id)

        # Validate ownership
        if not validate_record_ownership(record):
            log_security_event(
                f"Unauthorized edit attempt on record {id} by user {current_user.id}"
            )
            flash("You don't have permission to edit this record.", "error")
            return redirect(url_for("health_records_routes.list_records"))

        form = RecordForm(obj=record)

        if form.validate_on_submit():
            # Prepare form data
            form_data = {
                "date": form.date.data,
                "chief_complaint": form.chief_complaint.data,
                "doctor": form.doctor.data,
                "investigations": form.investigations.data,
                "diagnosis": form.diagnosis.data,
                "prescription": form.prescription.data,
                "notes": form.notes.data,
                "review_followup": form.review_followup.data,
            }

            # Get uploaded files
            files = request.files.getlist("documents")

            # Update the record
            if update_health_record(record, form_data, files):
                flash("Health record updated successfully!", "success")
                return redirect(
                    url_for("health_records_routes.view_record", id=record.id)
                )

        return render_template(
            "records/edit.html", form=form, record=record, title="Edit Health Record"
        )

    except Exception as e:
        current_app.logger.error(f"Error editing record {id}: {e}")
        flash("Error loading record for editing. Please try again.", "error")
        return redirect(url_for("health_records_routes.list_records"))


@health_records_routes.route("/delete/<int:id>", methods=["POST"])
@login_required
@monitor_performance
def delete_record(id):
    """Delete a health record"""
    try:
        record = HealthRecord.query.get_or_404(id)

        # Validate ownership
        if not validate_record_ownership(record):
            log_security_event(
                f"Unauthorized delete attempt on record {id} by user {current_user.id}"
            )
            flash("You don't have permission to delete this record.", "error")
            return redirect(url_for("health_records_routes.list_records"))

        # Delete the record
        if delete_health_record(record):
            flash("Health record deleted successfully!", "success")

        return redirect(url_for("health_records_routes.list_records"))

    except Exception as e:
        current_app.logger.error(f"Error deleting record {id}: {e}")
        flash("Error deleting record. Please try again.", "error")
        return redirect(url_for("health_records_routes.list_records"))


@health_records_routes.route("/export")
@login_required
@monitor_performance
def export_records():
    """Export user's health records to PDF"""
    try:
        records = (
            HealthRecord.query.filter_by(user_id=current_user.id)
            .order_by(HealthRecord.date.desc())
            .all()
        )

        if not records:
            flash("No records to export.", "info")
            return redirect(url_for("health_records_routes.list_records"))

        pdf_path = export_health_records_pdf(records, current_user)

        if pdf_path and os.path.exists(pdf_path):
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=f"health_records_{current_user.id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mimetype="application/pdf",
            )
        else:
            flash("Error generating PDF export.", "error")
            return redirect(url_for("health_records_routes.list_records"))

    except Exception as e:
        current_app.logger.error(f"Error exporting records: {e}")
        flash("Error exporting records. Please try again.", "error")
        return redirect(url_for("health_records_routes.list_records"))


@health_records_routes.route("/export/<int:id>")
@login_required
@monitor_performance
def export_single_record(id):
    """Export a single health record to PDF"""
    try:
        record = HealthRecord.query.get_or_404(id)

        # Validate ownership
        if not validate_record_ownership(record):
            log_security_event(
                f"Unauthorized export attempt on record {id} by user {current_user.id}"
            )
            flash("You don't have permission to export this record.", "error")
            return redirect(url_for("health_records_routes.list_records"))

        pdf_path = export_single_record_pdf(record)

        if pdf_path and os.path.exists(pdf_path):
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=f"health_record_{record.id}_{record.date.strftime('%Y%m%d') if record.date else 'undated'}.pdf",
                mimetype="application/pdf",
            )
        else:
            flash("Error generating PDF export.", "error")
            return redirect(url_for("health_records_routes.view_record", id=id))

    except Exception as e:
        current_app.logger.error(f"Error exporting record {id}: {e}")
        flash("Error exporting record. Please try again.", "error")
        return redirect(url_for("health_records_routes.view_record", id=id))


@health_records_routes.route("/download/<int:document_id>")
@login_required
@monitor_performance
def download_document(document_id):
    """Download a document file"""
    try:
        document = Document.query.get_or_404(document_id)

        # Validate ownership through health record
        if not validate_record_ownership(document.health_record):
            log_security_event(
                f"Unauthorized document download attempt: document {document_id} by user {current_user.id}"
            )
            flash("You don't have permission to download this document.", "error")
            return redirect(url_for("health_records_routes.list_records"))

        if document.file_path and os.path.exists(document.file_path):
            return send_file(
                document.file_path, as_attachment=True, download_name=document.filename
            )
        else:
            flash("Document file not found.", "error")
            return redirect(
                url_for(
                    "health_records_routes.view_record", id=document.health_record_id
                )
            )

    except Exception as e:
        current_app.logger.error(f"Error downloading document {document_id}: {e}")
        flash("Error downloading document. Please try again.", "error")
        return redirect(url_for("health_records_routes.list_records"))


@health_records_routes.route("/delete-document/<int:document_id>", methods=["POST"])
@login_required
@monitor_performance
def delete_document(document_id):
    """Delete a document file"""
    try:
        document = Document.query.get_or_404(document_id)
        record_id = document.health_record_id

        # Validate ownership through health record
        if not validate_record_ownership(document.health_record):
            log_security_event(
                f"Unauthorized document delete attempt: document {document_id} by user {current_user.id}"
            )
            flash("You don't have permission to delete this document.", "error")
            return redirect(url_for("health_records_routes.list_records"))

        # Delete the document file
        from ..record_operations import delete_document_file

        if delete_document_file(document):
            db.session.commit()
            flash("Document deleted successfully!", "success")
        else:
            flash("Error deleting document.", "error")

        return redirect(url_for("health_records_routes.view_record", id=record_id))

    except Exception as e:
        current_app.logger.error(f"Error deleting document {document_id}: {e}")
        flash("Error deleting document. Please try again.", "error")
        return redirect(url_for("health_records_routes.list_records"))

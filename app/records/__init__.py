import mimetypes
import os
import uuid
from datetime import datetime, timezone

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from werkzeug.utils import secure_filename
from wtforms import (
    DateField,
    FloatField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from .. import limiter
from ..models import Document, FamilyMember, HealthRecord, db
from ..utils.form_validators import SecurityValidationMixin, validate_file_upload
from ..utils.shared import (
    detect_suspicious_patterns,
    log_security_event,
    monitor_performance,
    sanitize_html,
    secure_filename_enhanced,
    validate_file_type,
)

records_bp = Blueprint("records", __name__, url_prefix="/records")


# Forms
class RecordForm(FlaskForm):
    family_member = SelectField("Family Member", coerce=int, validators=[Optional()])
    date = DateField("Date", format="%Y-%m-%d", validators=[DataRequired()])
    chief_complaint = TextAreaField(
        "Chief Complaint",
        validators=[Optional(), Length(max=2000)],
        render_kw={
            "rows": 3,
            "placeholder": "Describe the main reason for this visit or health concern",
        },
    )
    doctor = StringField(
        "Doctor",
        validators=[Optional(), Length(max=200)],
        render_kw={"placeholder": "Doctor's name or clinic/hospital"},
    )
    investigations = TextAreaField(
        "Investigations",
        validators=[Optional(), Length(max=3000)],
        render_kw={
            "rows": 4,
            "placeholder": "Tests ordered, procedures performed, imaging studies, etc.",
        },
    )
    diagnosis = TextAreaField(
        "Diagnosis",
        validators=[Optional(), Length(max=2000)],
        render_kw={
            "rows": 3,
            "placeholder": "Medical diagnosis or clinical impression",
        },
    )
    prescription = TextAreaField(
        "Prescription",
        validators=[Optional(), Length(max=3000)],
        render_kw={
            "rows": 4,
            "placeholder": "Medications prescribed with dosage and instructions",
        },
    )
    notes = TextAreaField(
        "Notes",
        validators=[Optional(), Length(max=5000)],
        render_kw={
            "rows": 4,
            "placeholder": "Additional notes, observations, or instructions",
        },
    )
    review_followup = TextAreaField(
        "Review / Follow up",
        validators=[Optional(), Length(max=1000)],
        render_kw={
            "rows": 2,
            "placeholder": "Next appointment date, follow-up instructions, monitoring requirements",
        },
    )
    documents = FileField(
        "Uploads",
        validators=[
            Optional(),
            FileAllowed(
                ["jpg", "jpeg", "png", "pdf"], "Only images and PDFs are allowed"
            ),
        ],
        render_kw={"multiple": True},
    )
    submit = SubmitField("Save Record")

    def validate_chief_complaint(self, chief_complaint):
        if chief_complaint.data and detect_suspicious_patterns(chief_complaint.data):
            raise ValidationError("Chief complaint contains invalid content.")

    def validate_doctor(self, doctor):
        if doctor.data and detect_suspicious_patterns(doctor.data):
            raise ValidationError("Doctor field contains invalid content.")

    def validate_diagnosis(self, diagnosis):
        if diagnosis.data and detect_suspicious_patterns(diagnosis.data):
            raise ValidationError("Diagnosis contains invalid content.")

    def validate_notes(self, notes):
        if notes.data and detect_suspicious_patterns(notes.data):
            raise ValidationError("Notes contain invalid content.")


class FamilyMemberForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    date_of_birth = DateField(
        "Date of Birth", format="%Y-%m-%d", validators=[Optional()]
    )
    relationship = StringField("Relationship", validators=[Optional()])

    # Basic Information
    gender = StringField("Gender", validators=[Optional()])
    blood_type = StringField("Blood Type", validators=[Optional()])
    height = FloatField("Height (cm)", validators=[Optional()])
    weight = FloatField("Weight (kg)", validators=[Optional()])

    # Medical History Section
    family_medical_history = TextAreaField(
        "Family Medical History",
        description="Provide family medical history including genetic conditions, hereditary diseases, etc.",
        validators=[Optional()],
    )
    surgical_history = TextAreaField(
        "Surgical History",
        description="List any past surgeries and dates",
        validators=[Optional()],
    )
    current_medications = TextAreaField(
        "Current Medications",
        description="List all current medications with dosages and frequencies",
        validators=[Optional()],
    )
    allergies = TextAreaField(
        "Known Allergies",
        description="List any known allergies (medications, foods, environmental)",
        validators=[Optional()],
    )
    chronic_conditions = TextAreaField(
        "Chronic Conditions",
        description="List any ongoing medical conditions",
        validators=[Optional()],
    )

    # Additional Notes
    notes = TextAreaField(
        "Additional Notes",
        description="Any other relevant medical information",
        validators=[Optional()],
    )

    submit = SubmitField("Save Family Member")


# Helper functions
# Helper functions for save_document
def _validate_and_secure_file(file):
    """Validate file and create secure filename"""
    # Enhanced security validation
    if not validate_file_type(file):
        log_security_event(
            "file_upload_rejected",
            {
                "user_id": current_user.id,
                "filename": file.filename,
                "reason": "Invalid file type or malicious content",
            },
        )
        raise ValueError("Invalid file type or potentially malicious file")

    # Use enhanced secure filename function
    filename = secure_filename_enhanced(file.filename)
    if not filename:
        raise ValueError("Invalid filename")

    # Create unique filename to avoid conflicts
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    return filename, unique_filename


def _create_upload_directory(record_id):
    """Create and secure upload directory"""
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], str(record_id))
    os.makedirs(upload_dir, exist_ok=True)
    os.chmod(upload_dir, 0o755)  # Secure permissions
    return upload_dir


def _save_and_validate_file_size(file, file_path):
    """Save file and validate size constraints"""
    file.save(file_path)
    file_size = os.path.getsize(file_path)

    # Enforce file size limits
    max_size = current_app.config.get(
        "MAX_CONTENT_LENGTH", 50 * 1024 * 1024
    )  # 50MB default
    if file_size > max_size:
        os.remove(file_path)
        raise ValueError(
            f"File size ({file_size} bytes) exceeds maximum allowed ({max_size} bytes)"
        )
    return file_size


def _validate_saved_file_content(file_path, filename):
    """Validate saved file content for security"""
    if not validate_file_type(file_path):
        os.remove(file_path)
        log_security_event(
            "file_upload_rejected",
            {
                "user_id": current_user.id,
                "filename": filename,
                "reason": "File content validation failed",
            },
        )
        raise ValueError("File content validation failed")


def _extract_text_if_pdf(file_path, file_type, filename):
    """Extract text from PDF files if applicable"""
    extracted_text = None

    if file_type == "pdf":
        try:
            from ..ai import extract_text_from_pdf

            current_app.logger.info(f"Extracting text from uploaded PDF: {filename}")
            extracted_text = extract_text_from_pdf(file_path)
            if extracted_text and extracted_text.strip():
                current_app.logger.info(
                    f"Successfully extracted {len(extracted_text)} characters from {filename}"
                )
                # Sanitize extracted text
                extracted_text = sanitize_html(extracted_text)
            else:
                current_app.logger.warning(f"No text extracted from PDF {filename}")
                extracted_text = None
        except Exception as e:
            current_app.logger.error(f"Error extracting text from PDF {filename}: {e}")
            extracted_text = None

    return extracted_text


@monitor_performance
def save_document(file, record_id):
    """Save an uploaded document and return file information"""
    try:
        filename, unique_filename = _validate_and_secure_file(file)
        upload_dir = _create_upload_directory(record_id)
        file_path = os.path.join(upload_dir, unique_filename)

        file_size = _save_and_validate_file_size(file, file_path)

        # Determine file type and validate again
        file_type = os.path.splitext(filename)[1].lower().replace(".", "")
        if file_type == "jpg":
            file_type = "jpeg"

        _validate_saved_file_content(file_path, filename)
        extracted_text = _extract_text_if_pdf(file_path, file_type, filename)

        # Log successful upload
        log_security_event(
            "file_upload_success",
            {
                "user_id": current_user.id,
                "filename": filename,
                "file_size": file_size,
                "file_type": file_type,
            },
        )

        return {
            "filename": filename,
            "file_path": file_path,
            "file_type": file_type,
            "file_size": file_size,
            "extracted_text": extracted_text,
        }

    except Exception as e:
        current_app.logger.error(f"Error saving document: {e}")
        # Clean up any partial file
        if "file_path" in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise


# Routes
@records_bp.route("/dashboard")
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

    return render_template(
        "records/dashboard.html",
        title="Dashboard",
        own_records=own_records,
        family_records=family_records,
        family_members=family_members,
    )


@records_bp.route("/list")
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
            return redirect(url_for("records.list_records"))

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
        return redirect(url_for("records.dashboard"))


@records_bp.route("/create", methods=["GET", "POST"])
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
                    return redirect(url_for("records.create_record"))

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


@records_bp.route("/<int:record_id>")
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
            return redirect(url_for("records.dashboard"))

        # Log successful record access
        log_security_event(
            "health_record_accessed",
            {"user_id": current_user.id, "record_id": record_id},
        )

        return render_template("records/view.html", title=record.title, record=record)

    except Exception as e:
        current_app.logger.error(f"Error viewing record {record_id}: {e}")
        flash("An error occurred while loading the record", "danger")
        return redirect(url_for("records.dashboard"))


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
    return redirect(url_for("records.dashboard"))


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


@records_bp.route("/<int:record_id>/edit", methods=["GET", "POST"])
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
        return redirect(url_for("records.dashboard"))


@records_bp.route("/<int:record_id>/delete", methods=["POST"])
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
            return redirect(url_for("records.dashboard"))

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
        return redirect(url_for("records.list_records"))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting record {record_id}: {e}")
        flash("An error occurred while deleting the record", "danger")
        return redirect(url_for("records.dashboard"))


# Family member routes
@records_bp.route("/family")
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


@records_bp.route("/family/add", methods=["GET", "POST"])
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

            # Validate names contain no suspicious patterns
            if detect_suspicious_patterns(first_name) or detect_suspicious_patterns(
                last_name
            ):
                log_security_event(
                    "suspicious_family_member_name",
                    {
                        "user_id": current_user.id,
                        "first_name": first_name,
                        "last_name": last_name,
                    },
                )
                flash("Invalid characters in name fields", "danger")
                return render_template(
                    "records/family_form.html", title="Add Family Member", form=form
                )

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
            )

            # Add to current user's family members
            current_user.family_members.append(family_member)
            db.session.add(family_member)
            db.session.commit()

            # Create initial medical history records if provided
            records_to_create = []

            if family_medical_history:
                records_to_create.append(
                    HealthRecord(
                        title="Family Medical History",
                        record_type="note",
                        description=family_medical_history,
                        date=datetime.now(timezone.utc),
                        family_member_id=family_member.id,
                    )
                )

            if surgical_history:
                records_to_create.append(
                    HealthRecord(
                        title="Surgical History",
                        record_type="note",
                        description=surgical_history,
                        date=datetime.now(timezone.utc),
                        family_member_id=family_member.id,
                    )
                )

            if current_medications:
                records_to_create.append(
                    HealthRecord(
                        title="Current Medications",
                        record_type="prescription",
                        description=current_medications,
                        date=datetime.now(timezone.utc),
                        family_member_id=family_member.id,
                    )
                )

            if allergies:
                records_to_create.append(
                    HealthRecord(
                        title="Known Allergies",
                        record_type="note",
                        description=allergies,
                        date=datetime.now(timezone.utc),
                        family_member_id=family_member.id,
                    )
                )

            if chronic_conditions:
                records_to_create.append(
                    HealthRecord(
                        title="Chronic Conditions",
                        record_type="note",
                        description=chronic_conditions,
                        date=datetime.now(timezone.utc),
                        family_member_id=family_member.id,
                    )
                )

            # Add all records at once
            for record in records_to_create:
                db.session.add(record)

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
                f"Family member {family_member.first_name} {family_member.last_name} added successfully with complete medical history!",
                "success",
            )
            return redirect(url_for("records.list_family"))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding family member: {e}")
            flash(
                "An error occurred while adding the family member. Please try again.",
                "danger",
            )

    return render_template(
        "records/family_form.html", title="Add Family Member", form=form
    )


@records_bp.route("/family/<int:family_member_id>/edit", methods=["GET", "POST"])
@login_required
def edit_family_member(family_member_id):
    """Edit an existing family member"""
    family_member = FamilyMember.query.get_or_404(family_member_id)

    # Check if the family member belongs to the current user
    if family_member not in current_user.family_members:
        flash("You do not have permission to edit this family member", "danger")
        return redirect(url_for("records.list_family"))

    form = FamilyMemberForm()

    if form.validate_on_submit():
        # Update family member information
        family_member.first_name = form.first_name.data
        family_member.last_name = form.last_name.data
        family_member.date_of_birth = form.date_of_birth.data
        family_member.relationship = form.relationship.data
        family_member.gender = form.gender.data
        family_member.blood_type = form.blood_type.data
        family_member.height = form.height.data
        family_member.weight = form.weight.data
        family_member.family_medical_history = form.family_medical_history.data
        family_member.surgical_history = form.surgical_history.data
        family_member.current_medications = form.current_medications.data
        family_member.allergies = form.allergies.data
        family_member.chronic_conditions = form.chronic_conditions.data
        family_member.notes = form.notes.data

        db.session.commit()

        flash(
            f"Family member {family_member.first_name} {family_member.last_name} updated successfully!",
            "success",
        )
        return redirect(url_for("records.list_family"))

    elif request.method == "GET":
        # Populate form with existing family member data
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

    return render_template(
        "records/family_form.html",
        title=f"Edit {family_member.first_name} {family_member.last_name}",
        form=form,
        family_member=family_member,
    )


@records_bp.route("/family/<int:family_member_id>/delete", methods=["POST"])
@login_required
def delete_family_member(family_member_id):
    """Delete a family member and all associated records"""
    family_member = FamilyMember.query.get_or_404(family_member_id)

    # Check if the family member belongs to the current user
    if family_member not in current_user.family_members:
        flash("You do not have permission to delete this family member", "danger")
        return redirect(url_for("records.list_family"))

    # Get family member name for flash message
    member_name = f"{family_member.first_name} {family_member.last_name}"

    # Get associated health records to delete documents
    associated_records = HealthRecord.query.filter_by(
        family_member_id=family_member.id
    ).all()

    # Delete files associated with health records
    for record in associated_records:
        documents = Document.query.filter_by(health_record_id=record.id).all()
        for doc in documents:
            try:
                os.remove(doc.file_path)
            except (FileNotFoundError, PermissionError) as e:
                current_app.logger.error(f"Error deleting file {doc.file_path}: {e}")

    # Delete family member (cascade will delete associated records and documents)
    db.session.delete(family_member)
    db.session.commit()

    flash(
        f"Family member {member_name} and all associated records have been deleted successfully",
        "success",
    )
    return redirect(url_for("records.list_family"))


@records_bp.route("/family/<int:family_member_id>")
@login_required
def view_family_member(family_member_id):
    """View a specific family member's details"""
    family_member = FamilyMember.query.get_or_404(family_member_id)

    # Check if the family member belongs to the current user
    if family_member not in current_user.family_members:
        flash("You do not have permission to view this family member", "danger")
        return redirect(url_for("records.list_family"))

    # Get recent health records for this family member
    recent_records = (
        HealthRecord.query.filter_by(family_member_id=family_member.id)
        .order_by(HealthRecord.date.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "records/family_profile.html",
        title=f"{family_member.first_name} {family_member.last_name}",
        family_member=family_member,
        recent_records=recent_records,
    )


def _validate_filename_security(filename, record_id):
    """Validate filename for security issues"""
    if not filename or ".." in filename or "/" in filename or "\\" in filename:
        log_security_event(
            "file_access_path_traversal_attempt",
            {
                "user_id": current_user.id,
                "filename": filename,
                "record_id": record_id,
            },
        )
        return False
    return True


def _check_file_access_permission(record):
    """Check if current user has permission to access files from this record"""
    if record.user_id == current_user.id:
        return True
    if record.family_member_id and record.family_member in current_user.family_members:
        return True
    return False


def _handle_unauthorized_file_access(record_id, filename, record):
    """Handle unauthorized file access attempt"""
    log_security_event(
        "unauthorized_file_access_attempt",
        {
            "user_id": current_user.id,
            "record_id": record_id,
            "filename": filename,
            "record_owner_id": record.user_id,
            "record_family_member_id": record.family_member_id,
        },
    )
    abort(404)  # Return 404 instead of 403 to avoid information disclosure


def _verify_document_belongs_to_record(record_id, filename):
    """Verify that the requested file belongs to this record"""
    document = (
        Document.query.filter_by(health_record_id=record_id)
        .filter(Document.file_path.endswith(filename))
        .first()
    )

    if not document:
        log_security_event(
            "file_access_invalid_document",
            {
                "user_id": current_user.id,
                "record_id": record_id,
                "filename": filename,
            },
        )
        return False
    return True


def _validate_file_path_security(file_path, file_directory, record_id, filename):
    """Validate file path for directory traversal attacks"""
    real_file_path = os.path.realpath(file_path)
    real_upload_dir = os.path.realpath(file_directory)

    if not real_file_path.startswith(real_upload_dir):
        log_security_event(
            "file_access_directory_traversal",
            {
                "user_id": current_user.id,
                "record_id": record_id,
                "filename": filename,
                "attempted_path": file_path,
            },
        )
        return False
    return True


def _determine_file_mimetype(filename):
    """Determine appropriate MIME type for file"""
    mimetype = mimetypes.guess_type(filename)[0]
    if not mimetype:
        if filename.lower().endswith(".pdf"):
            mimetype = "application/pdf"
        elif filename.lower().endswith((".jpg", ".jpeg")):
            mimetype = "image/jpeg"
        elif filename.lower().endswith(".png"):
            mimetype = "image/png"
        else:
            mimetype = "application/octet-stream"
    return mimetype


@records_bp.route("/uploads/<int:record_id>/<filename>")
@login_required
@limiter.limit("30 per minute")  # Rate limit file access
@monitor_performance
def serve_upload(record_id, filename):
    """Securely serve uploaded files"""
    try:
        # Validate filename security
        if not _validate_filename_security(filename, record_id):
            abort(404)

        # Get the record to check permissions
        record = HealthRecord.query.get_or_404(record_id)

        # Check file access permissions
        if not _check_file_access_permission(record):
            _handle_unauthorized_file_access(record_id, filename, record)

        # Verify document belongs to record
        if not _verify_document_belongs_to_record(record_id, filename):
            abort(404)

        # Check if file exists on disk
        file_directory = os.path.join(
            current_app.config["UPLOAD_FOLDER"], str(record_id)
        )
        file_path = os.path.join(file_directory, filename)

        # Validate file path security
        if not _validate_file_path_security(
            file_path, file_directory, record_id, filename
        ):
            abort(404)

        if not os.path.exists(file_path):
            current_app.logger.error(f"File not found on disk: {file_path}")
            abort(404)

        # Determine MIME type
        mimetype = _determine_file_mimetype(filename)

        # Log successful file access
        log_security_event(
            "file_accessed",
            {
                "user_id": current_user.id,
                "record_id": record_id,
                "filename": filename,
                "file_size": os.path.getsize(file_path),
            },
        )

        try:
            return send_from_directory(
                directory=file_directory,
                path=filename,
                mimetype=mimetype,
                as_attachment=False,  # Display inline for images and PDFs
            )
        except Exception as e:
            current_app.logger.error(f"Error serving file {file_path}: {e}")
            abort(404)

    except Exception as e:
        current_app.logger.error(f"Error in serve_upload: {e}")
        abort(404)


def _parse_list_parameters():
    """Parse and return request parameters for list_records"""
    return {
        "page": request.args.get("page", 1, type=int),
        "record_type": request.args.get("type", None),
        "family_member_id": request.args.get("family_member", None, type=int),
        "search_name": request.args.get("name", None),
    }


def _validate_search_parameters(params):
    """Validate search parameters and return redirect if invalid"""
    search_name = params["search_name"]
    if search_name:
        search_name = sanitize_html(search_name.strip())
        params["search_name"] = search_name  # Update the sanitized value

        if detect_suspicious_patterns(search_name):
            log_security_event(
                "suspicious_search_attempt",
                {"user_id": current_user.id, "search_term": search_name},
            )
            flash("Invalid search parameters", "danger")
            return redirect(url_for("records.list_records"))
    return None


def _build_records_query(params):
    """Build the database query based on parameters"""
    query = HealthRecord.query

    # Apply filters
    if params["record_type"]:
        query = query.filter_by(record_type=params["record_type"])

    if params["search_name"]:
        query = query.filter(HealthRecord.title.ilike(f"%{params['search_name']}%"))

    # Apply family member filter
    return _apply_family_member_filter(query, params["family_member_id"])


def _apply_family_member_filter(query, family_member_id):
    """Apply family member filtering to the query"""
    if family_member_id is not None:
        if family_member_id == 0:
            return query.filter_by(user_id=current_user.id)
        else:
            return _filter_by_family_member(query, family_member_id)
    else:
        return _filter_all_user_records(query)


def _filter_by_family_member(query, family_member_id):
    """Filter by specific family member with security check"""
    family_member = FamilyMember.query.get(family_member_id)
    if family_member and family_member in current_user.family_members:
        return query.filter_by(family_member_id=family_member_id)
    else:
        log_security_event(
            "unauthorized_family_access_attempt",
            {
                "user_id": current_user.id,
                "attempted_family_member_id": family_member_id,
            },
        )
        flash("You do not have access to this family member", "danger")
        return None  # Will cause redirect in calling function


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

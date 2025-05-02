from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from ..models import db, HealthRecord, Document, FamilyMember

records_bp = Blueprint('records', __name__, url_prefix='/records')

# Forms
class RecordForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    record_type = SelectField('Record Type', validators=[DataRequired()],
                             choices=[('complaint', 'Complaint/Symptom'),
                                     ('doctor_visit', 'Doctor Visit'),
                                     ('investigation', 'Investigation'),
                                     ('prescription', 'Prescription'),
                                     ('lab_report', 'Lab Report'),
                                     ('note', 'Doctor\'s Note')])
    description = TextAreaField('Description', validators=[Optional(), Length(max=5000)])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    family_member = SelectField('Family Member', coerce=int, validators=[Optional()])
    documents = FileField('Upload Documents', validators=[Optional(),
                                                         FileAllowed(['jpg', 'jpeg', 'png', 'pdf'],
                                                                    'Only images and PDFs are allowed')])
    submit = SubmitField('Save Record')

class FamilyMemberForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    relationship = StringField('Relationship', validators=[Optional()])
    submit = SubmitField('Save Family Member')

# Helper functions
def save_document(file, record_id):
    """Save an uploaded document and return file information"""
    filename = secure_filename(file.filename)
    # Create unique filename to avoid conflicts
    unique_filename = f"{uuid.uuid4().hex}_{filename}"

    # Ensure upload directory exists
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(record_id))
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)

    # Determine file type and size
    file_type = os.path.splitext(filename)[1].lower().replace('.', '')
    if file_type == 'jpg':
        file_type = 'jpeg'
    file_size = os.path.getsize(file_path)

    return {
        'filename': filename,
        'file_path': file_path,
        'file_type': file_type,
        'file_size': file_size
    }

# Routes
@records_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard showing recent records and stats"""
    # Get latest records
    own_records = HealthRecord.query.filter_by(user_id=current_user.id)\
                                   .order_by(HealthRecord.date.desc())\
                                   .limit(5).all()

    # Get family members
    family_members = current_user.family_members

    # Get family records if there are family members
    family_records = []
    if family_members:
        family_member_ids = [fm.id for fm in family_members]
        family_records = HealthRecord.query.filter(HealthRecord.family_member_id.in_(family_member_ids))\
                                         .order_by(HealthRecord.date.desc())\
                                         .limit(5).all()

    return render_template('records/dashboard.html',
                          title='Dashboard',
                          own_records=own_records,
                          family_records=family_records,
                          family_members=family_members)

@records_bp.route('/list')
@login_required
def list_records():
    """List all health records"""
    page = request.args.get('page', 1, type=int)
    record_type = request.args.get('type', None)
    family_member_id = request.args.get('family_member', None, type=int)

    # Base query
    query = HealthRecord.query

    # Filter by record type if specified
    if record_type:
        query = query.filter_by(record_type=record_type)

    # Filter by owner (user or specified family member)
    if family_member_id:
        # Check if the family member belongs to the current user
        if FamilyMember.query.get(family_member_id) in current_user.family_members:
            query = query.filter_by(family_member_id=family_member_id)
        else:
            flash('You do not have access to this family member', 'danger')
            return redirect(url_for('records.list_records'))
    else:
        # Show user's own records
        query = query.filter_by(user_id=current_user.id)

    # Order by date, newest first
    records = query.order_by(HealthRecord.date.desc()).paginate(page=page, per_page=10)

    return render_template('records/list.html',
                          title='Health Records',
                          records=records,
                          record_type=record_type,
                          family_member_id=family_member_id)

@records_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_record():
    """Create a new health record"""
    form = RecordForm()

    # Populate family member choices
    family_members = [(0, 'Myself')] + [(m.id, f"{m.first_name} {m.last_name}") for m in current_user.family_members]
    form.family_member.choices = family_members

    if form.validate_on_submit():
        # Create new health record
        record = HealthRecord(
            title=form.title.data,
            record_type=form.record_type.data,
            description=form.description.data,
            date=form.date.data
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
                flash('Invalid family member selection', 'danger')
                return redirect(url_for('records.create_record'))

        # Save record to get an ID
        db.session.add(record)
        db.session.commit()

        # Handle document upload if provided
        if form.documents.data:
            file = form.documents.data
            file_info = save_document(file, record.id)

            # Create document record
            document = Document(
                filename=file_info['filename'],
                file_path=file_info['file_path'],
                file_type=file_info['file_type'],
                file_size=file_info['file_size'],
                health_record_id=record.id
            )
            db.session.add(document)
            db.session.commit()

        flash('Health record created successfully!', 'success')
        return redirect(url_for('records.view_record', record_id=record.id))

    return render_template('records/create.html', title='Create Record', form=form)

@records_bp.route('/<int:record_id>')
@login_required
def view_record(record_id):
    """View a specific health record"""
    record = HealthRecord.query.get_or_404(record_id)

    # Check if user has permission to view this record
    if record.user_id == current_user.id:
        # This is the user's own record
        pass
    elif record.family_member_id and record.family_member in current_user.family_members:
        # This is a record for a family member of the user
        pass
    else:
        flash('You do not have permission to view this record', 'danger')
        return redirect(url_for('records.dashboard'))

    return render_template('records/view.html', title=record.title, record=record)

@records_bp.route('/<int:record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_record(record_id):
    """Edit an existing health record"""
    record = HealthRecord.query.get_or_404(record_id)

    # Check if user has permission to edit this record
    if record.user_id == current_user.id:
        # This is the user's own record
        pass
    elif record.family_member_id and record.family_member in current_user.family_members:
        # This is a record for a family member of the user
        pass
    else:
        flash('You do not have permission to edit this record', 'danger')
        return redirect(url_for('records.dashboard'))

    form = RecordForm()

    # Populate family member choices
    family_members = [(0, 'Myself')] + [(m.id, f"{m.first_name} {m.last_name}") for m in current_user.family_members]
    form.family_member.choices = family_members

    if form.validate_on_submit():
        # Update record fields
        record.title = form.title.data
        record.record_type = form.record_type.data
        record.description = form.description.data
        record.date = form.date.data
        record.updated_at = datetime.utcnow()

        # Update user or family member assignment
        if form.family_member.data == 0:
            record.user_id = current_user.id
            record.family_member_id = None
        else:
            # Verify family member belongs to current user
            family_member = FamilyMember.query.get(form.family_member.data)
            if family_member and family_member in current_user.family_members:
                record.family_member_id = family_member.id
                record.user_id = None
            else:
                flash('Invalid family member selection', 'danger')
                return redirect(url_for('records.edit_record', record_id=record.id))

        # Handle document upload if provided
        if form.documents.data:
            file = form.documents.data
            file_info = save_document(file, record.id)

            # Create document record
            document = Document(
                filename=file_info['filename'],
                file_path=file_info['file_path'],
                file_type=file_info['file_type'],
                file_size=file_info['file_size'],
                health_record_id=record.id
            )
            db.session.add(document)

        db.session.commit()
        flash('Health record updated successfully!', 'success')
        return redirect(url_for('records.view_record', record_id=record.id))

    elif request.method == 'GET':
        # Populate form with existing record data
        form.title.data = record.title
        form.record_type.data = record.record_type
        form.description.data = record.description
        form.date.data = record.date

        # Set appropriate family member
        if record.user_id:
            form.family_member.data = 0
        else:
            form.family_member.data = record.family_member_id

    return render_template('records/edit.html', title='Edit Record', form=form, record=record)

@records_bp.route('/<int:record_id>/delete', methods=['POST'])
@login_required
def delete_record(record_id):
    """Delete a health record"""
    record = HealthRecord.query.get_or_404(record_id)

    # Check if user has permission to delete this record
    if record.user_id == current_user.id:
        # This is the user's own record
        pass
    elif record.family_member_id and record.family_member in current_user.family_members:
        # This is a record for a family member of the user
        pass
    else:
        flash('You do not have permission to delete this record', 'danger')
        return redirect(url_for('records.dashboard'))

    # Get associated documents to delete files
    documents = Document.query.filter_by(health_record_id=record.id).all()

    # Delete files from disk
    for doc in documents:
        try:
            os.remove(doc.file_path)
        except (FileNotFoundError, PermissionError) as e:
            current_app.logger.error(f"Error deleting file {doc.file_path}: {e}")

    # Delete record (cascade will delete associated documents)
    db.session.delete(record)
    db.session.commit()

    flash('Health record deleted successfully', 'success')
    return redirect(url_for('records.list_records'))

# Family member routes
@records_bp.route('/family')
@login_required
def list_family():
    """List all family members"""
    family_members = current_user.family_members
    return render_template('records/family_list.html',
                          title='Family Members',
                          family_members=family_members)

@records_bp.route('/family/add', methods=['GET', 'POST'])
@login_required
def add_family_member():
    """Add a new family member"""
    form = FamilyMemberForm()

    if form.validate_on_submit():
        family_member = FamilyMember(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            date_of_birth=form.date_of_birth.data,
            relationship=form.relationship.data
        )

        # Add to current user's family members
        current_user.family_members.append(family_member)
        db.session.add(family_member)
        db.session.commit()

        flash('Family member added successfully!', 'success')
        return redirect(url_for('records.list_family'))

    return render_template('records/family_form.html',
                          title='Add Family Member',
                          form=form)
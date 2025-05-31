from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField, FloatField
from wtforms.validators import DataRequired, Length, Optional
import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from ..models import db, HealthRecord, Document, FamilyMember

records_bp = Blueprint('records', __name__, url_prefix='/records')

# Forms
class RecordForm(FlaskForm):
    family_member = SelectField('Family Member', coerce=int, validators=[Optional()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    chief_complaint = TextAreaField('Chief Complaint', validators=[Optional(), Length(max=2000)], 
                                   render_kw={'rows': 3, 'placeholder': 'Describe the main reason for this visit or health concern'})
    doctor = StringField('Doctor', validators=[Optional(), Length(max=200)], 
                        render_kw={'placeholder': 'Doctor\'s name or clinic/hospital'})
    investigations = TextAreaField('Investigations', validators=[Optional(), Length(max=3000)], 
                                  render_kw={'rows': 4, 'placeholder': 'Tests ordered, procedures performed, imaging studies, etc.'})
    diagnosis = TextAreaField('Diagnosis', validators=[Optional(), Length(max=2000)], 
                             render_kw={'rows': 3, 'placeholder': 'Medical diagnosis or clinical impression'})
    prescription = TextAreaField('Prescription', validators=[Optional(), Length(max=3000)], 
                                render_kw={'rows': 4, 'placeholder': 'Medications prescribed with dosage and instructions'})
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=5000)], 
                         render_kw={'rows': 4, 'placeholder': 'Additional notes, observations, or instructions'})
    review_followup = TextAreaField('Review / Follow up', validators=[Optional(), Length(max=1000)], 
                                   render_kw={'rows': 2, 'placeholder': 'Next appointment date, follow-up instructions, monitoring requirements'})
    documents = FileField('Uploads', validators=[Optional(),
                                                FileAllowed(['jpg', 'jpeg', 'png', 'pdf'],
                                                           'Only images and PDFs are allowed')],
                         render_kw={'multiple': True})
    submit = SubmitField('Save Record')

class FamilyMemberForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    relationship = StringField('Relationship', validators=[Optional()])
    
    # Basic Information
    gender = StringField('Gender', validators=[Optional()])
    blood_type = StringField('Blood Type', validators=[Optional()])
    height = FloatField('Height (cm)', validators=[Optional()])
    weight = FloatField('Weight (kg)', validators=[Optional()])
    
    # Medical History Section
    family_medical_history = TextAreaField('Family Medical History', 
                                         description='Provide family medical history including genetic conditions, hereditary diseases, etc.',
                                         validators=[Optional()])
    surgical_history = TextAreaField('Surgical History',
                                   description='List any past surgeries and dates',
                                   validators=[Optional()])
    current_medications = TextAreaField('Current Medications',
                                      description='List all current medications with dosages and frequencies',
                                      validators=[Optional()])
    allergies = TextAreaField('Known Allergies',
                            description='List any known allergies (medications, foods, environmental)',
                            validators=[Optional()])
    chronic_conditions = TextAreaField('Chronic Conditions',
                                     description='List any ongoing medical conditions',
                                     validators=[Optional()])
    
    # Additional Notes
    notes = TextAreaField('Additional Notes',
                         description='Any other relevant medical information',
                         validators=[Optional()])
    
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

    # Initialize extracted text
    extracted_text = None
    
    # For PDF files, automatically extract text using OCR
    if file_type == 'pdf':
        try:
            from ..ai import extract_text_from_pdf
            current_app.logger.info(f"Extracting text from uploaded PDF: {filename}")
            extracted_text = extract_text_from_pdf(file_path)
            if extracted_text and extracted_text.strip():
                current_app.logger.info(f"Successfully extracted {len(extracted_text)} characters from {filename}")
            else:
                current_app.logger.warning(f"No text extracted from PDF {filename}")
                extracted_text = None
        except Exception as e:
            current_app.logger.error(f"Error extracting text from PDF {filename}: {e}")
            extracted_text = None

    return {
        'filename': filename,
        'file_path': file_path,
        'file_type': file_type,
        'file_size': file_size,
        'extracted_text': extracted_text
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
    search_name = request.args.get('name', None)

    # Base query
    query = HealthRecord.query

    # Filter by record type if specified
    if record_type:
        query = query.filter_by(record_type=record_type)

    # Filter by name (title) if specified
    if search_name:
        query = query.filter(HealthRecord.title.ilike(f'%{search_name}%'))

    # Filter by owner (user or specified family member)
    if family_member_id is not None:
        if family_member_id == 0:
            # Show only user's own records
            query = query.filter_by(user_id=current_user.id)
        else:
            # Check if the family member belongs to the current user
            family_member = FamilyMember.query.get(family_member_id)
            if family_member and family_member in current_user.family_members:
                query = query.filter_by(family_member_id=family_member_id)
            else:
                flash('You do not have access to this family member', 'danger')
                return redirect(url_for('records.list_records'))
    else:
        # Show user's own records and family member records
        family_member_ids = [fm.id for fm in current_user.family_members]
        if family_member_ids:
            query = query.filter(
                (HealthRecord.user_id == current_user.id) |
                (HealthRecord.family_member_id.in_(family_member_ids))
            )
        else:
            query = query.filter_by(user_id=current_user.id)

    # Order by date, newest first
    records = query.order_by(HealthRecord.date.desc()).paginate(page=page, per_page=10)

    return render_template('records/list.html',
                          title='Health Records',
                          records=records,
                          record_type=record_type,
                          family_member_id=family_member_id,
                          search_name=search_name)

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
            date=form.date.data,
            chief_complaint=form.chief_complaint.data,
            doctor=form.doctor.data,
            investigations=form.investigations.data,
            diagnosis=form.diagnosis.data,
            prescription=form.prescription.data,
            notes=form.notes.data,
            review_followup=form.review_followup.data
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

        # Handle multiple document uploads if provided
        if form.documents.data:
            files = request.files.getlist('documents')
            for file in files:
                if file and file.filename:  # Check if file is not empty
                    file_info = save_document(file, record.id)

                    # Create document record
                    document = Document(
                        filename=file_info['filename'],
                        file_path=file_info['file_path'],
                        file_type=file_info['file_type'],
                        file_size=file_info['file_size'],
                        extracted_text=file_info['extracted_text'],
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
        record.date = form.date.data
        record.chief_complaint = form.chief_complaint.data
        record.doctor = form.doctor.data
        record.investigations = form.investigations.data
        record.diagnosis = form.diagnosis.data
        record.prescription = form.prescription.data
        record.notes = form.notes.data
        record.review_followup = form.review_followup.data
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

        # Handle multiple document uploads if provided
        if form.documents.data:
            files = request.files.getlist('documents')
            for file in files:
                if file and file.filename:  # Check if file is not empty
                    file_info = save_document(file, record.id)

                    # Create document record
                    document = Document(
                        filename=file_info['filename'],
                        file_path=file_info['file_path'],
                        file_type=file_info['file_type'],
                        file_size=file_info['file_size'],
                        extracted_text=file_info['extracted_text'],
                        health_record_id=record.id
                    )
                    db.session.add(document)

        db.session.commit()
        flash('Health record updated successfully!', 'success')
        return redirect(url_for('records.view_record', record_id=record.id))

    elif request.method == 'GET':
        # Populate form with existing record data
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
    """Add a new family member with complete medical history"""
    form = FamilyMemberForm()

    if form.validate_on_submit():
        family_member = FamilyMember(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            date_of_birth=form.date_of_birth.data,
            relationship=form.relationship.data,
            gender=form.gender.data,
            blood_type=form.blood_type.data,
            height=form.height.data,
            weight=form.weight.data,
            family_medical_history=form.family_medical_history.data,
            surgical_history=form.surgical_history.data,
            current_medications=form.current_medications.data,
            allergies=form.allergies.data,
            chronic_conditions=form.chronic_conditions.data,
            notes=form.notes.data
        )

        # Add to current user's family members
        current_user.family_members.append(family_member)
        db.session.add(family_member)
        db.session.commit()

        # Create initial medical history records if provided
        records_to_create = []
        
        if form.family_medical_history.data:
            records_to_create.append(HealthRecord(
                title="Family Medical History",
                record_type="note",
                description=form.family_medical_history.data,
                date=datetime.utcnow(),
                family_member_id=family_member.id
            ))
        
        if form.surgical_history.data:
            records_to_create.append(HealthRecord(
                title="Surgical History",
                record_type="note",
                description=form.surgical_history.data,
                date=datetime.utcnow(),
                family_member_id=family_member.id
            ))
        
        if form.current_medications.data:
            records_to_create.append(HealthRecord(
                title="Current Medications",
                record_type="prescription",
                description=form.current_medications.data,
                date=datetime.utcnow(),
                family_member_id=family_member.id
            ))
        
        if form.allergies.data:
            records_to_create.append(HealthRecord(
                title="Known Allergies",
                record_type="note",
                description=form.allergies.data,
                date=datetime.utcnow(),
                family_member_id=family_member.id
            ))
        
        if form.chronic_conditions.data:
            records_to_create.append(HealthRecord(
                title="Chronic Conditions",
                record_type="note",
                description=form.chronic_conditions.data,
                date=datetime.utcnow(),
                family_member_id=family_member.id
            ))
        
        # Add all records at once
        for record in records_to_create:
            db.session.add(record)
        
        db.session.commit()

        flash(f'Family member {family_member.first_name} {family_member.last_name} added successfully with complete medical history!', 'success')
        return redirect(url_for('records.list_family'))

    return render_template('records/family_form.html',
                          title='Add Family Member',
                          form=form)

@records_bp.route('/family/<int:family_member_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_family_member(family_member_id):
    """Edit an existing family member"""
    family_member = FamilyMember.query.get_or_404(family_member_id)
    
    # Check if the family member belongs to the current user
    if family_member not in current_user.family_members:
        flash('You do not have permission to edit this family member', 'danger')
        return redirect(url_for('records.list_family'))
    
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

        flash(f'Family member {family_member.first_name} {family_member.last_name} updated successfully!', 'success')
        return redirect(url_for('records.list_family'))

    elif request.method == 'GET':
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

    return render_template('records/family_form.html',
                          title=f'Edit {family_member.first_name} {family_member.last_name}',
                          form=form,
                          family_member=family_member)

@records_bp.route('/family/<int:family_member_id>/delete', methods=['POST'])
@login_required
def delete_family_member(family_member_id):
    """Delete a family member and all associated records"""
    family_member = FamilyMember.query.get_or_404(family_member_id)
    
    # Check if the family member belongs to the current user
    if family_member not in current_user.family_members:
        flash('You do not have permission to delete this family member', 'danger')
        return redirect(url_for('records.list_family'))
    
    # Get family member name for flash message
    member_name = f"{family_member.first_name} {family_member.last_name}"
    
    # Get associated health records to delete documents
    associated_records = HealthRecord.query.filter_by(family_member_id=family_member.id).all()
    
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

    flash(f'Family member {member_name} and all associated records have been deleted successfully', 'success')
    return redirect(url_for('records.list_family'))

@records_bp.route('/family/<int:family_member_id>')
@login_required
def view_family_member(family_member_id):
    """View a specific family member's details"""
    family_member = FamilyMember.query.get_or_404(family_member_id)
    
    # Check if the family member belongs to the current user
    if family_member not in current_user.family_members:
        flash('You do not have permission to view this family member', 'danger')
        return redirect(url_for('records.list_family'))
    
    # Get recent health records for this family member
    recent_records = HealthRecord.query.filter_by(family_member_id=family_member.id)\
                                      .order_by(HealthRecord.date.desc())\
                                      .limit(10).all()
    
    return render_template('records/family_profile.html',
                          title=f'{family_member.first_name} {family_member.last_name}',
                          family_member=family_member,
                          recent_records=recent_records)
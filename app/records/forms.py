"""
Records Forms Module

This module contains all form definitions for the records module.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    DateField,
    FloatField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from ..utils.form_validators import SecurityValidationMixin
from ..utils.shared import detect_suspicious_patterns


class RecordForm(FlaskForm, SecurityValidationMixin):
    """Form for creating and editing health records"""

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


class FamilyMemberForm(FlaskForm, SecurityValidationMixin):
    """Form for creating and editing family members"""

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

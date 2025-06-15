"""
Streamlined forms module with essential fields only.
"""

from datetime import datetime

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
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from ..utils.form_validators import SecurityValidationMixin


class RecordForm(FlaskForm, SecurityValidationMixin):
    """Streamlined health record form"""

    family_member = SelectField("Family Member", coerce=int, validators=[Optional()])
    date = DateField("Date", format="%Y-%m-%d", validators=[DataRequired()])

    # Essential medical fields
    chief_complaint = TextAreaField(
        "Chief Complaint",
        validators=[Optional(), Length(max=2000)],
        render_kw={"rows": 3, "placeholder": "Main reason for visit or health concern"},
    )
    doctor = StringField(
        "Doctor",
        validators=[Optional(), Length(max=200)],
        render_kw={"placeholder": "Doctor's name"},
    )
    investigations = TextAreaField(
        "Investigations",
        validators=[Optional(), Length(max=2000)],
        render_kw={"rows": 3, "placeholder": "Tests, labs, imaging performed"},
    )
    diagnosis = TextAreaField(
        "Diagnosis",
        validators=[Optional(), Length(max=2000)],
        render_kw={"rows": 3, "placeholder": "Medical diagnosis"},
    )
    prescription = TextAreaField(
        "Prescription",
        validators=[Optional(), Length(max=3000)],
        render_kw={"rows": 4, "placeholder": "Medications with dosage"},
    )
    notes = TextAreaField(
        "Notes",
        validators=[Optional(), Length(max=3000)],
        render_kw={"rows": 4, "placeholder": "Additional notes"},
    )
    review_followup = TextAreaField(
        "Review/Follow-up",
        validators=[Optional(), Length(max=1000)],
        render_kw={"rows": 2, "placeholder": "Follow-up instructions or next steps"},
    )

    # Visit details
    appointment_type = SelectField(
        "Type",
        choices=[
            ("", "Select Type"),
            ("consultation", "Consultation"),
            ("follow-up", "Follow-up"),
            ("routine", "Routine Check-up"),
            ("emergency", "Emergency"),
        ],
        validators=[Optional()],
    )
    doctor_specialty = SelectField(
        "Specialty",
        choices=[
            ("", "Select Specialty"),
            ("general", "General Practice"),
            ("cardiology", "Cardiology"),
            ("neurology", "Neurology"),
            ("orthopedics", "Orthopedics"),
            ("dermatology", "Dermatology"),
            ("other", "Other"),
        ],
        validators=[Optional()],
    )
    clinic_hospital = StringField(
        "Clinic/Hospital",
        validators=[Optional(), Length(max=200)],
        render_kw={"placeholder": "Medical facility name"},
    )
    cost = FloatField(
        "Cost",
        validators=[Optional(), NumberRange(min=0)],
        render_kw={"placeholder": "Visit cost"},
    )

    file = FileField(
        "Upload Document",
        validators=[
            Optional(),
            FileAllowed(["pdf", "jpg", "jpeg", "png"], "PDF and image files only"),
        ],
    )
    submit = SubmitField("Save Record")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.populate_family_members()

    def populate_family_members(self):
        from flask_login import current_user

        if current_user.is_authenticated:
            # Use the many-to-many relationship to get family members
            family_members = current_user.family_members
            choices = [("", "Select Family Member")]
            choices.extend(
                [
                    (member.id, f"{member.first_name} {member.last_name}")
                    for member in family_members
                ]
            )
            self.family_member.choices = choices


class FamilyMemberForm(FlaskForm, SecurityValidationMixin):
    """Family member form with medical history"""

    first_name = StringField(
        "First Name", validators=[DataRequired(), Length(min=2, max=50)]
    )
    last_name = StringField(
        "Last Name", validators=[DataRequired(), Length(min=2, max=50)]
    )
    relationship = SelectField(
        "Relationship",
        choices=[
            ("", "Select Relationship"),
            ("self", "Self"),
            ("spouse", "Spouse"),
            ("child", "Child"),
            ("parent", "Parent"),
            ("sibling", "Sibling"),
            ("other", "Other"),
        ],
        validators=[DataRequired()],
    )
    date_of_birth = DateField("Date of Birth", validators=[Optional()])

    # Basic Information
    gender = SelectField(
        "Gender",
        choices=[
            ("", "Select Gender"),
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other"),
        ],
        validators=[Optional()],
    )
    blood_type = SelectField(
        "Blood Type",
        choices=[
            ("", "Select Blood Type"),
            ("A+", "A+"),
            ("A-", "A-"),
            ("B+", "B+"),
            ("B-", "B-"),
            ("AB+", "AB+"),
            ("AB-", "AB-"),
            ("O+", "O+"),
            ("O-", "O-"),
        ],
        validators=[Optional()],
    )

    # Medical History
    allergies = TextAreaField(
        "Known Allergies",
        validators=[Optional(), Length(max=2000)],
        render_kw={
            "rows": 3,
            "placeholder": "Food allergies, drug allergies, environmental allergies",
        },
    )
    chronic_conditions = TextAreaField(
        "Chronic Conditions",
        validators=[Optional(), Length(max=2000)],
        render_kw={"rows": 3, "placeholder": "Diabetes, hypertension, asthma, etc."},
    )
    current_medications = TextAreaField(
        "Current Medications",
        validators=[Optional(), Length(max=2000)],
        render_kw={"rows": 3, "placeholder": "Current prescriptions and dosages"},
    )
    family_medical_history = TextAreaField(
        "Family Medical History",
        validators=[Optional(), Length(max=3000)],
        render_kw={
            "rows": 4,
            "placeholder": "Hereditary conditions, family history of diseases",
        },
    )
    surgical_history = TextAreaField(
        "Surgical History",
        validators=[Optional(), Length(max=2000)],
        render_kw={"rows": 3, "placeholder": "Previous surgeries and procedures"},
    )

    # Emergency Contact
    emergency_contact_name = StringField(
        "Emergency Contact Name",
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "Emergency contact person"},
    )
    emergency_contact_phone = StringField(
        "Emergency Contact Phone",
        validators=[Optional(), Length(max=20)],
        render_kw={"placeholder": "Emergency contact phone number"},
    )

    # Healthcare Information
    primary_doctor = StringField(
        "Primary Doctor",
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "Primary care physician"},
    )
    insurance_provider = StringField(
        "Insurance Provider",
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "Health insurance company"},
    )

    notes = TextAreaField(
        "Additional Notes",
        validators=[Optional(), Length(max=3000)],
        render_kw={"rows": 4, "placeholder": "Any additional medical information"},
    )

    submit = SubmitField("Save Family Member")


class MedicalConditionForm(FlaskForm, SecurityValidationMixin):
    """Medical condition form"""

    family_member = SelectField("Family Member", coerce=int, validators=[Optional()])
    condition_name = StringField(
        "Condition",
        validators=[DataRequired(), Length(min=2, max=200)],
        render_kw={"placeholder": "e.g., Diabetes, Hypertension"},
    )
    diagnosis_date = DateField("Diagnosis Date", validators=[Optional()])
    condition_type = SelectField(
        "Type",
        choices=[
            ("", "Select Type"),
            ("chronic", "Chronic"),
            ("acute", "Acute"),
            ("hereditary", "Hereditary"),
            ("infectious", "Infectious"),
        ],
        validators=[Optional()],
    )
    severity = SelectField(
        "Severity",
        choices=[
            ("", "Select Severity"),
            ("mild", "Mild"),
            ("moderate", "Moderate"),
            ("severe", "Severe"),
        ],
        validators=[Optional()],
    )
    current_status = SelectField(
        "Status",
        choices=[
            ("active", "Active"),
            ("managed", "Managed"),
            ("resolved", "Resolved"),
            ("monitoring", "Monitoring"),
        ],
        validators=[DataRequired()],
    )
    description = TextAreaField(
        "Description",
        validators=[Optional(), Length(max=2000)],
        render_kw={"rows": 4, "placeholder": "Condition details and symptoms"},
    )
    submit = SubmitField("Save Condition")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.populate_family_members()

    def populate_family_members(self):
        from flask_login import current_user

        if current_user.is_authenticated:
            # Use the many-to-many relationship to get family members
            family_members = current_user.family_members
            choices = [("", "Select Family Member")]
            choices.extend(
                [
                    (member.id, f"{member.first_name} {member.last_name}")
                    for member in family_members
                ]
            )
            self.family_member.choices = choices


class ConditionProgressForm(FlaskForm, SecurityValidationMixin):
    """Progress note form"""

    note_date = DateField("Date", validators=[DataRequired()], default=datetime.today)
    symptoms = TextAreaField(
        "Symptoms",
        validators=[Optional(), Length(max=2000)],
        render_kw={"rows": 3, "placeholder": "Current symptoms"},
    )
    medications = TextAreaField(
        "Medications",
        validators=[Optional(), Length(max=1500)],
        render_kw={"rows": 3, "placeholder": "Current medications"},
    )
    notes = TextAreaField(
        "Notes",
        validators=[Optional(), Length(max=2000)],
        render_kw={"rows": 4, "placeholder": "Progress notes and observations"},
    )
    submit = SubmitField("Save Progress Note")

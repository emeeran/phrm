"""
Records Forms Module

This module contains all form definitions for the records module.
"""

from datetime import datetime

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    DateField,
    DateTimeField,
    FloatField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)

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

    # Enhanced doctor visit tracking fields
    appointment_type = SelectField(
        "Appointment Type",
        choices=[
            ("", "Select Type"),
            ("consultation", "Initial Consultation"),
            ("follow-up", "Follow-up Visit"),
            ("routine", "Routine Check-up"),
            ("emergency", "Emergency Visit"),
            ("procedure", "Medical Procedure"),
            ("diagnostic", "Diagnostic Tests"),
        ],
        validators=[Optional()],
    )
    doctor_specialty = SelectField(
        "Doctor Specialty",
        choices=[
            ("", "Select Specialty"),
            ("general", "General Practice"),
            ("cardiology", "Cardiology"),
            ("neurology", "Neurology"),
            ("orthopedics", "Orthopedics"),
            ("dermatology", "Dermatology"),
            ("psychiatry", "Psychiatry"),
            ("pediatrics", "Pediatrics"),
            ("gynecology", "Gynecology"),
            ("oncology", "Oncology"),
            ("endocrinology", "Endocrinology"),
            ("gastroenterology", "Gastroenterology"),
            ("ophthalmology", "Ophthalmology"),
            ("other", "Other"),
        ],
        validators=[Optional()],
    )
    clinic_hospital = StringField(
        "Clinic/Hospital",
        validators=[Optional(), Length(max=200)],
        render_kw={"placeholder": "Name of clinic, hospital, or medical facility"},
    )
    visit_duration = IntegerField(
        "Visit Duration (minutes)",
        validators=[Optional(), NumberRange(min=1, max=480)],
        render_kw={"placeholder": "Duration in minutes"},
    )
    cost = FloatField(
        "Cost",
        validators=[Optional(), NumberRange(min=0)],
        render_kw={"placeholder": "Visit cost if applicable"},
    )

    # Medical condition tracking
    current_symptoms = TextAreaField(
        "Current Symptoms",
        validators=[Optional(), Length(max=2000)],
        render_kw={"rows": 3, "placeholder": "Active symptoms at time of visit"},
    )
    vital_signs = TextAreaField(
        "Vital Signs",
        validators=[Optional(), Length(max=1000)],
        render_kw={
            "rows": 2,
            "placeholder": "Blood pressure, heart rate, temperature, etc.",
        },
    )
    medical_urgency = SelectField(
        "Medical Urgency",
        choices=[
            ("routine", "Routine"),
            ("urgent", "Urgent"),
            ("emergency", "Emergency"),
        ],
        default="routine",
        validators=[Optional()],
    )

    # Treatment and prognosis
    treatment_plan = TextAreaField(
        "Treatment Plan",
        validators=[Optional(), Length(max=3000)],
        render_kw={
            "rows": 4,
            "placeholder": "Detailed treatment plan and recommendations",
        },
    )
    medication_changes = TextAreaField(
        "Medication Changes",
        validators=[Optional(), Length(max=2000)],
        render_kw={
            "rows": 3,
            "placeholder": "Changes to medications, new prescriptions, discontinued drugs",
        },
    )
    prognosis = TextAreaField(
        "Prognosis",
        validators=[Optional(), Length(max=2000)],
        render_kw={
            "rows": 3,
            "placeholder": "Doctor's prognosis and expected outcomes",
        },
    )
    next_appointment = DateTimeField(
        "Next Appointment",
        validators=[Optional()],
        format="%Y-%m-%dT%H:%M",
        render_kw={"type": "datetime-local"},
    )

    # Condition progression
    condition_status = SelectField(
        "Condition Status",
        choices=[
            ("", "Select Status"),
            ("improving", "Improving"),
            ("stable", "Stable"),
            ("worsening", "Worsening"),
            ("resolved", "Resolved"),
            ("new", "New Condition"),
        ],
        validators=[Optional()],
    )
    pain_scale = IntegerField(
        "Pain Scale (1-10)",
        validators=[Optional(), NumberRange(min=1, max=10)],
        render_kw={"placeholder": "Rate pain from 1 (minimal) to 10 (severe)"},
    )
    functional_status = TextAreaField(
        "Functional Status",
        validators=[Optional(), Length(max=1000)],
        render_kw={
            "rows": 2,
            "placeholder": "How condition affects daily activities and quality of life",
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


class MedicalConditionForm(FlaskForm, SecurityValidationMixin):
    """Form for managing ongoing medical conditions"""

    family_member = SelectField("Family Member", coerce=int, validators=[Optional()])

    # Condition Details
    condition_name = StringField(
        "Condition Name",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "Name of the medical condition or diagnosis"},
    )
    condition_category = SelectField(
        "Condition Category",
        choices=[
            ("", "Select Category"),
            ("chronic", "Chronic Condition"),
            ("acute", "Acute Condition"),
            ("genetic", "Genetic Condition"),
            ("autoimmune", "Autoimmune Condition"),
            ("infectious", "Infectious Disease"),
            ("mental_health", "Mental Health"),
            ("cancer", "Cancer/Oncology"),
            ("cardiovascular", "Cardiovascular"),
            ("neurological", "Neurological"),
            ("respiratory", "Respiratory"),
            ("endocrine", "Endocrine/Hormonal"),
            ("musculoskeletal", "Musculoskeletal"),
            ("gastrointestinal", "Gastrointestinal"),
            ("other", "Other"),
        ],
        validators=[Optional()],
    )
    icd_code = StringField(
        "ICD-10 Code",
        validators=[Optional(), Length(max=20)],
        render_kw={"placeholder": "ICD-10 diagnosis code if known"},
    )
    diagnosed_date = DateField(
        "Date Diagnosed", validators=[Optional()], format="%Y-%m-%d"
    )
    diagnosing_doctor = StringField(
        "Diagnosing Doctor",
        validators=[Optional(), Length(max=200)],
        render_kw={"placeholder": "Doctor who made the diagnosis"},
    )

    # Current Status
    current_status = SelectField(
        "Current Status",
        choices=[
            ("active", "Active"),
            ("resolved", "Resolved"),
            ("managed", "Well Managed"),
            ("monitoring", "Under Monitoring"),
            ("recurrent", "Recurrent"),
        ],
        default="active",
        validators=[DataRequired()],
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

    # Treatment Information
    current_treatments = TextAreaField(
        "Current Treatments",
        validators=[Optional(), Length(max=3000)],
        render_kw={
            "rows": 4,
            "placeholder": "Current medications, therapies, and treatments",
        },
    )
    treatment_goals = TextAreaField(
        "Treatment Goals",
        validators=[Optional(), Length(max=2000)],
        render_kw={
            "rows": 3,
            "placeholder": "Goals and objectives of current treatment plan",
        },
    )
    treatment_effectiveness = SelectField(
        "Treatment Effectiveness",
        choices=[
            ("", "Select Effectiveness"),
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
            ("unknown", "Unknown/Too Early"),
        ],
        validators=[Optional()],
    )

    # Prognosis and Monitoring
    prognosis = TextAreaField(
        "Prognosis",
        validators=[Optional(), Length(max=2000)],
        render_kw={
            "rows": 3,
            "placeholder": "Long-term outlook and expected progression",
        },
    )
    monitoring_plan = TextAreaField(
        "Monitoring Plan",
        validators=[Optional(), Length(max=2000)],
        render_kw={
            "rows": 3,
            "placeholder": "How condition is monitored (tests, frequency, symptoms to watch)",
        },
    )
    next_review_date = DateField(
        "Next Review Date", validators=[Optional()], format="%Y-%m-%d"
    )

    # Impact Assessment
    quality_of_life_impact = SelectField(
        "Quality of Life Impact",
        choices=[
            ("", "Select Impact"),
            ("minimal", "Minimal"),
            ("moderate", "Moderate"),
            ("significant", "Significant"),
            ("severe", "Severe"),
        ],
        validators=[Optional()],
    )
    functional_limitations = TextAreaField(
        "Functional Limitations",
        validators=[Optional(), Length(max=2000)],
        render_kw={
            "rows": 3,
            "placeholder": "How condition affects daily activities and functioning",
        },
    )
    work_impact = SelectField(
        "Work/School Impact",
        choices=[
            ("", "Select Impact"),
            ("none", "No Impact"),
            ("minimal", "Minimal Impact"),
            ("moderate", "Moderate Impact"),
            ("significant", "Significant Impact"),
            ("unable", "Unable to Work/Study"),
        ],
        validators=[Optional()],
    )

    # Additional Information
    notes = TextAreaField(
        "Additional Notes",
        validators=[Optional(), Length(max=3000)],
        render_kw={
            "rows": 4,
            "placeholder": "Additional notes, observations, or important information",
        },
    )
    external_resources = TextAreaField(
        "External Resources",
        validators=[Optional(), Length(max=1000)],
        render_kw={
            "rows": 2,
            "placeholder": "Links to patient education materials, support groups, etc.",
        },
    )

    submit = SubmitField("Save Condition")


class ConditionProgressForm(FlaskForm, SecurityValidationMixin):
    """Form for recording condition progress notes"""

    condition_id = SelectField(
        "Medical Condition", coerce=int, validators=[DataRequired()]
    )

    note_date = DateField(
        "Note Date",
        validators=[DataRequired()],
        format="%Y-%m-%d",
        default=lambda: datetime.now().date(),
    )

    progress_status = SelectField(
        "Progress Status",
        choices=[
            ("improving", "Improving"),
            ("stable", "Stable"),
            ("worsening", "Worsening"),
            ("complication", "Complication/Setback"),
            ("resolved", "Resolved"),
        ],
        validators=[DataRequired()],
    )

    symptoms_changes = TextAreaField(
        "Symptoms Changes",
        validators=[Optional(), Length(max=2000)],
        render_kw={"rows": 3, "placeholder": "Changes in symptoms since last note"},
    )

    treatment_changes = TextAreaField(
        "Treatment Changes",
        validators=[Optional(), Length(max=2000)],
        render_kw={
            "rows": 3,
            "placeholder": "Changes to treatment plan, medications, therapies",
        },
    )

    pain_level = IntegerField(
        "Pain Level (1-10)",
        validators=[Optional(), NumberRange(min=1, max=10)],
        render_kw={"placeholder": "Rate current pain level"},
    )

    functional_score = IntegerField(
        "Functional Score (1-10)",
        validators=[Optional(), NumberRange(min=1, max=10)],
        render_kw={"placeholder": "Rate current functional ability"},
    )

    vital_measurements = TextAreaField(
        "Vital Measurements",
        validators=[Optional(), Length(max=1000)],
        render_kw={
            "rows": 2,
            "placeholder": "Blood pressure, weight, temperature, relevant lab values",
        },
    )

    clinical_observations = TextAreaField(
        "Clinical Observations",
        validators=[Optional(), Length(max=2000)],
        render_kw={"rows": 3, "placeholder": "Objective clinical observations"},
    )

    doctor_notes = TextAreaField(
        "Doctor's Notes",
        validators=[Optional(), Length(max=2000)],
        render_kw={
            "rows": 3,
            "placeholder": "Healthcare provider's assessment and notes",
        },
    )

    patient_reported_outcomes = TextAreaField(
        "Patient Reported Outcomes",
        validators=[Optional(), Length(max=2000)],
        render_kw={
            "rows": 3,
            "placeholder": "Patient's own assessment of symptoms and quality of life",
        },
    )

    recorded_by = SelectField(
        "Recorded By",
        choices=[
            ("patient", "Patient/Self"),
            ("doctor", "Doctor"),
            ("nurse", "Nurse"),
            ("caregiver", "Caregiver"),
            ("other", "Other"),
        ],
        default="patient",
        validators=[DataRequired()],
    )

    submit = SubmitField("Save Progress Note")

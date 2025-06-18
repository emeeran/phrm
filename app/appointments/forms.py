"""
Forms for the appointments module.
"""

from datetime import datetime, time

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    TimeField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from ..utils.form_validators import SecurityValidationMixin


class AppointmentForm(FlaskForm, SecurityValidationMixin):
    """Form for creating and editing appointments"""

    # Basic appointment details
    title = StringField(
        "Appointment Title*",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "Brief description of the appointment"},
    )
    doctor_name = StringField(
        "Doctor Name*",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "Full name of the doctor"},
    )
    doctor_specialty = StringField(
        "Doctor Specialty",
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "e.g., Cardiologist, Pediatrician"},
    )
    clinic_hospital = StringField(
        "Clinic/Hospital",
        validators=[Optional(), Length(max=200)],
        render_kw={"placeholder": "Name of the medical facility"},
    )

    # Date and time
    appointment_date = DateField(
        "Date*",
        validators=[DataRequired()],
        default=datetime.utcnow().date,
        render_kw={"placeholder": "Appointment date"},
    )
    appointment_time = TimeField(
        "Time*",
        validators=[DataRequired()],
        default=time(9, 0),  # Default to 9:00 AM
        render_kw={"placeholder": "Appointment time"},
    )
    duration_minutes = IntegerField(
        "Duration (minutes)",
        validators=[Optional(), NumberRange(min=5, max=480)],
        default=30,
        render_kw={"placeholder": "Duration in minutes"},
    )

    # Status
    status = SelectField(
        "Status",
        choices=[
            ("scheduled", "Scheduled"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
            ("rescheduled", "Rescheduled"),
        ],
        default="scheduled",
    )

    # Additional information
    purpose = TextAreaField(
        "Purpose of Visit",
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "Reason for the appointment", "rows": 3},
    )
    preparation = TextAreaField(
        "Pre-appointment Instructions",
        validators=[Optional(), Length(max=500)],
        render_kw={
            "placeholder": "Any preparation needed before the appointment",
            "rows": 3,
        },
    )
    notes = TextAreaField(
        "Additional Notes",
        validators=[Optional(), Length(max=1000)],
        render_kw={
            "placeholder": "Any other information about this appointment",
            "rows": 3,
        },
    )

    # Follow-up
    follow_up_needed = BooleanField("Follow-up Appointment Needed", default=False)

    # Person for the appointment (user or family member)
    person_type = SelectField(
        "Appointment For",
        choices=[("self", "Myself"), ("family", "Family Member")],
        default="self",
    )
    family_member_id = SelectField(
        "Family Member",
        validators=[Optional()],
        coerce=int,
        render_kw={"placeholder": "Select family member"},
    )

    # Reminder
    set_reminder = BooleanField("Set Reminder", default=True)

    # Submit button
    submit = SubmitField("Save Appointment")

    def __init__(self, *args, **kwargs):
        """Initialize the form with family members"""
        family_members = kwargs.pop("family_members", [])
        super().__init__(*args, **kwargs)

        # Set family member choices
        self.family_member_id.choices = [(0, "-- Select Family Member --")] + [
            (fm.id, f"{fm.first_name} {fm.last_name}") for fm in family_members
        ]

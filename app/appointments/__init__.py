"""
Appointments blueprint for managing doctor appointments.
"""

from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..models import db
from ..models.core.appointment import Appointment
from ..models.core.user import FamilyMember
from .forms import AppointmentForm

appointments_bp = Blueprint("appointments", __name__, url_prefix="/appointments")


@appointments_bp.route("/")
@login_required
def list_appointments():
    """List all appointments"""
    # Get selected family member from query params
    member_id = request.args.get("member_id", "all")

    # Load family members for dropdown selector
    family_members = current_user.family_members

    # Set selected member
    selected_member = None

    if member_id != "all" and member_id != "self" and member_id.isdigit():
        # Find the selected family member
        selected_member = FamilyMember.query.filter_by(id=int(member_id)).first_or_404()

        # Make sure the family member belongs to the current user
        if selected_member not in current_user.family_members:
            flash(
                "You don't have access to this family member's appointments.", "danger"
            )
            return redirect(url_for("appointments.list_appointments"))

    # Query appointments
    query = Appointment.query

    # Filter by status if provided
    status = request.args.get("status", "all")
    if status != "all":
        query = query.filter_by(status=status)

    # Filter by time period if provided
    period = request.args.get("period", "upcoming")
    if period == "upcoming":
        query = query.filter(Appointment.appointment_date >= datetime.utcnow())
    elif period == "past":
        query = query.filter(Appointment.appointment_date < datetime.utcnow())
    elif period == "today":
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        query = query.filter(
            Appointment.appointment_date >= today,
            Appointment.appointment_date < tomorrow,
        )
    elif period == "week":
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        next_week = today + timedelta(days=7)
        query = query.filter(
            Appointment.appointment_date >= today,
            Appointment.appointment_date < next_week,
        )

    # Filter by member if selected
    if member_id == "self":
        query = query.filter_by(user_id=current_user.id, family_member_id=None)
    elif selected_member:
        query = query.filter_by(family_member_id=selected_member.id)
    else:
        # Either "all" or invalid member_id, show all appointments
        query = query.filter(
            (Appointment.user_id == current_user.id)
            | (Appointment.family_member_id.in_([m.id for m in family_members]))
        )

    # Sort results
    query = query.order_by(Appointment.appointment_date.asc())

    # Get appointments
    appointments = query.all()

    return render_template(
        "appointments/list.html",
        appointments=appointments,
        family_members=family_members,
        selected_member=selected_member,
        status_filter=status,
        period_filter=period,
        member_id=member_id,
    )


@appointments_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_appointment():
    """Add a new appointment"""
    # Get family members for the dropdown
    family_members = current_user.family_members

    # Create form instance with family members
    form = AppointmentForm(family_members=family_members)

    # Handle form submission
    if form.validate_on_submit():
        # Create new appointment
        appointment = Appointment()

        # Set user_id or family_member_id based on selection
        if form.person_type.data == "self":
            appointment.user_id = current_user.id
            appointment.family_member_id = None
        else:
            appointment.user_id = None
            appointment.family_member_id = form.family_member_id.data

        # Set basic appointment details
        appointment.title = form.title.data
        appointment.doctor_name = form.doctor_name.data
        appointment.doctor_specialty = form.doctor_specialty.data
        appointment.clinic_hospital = form.clinic_hospital.data

        # Combine date and time for appointment_date
        appointment_date = form.appointment_date.data
        appointment_time = form.appointment_time.data
        appointment.appointment_date = datetime.combine(
            appointment_date, appointment_time
        )

        # Set other appointment details
        appointment.duration_minutes = form.duration_minutes.data
        appointment.status = form.status.data
        appointment.purpose = form.purpose.data
        appointment.preparation = form.preparation.data
        appointment.notes = form.notes.data
        appointment.follow_up_needed = form.follow_up_needed.data

        # Add to database
        db.session.add(appointment)
        db.session.commit()

        flash("Appointment created successfully.", "success")
        return redirect(
            url_for("appointments.view_appointment", appointment_id=appointment.id)
        )

    return render_template("appointments/add.html", form=form)


@appointments_bp.route("/<int:appointment_id>")
@login_required
def view_appointment(appointment_id):
    """View appointment details"""
    appointment = Appointment.query.get_or_404(appointment_id)

    # Security check - make sure the appointment belongs to the current user
    if appointment.user_id != current_user.id:
        # Check if it belongs to one of the user's family members
        family_member_ids = [member.id for member in current_user.family_members]
        if appointment.family_member_id not in family_member_ids:
            flash("You don't have access to this appointment.", "danger")
            return redirect(url_for("appointments.list_appointments"))

    return render_template("appointments/view.html", appointment=appointment)


@appointments_bp.route("/<int:appointment_id>/edit", methods=["GET", "POST"])
@login_required
def edit_appointment(appointment_id):
    """Edit an existing appointment"""
    # Get the appointment
    appointment = Appointment.query.get_or_404(appointment_id)

    # Security check - make sure the appointment belongs to the current user
    if appointment.user_id != current_user.id:
        # Check if it belongs to one of the user's family members
        family_member_ids = [member.id for member in current_user.family_members]
        if appointment.family_member_id not in family_member_ids:
            flash("You don't have access to this appointment.", "danger")
            return redirect(url_for("appointments.list_appointments"))

    # Get family members for the dropdown
    family_members = current_user.family_members

    # Create form instance with family members
    form = AppointmentForm(family_members=family_members, obj=appointment)

    # Set person_type based on current appointment
    if appointment.user_id:
        form.person_type.data = "self"
    else:
        form.person_type.data = "family"

    # Split datetime into date and time for form fields
    if request.method == "GET":
        if appointment.appointment_date:
            form.appointment_date.data = appointment.appointment_date.date()
            form.appointment_time.data = appointment.appointment_date.time()

    # Handle form submission
    if form.validate_on_submit():
        # Set user_id or family_member_id based on selection
        if form.person_type.data == "self":
            appointment.user_id = current_user.id
            appointment.family_member_id = None
        else:
            appointment.user_id = None
            appointment.family_member_id = form.family_member_id.data

        # Set basic appointment details
        appointment.title = form.title.data
        appointment.doctor_name = form.doctor_name.data
        appointment.doctor_specialty = form.doctor_specialty.data
        appointment.clinic_hospital = form.clinic_hospital.data

        # Combine date and time for appointment_date
        appointment_date = form.appointment_date.data
        appointment_time = form.appointment_time.data
        appointment.appointment_date = datetime.combine(
            appointment_date, appointment_time
        )

        # Set other appointment details
        appointment.duration_minutes = form.duration_minutes.data
        appointment.status = form.status.data
        appointment.purpose = form.purpose.data
        appointment.preparation = form.preparation.data
        appointment.notes = form.notes.data
        appointment.follow_up_needed = form.follow_up_needed.data

        # Update database
        db.session.commit()

        flash("Appointment updated successfully.", "success")
        return redirect(
            url_for("appointments.view_appointment", appointment_id=appointment.id)
        )

    return render_template("appointments/add.html", form=form, appointment=appointment)


@appointments_bp.route("/<int:appointment_id>/delete", methods=["POST"])
@login_required
def delete_appointment(appointment_id):
    """Delete an appointment"""
    appointment = Appointment.query.get_or_404(appointment_id)

    # Security check - make sure the appointment belongs to the current user
    if appointment.user_id != current_user.id:
        # Check if it belongs to one of the user's family members
        family_member_ids = [member.id for member in current_user.family_members]
        if appointment.family_member_id not in family_member_ids:
            flash("You don't have access to this appointment.", "danger")
            return redirect(url_for("appointments.list_appointments"))

    db.session.delete(appointment)
    db.session.commit()

    flash("Appointment deleted successfully.", "success")
    return redirect(url_for("appointments.list_appointments"))


@appointments_bp.route("/<int:appointment_id>/status", methods=["POST"])
@login_required
def update_status(appointment_id):
    """Update appointment status"""
    appointment = Appointment.query.get_or_404(appointment_id)

    # Security check - make sure the appointment belongs to the current user
    if appointment.user_id != current_user.id:
        # Check if it belongs to one of the user's family members
        family_member_ids = [member.id for member in current_user.family_members]
        if appointment.family_member_id not in family_member_ids:
            flash("You don't have access to this appointment.", "danger")
            return redirect(url_for("appointments.list_appointments"))

    # Get new status from form
    new_status = request.form.get("status")
    if new_status in ["scheduled", "completed", "cancelled", "rescheduled"]:
        appointment.status = new_status
        db.session.commit()
        flash(f"Appointment status updated to {new_status}.", "success")
    else:
        flash("Invalid appointment status.", "danger")

    return redirect(
        url_for("appointments.view_appointment", appointment_id=appointment.id)
    )

"""
Medications blueprint for managing current medications and checking interactions.
"""

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..models import db
from ..models.core.current_medication import CurrentMedication
from ..models.core.family_member import FamilyMember
from ..utils.medicine_interaction import MedicineInteractionChecker

medications_bp = Blueprint("medications", __name__, url_prefix="/medications")


@medications_bp.route("/")
@login_required
def list_medications():
    """List all medications for a family member"""
    # Get member_id from query params
    member_id = request.args.get("member_id")

    # Load family members for dropdown selector
    family_members = current_user.family_members

    # Set selected member
    selected_member = None

    if member_id and member_id != "self" and member_id.isdigit():
        # Find the selected family member
        selected_member = FamilyMember.query.filter_by(id=int(member_id)).first_or_404()

        # Make sure the family member belongs to the current user
        if selected_member not in current_user.family_members:
            flash(
                "You don't have access to this family member's medications.", "danger"
            )
            return redirect(url_for("medications.list_medications"))

        # Get medications for this family member
        medications = CurrentMedication.query.filter_by(
            family_member_id=selected_member.id
        ).all()
    else:
        # Currently we only support medications for family members, not the user
        medications = []

        if member_id == "self":
            flash(
                "Personal medications are currently not supported. Please select a family member.",
                "info",
            )

    return render_template(
        "medications/list.html",
        medications=medications,
        family_members=family_members,
        selected_member=selected_member,
    )


@medications_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_medication():
    """Add a new medication"""
    # Get member_id from query params
    member_id = request.args.get("member_id")

    # This will be implemented in a separate file or as part of the forms module
    return render_template("medications/add.html", member_id=member_id)


@medications_bp.route("/<int:medication_id>")
@login_required
def view_medication(medication_id):
    """View medication details"""
    medication = CurrentMedication.query.get_or_404(medication_id)

    # Security check - make sure the medication belongs to one of the user's family members
    family_member_ids = [member.id for member in current_user.family_members]
    if medication.family_member_id not in family_member_ids:
        flash("You don't have access to this medication.", "danger")
        return redirect(url_for("medications.list_medications"))

    return render_template("medications/view.html", medication=medication)


@medications_bp.route("/<int:medication_id>/edit", methods=["GET", "POST"])
@login_required
def edit_medication(medication_id):
    """Edit an existing medication"""
    # This will be implemented in a separate file or as part of the forms module
    return render_template("medications/edit.html")


@medications_bp.route("/<int:medication_id>/delete", methods=["POST"])
@login_required
def delete_medication(medication_id):
    """Delete a medication"""
    medication = CurrentMedication.query.get_or_404(medication_id)

    # Security check - make sure the medication belongs to one of the user's family members
    family_member_ids = [member.id for member in current_user.family_members]
    if medication.family_member_id not in family_member_ids:
        flash("You don't have access to this medication.", "danger")
        return redirect(url_for("medications.list_medications"))

    family_member_id = medication.family_member_id

    db.session.delete(medication)
    db.session.commit()

    flash("Medication deleted successfully.", "success")
    return redirect(url_for("medications.list_medications", member_id=family_member_id))


@medications_bp.route("/interactions")
@login_required
def interactions():
    """Check for medicine interactions"""
    # Get member_id from query params
    member_id = request.args.get("member_id")

    # Load family members for dropdown selector
    family_members = current_user.family_members

    # Set selected member
    selected_member = None
    interactions = []
    medications = []

    if member_id and member_id != "self" and member_id.isdigit():
        # Find the selected family member
        selected_member = FamilyMember.query.filter_by(id=int(member_id)).first_or_404()

        # Make sure the family member belongs to the current user
        if selected_member not in current_user.family_members:
            flash(
                "You don't have access to this family member's medications.", "danger"
            )
            return redirect(url_for("medications.interactions"))

        # Get medications for this family member
        medications = CurrentMedication.query.filter_by(
            family_member_id=selected_member.id
        ).all()

        # Check for interactions
        if len(medications) >= 2:
            interaction_checker = MedicineInteractionChecker()
            interactions = interaction_checker.check_interactions(selected_member.id)

    return render_template(
        "medications/interactions.html",
        family_members=family_members,
        selected_member=selected_member,
        medications=medications,
        interactions=interactions,
    )


@medications_bp.route("/check-interaction", methods=["POST"])
@login_required
def check_specific_interaction():
    """Check for interaction between specific medicines"""
    # Get medicines from request
    medicine1 = request.form.get("medicine1", "").strip()
    medicine2 = request.form.get("medicine2", "").strip()

    if not medicine1 or not medicine2:
        return jsonify({"error": "Please enter two medications to check"}), 400

    # Check for interaction
    interaction_checker = MedicineInteractionChecker()
    interaction = interaction_checker._check_pair(medicine1.lower(), medicine2.lower())

    if interaction:
        return jsonify(
            {
                "found": True,
                "severity": interaction["severity"],
                "description": interaction["description"],
                "recommendation": interaction["recommendation"],
            }
        )
    else:
        return jsonify(
            {
                "found": False,
                "message": "No known interactions found between these medications.",
            }
        )

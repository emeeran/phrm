"""
Medical Conditions Routes Module

This module contains route handlers for medical condition management,
including CRUD operations and AI-powered analysis.
"""

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from ... import limiter
from ...models import ConditionProgressNote, FamilyMember, MedicalCondition, db
from ...utils.medical_condition_ai import (
    analyze_condition_progression,
    get_condition_insights,
)
from ...utils.performance_monitor import monitor_performance
from ...utils.security_utils import log_security_event, sanitize_html
from ..forms import ConditionProgressForm, MedicalConditionForm

medical_conditions_routes = Blueprint("medical_conditions_routes", __name__)


@medical_conditions_routes.route("/conditions")
@login_required
@monitor_performance
def list_conditions():
    """List all medical conditions for the user and their family"""
    page = request.args.get("page", 1, type=int)
    per_page = 10

    # Get user's conditions
    user_conditions = (
        MedicalCondition.query.filter_by(user_id=current_user.id)
        .order_by(
            MedicalCondition.current_status.asc(), MedicalCondition.condition_name.asc()
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    # Get family member conditions
    family_conditions = []
    for family_member in current_user.family_members:
        conditions = (
            MedicalCondition.query.filter_by(family_member_id=family_member.id)
            .order_by(
                MedicalCondition.current_status.asc(),
                MedicalCondition.condition_name.asc(),
            )
            .all()
        )
        if conditions:
            family_conditions.append(
                {"family_member": family_member, "conditions": conditions}
            )

    return render_template(
        "records/conditions/list.html",
        user_conditions=user_conditions,
        family_conditions=family_conditions,
        title="Medical Conditions",
    )


@medical_conditions_routes.route("/conditions/create", methods=["GET", "POST"])
@login_required
@limiter.limit("5 per minute")
@monitor_performance
def create_condition():
    """Create a new medical condition"""
    form = MedicalConditionForm()

    # Populate family member choices
    family_members = [(0, "Myself")] + [
        (m.id, f"{m.first_name} {m.last_name}") for m in current_user.family_members
    ]
    form.family_member.choices = family_members

    if form.validate_on_submit():
        try:
            # Create new medical condition
            condition = MedicalCondition(
                condition_name=sanitize_html(form.condition_name.data),
                condition_category=form.condition_category.data,
                icd_code=(
                    sanitize_html(form.icd_code.data) if form.icd_code.data else None
                ),
                diagnosed_date=form.diagnosed_date.data,
                diagnosing_doctor=(
                    sanitize_html(form.diagnosing_doctor.data)
                    if form.diagnosing_doctor.data
                    else None
                ),
                current_status=form.current_status.data,
                severity=form.severity.data,
                current_treatments=(
                    sanitize_html(form.current_treatments.data)
                    if form.current_treatments.data
                    else None
                ),
                treatment_goals=(
                    sanitize_html(form.treatment_goals.data)
                    if form.treatment_goals.data
                    else None
                ),
                treatment_effectiveness=form.treatment_effectiveness.data,
                prognosis=(
                    sanitize_html(form.prognosis.data) if form.prognosis.data else None
                ),
                monitoring_plan=(
                    sanitize_html(form.monitoring_plan.data)
                    if form.monitoring_plan.data
                    else None
                ),
                next_review_date=form.next_review_date.data,
                quality_of_life_impact=form.quality_of_life_impact.data,
                functional_limitations=(
                    sanitize_html(form.functional_limitations.data)
                    if form.functional_limitations.data
                    else None
                ),
                work_impact=form.work_impact.data,
                notes=sanitize_html(form.notes.data) if form.notes.data else None,
                external_resources=(
                    sanitize_html(form.external_resources.data)
                    if form.external_resources.data
                    else None
                ),
            )

            # Assign to user or family member
            if form.family_member.data == 0:
                condition.user_id = current_user.id
            else:
                # Verify family member belongs to current user
                family_member = FamilyMember.query.get(form.family_member.data)
                if family_member and family_member in current_user.family_members:
                    condition.family_member_id = family_member.id
                else:
                    log_security_event(
                        "invalid_family_member_assignment",
                        {
                            "user_id": current_user.id,
                            "attempted_family_member_id": form.family_member.data,
                        },
                    )
                    flash("Invalid family member selection", "danger")
                    return redirect(
                        url_for("records.medical_conditions_routes.create_condition")
                    )

            db.session.add(condition)
            db.session.commit()

            current_app.logger.info(
                f"User {current_user.id} created medical condition {condition.id}: {condition.condition_name}"
            )

            flash(
                f"Medical condition '{condition.condition_name}' has been added successfully!",
                "success",
            )
            return redirect(
                url_for(
                    "records.medical_conditions_routes.view_condition",
                    condition_id=condition.id,
                )
            )

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating medical condition: {e}")
            flash(
                "An error occurred while saving the condition. Please try again.",
                "danger",
            )

    return render_template(
        "records/conditions/form.html",
        form=form,
        title="Add Medical Condition",
        action="Create",
    )


@medical_conditions_routes.route("/conditions/<int:condition_id>")
@login_required
@monitor_performance
def view_condition(condition_id):
    """View a specific medical condition with its history"""
    condition = MedicalCondition.query.get_or_404(condition_id)

    # Check ownership
    if not _check_condition_access(condition):
        log_security_event(
            "unauthorized_condition_access",
            {"user_id": current_user.id, "condition_id": condition_id},
        )
        flash("You don't have permission to view this condition.", "danger")
        return redirect(url_for("records.medical_conditions_routes.list_conditions"))

    # Get progress notes
    progress_notes = (
        ConditionProgressNote.query.filter_by(condition_id=condition_id)
        .order_by(ConditionProgressNote.note_date.desc())
        .all()
    )

    # Get related health records
    related_records = []
    if hasattr(condition, "health_records"):
        related_records = (
            condition.health_records.order_by(
                condition.health_records.property.mapper.class_.date.desc()
            )
            .limit(10)
            .all()
        )

    return render_template(
        "records/conditions/view.html",
        condition=condition,
        progress_notes=progress_notes,
        related_records=related_records,
        title=f"Condition: {condition.condition_name}",
    )


@medical_conditions_routes.route(
    "/conditions/<int:condition_id>/edit", methods=["GET", "POST"]
)
@login_required
@limiter.limit("3 per minute")
@monitor_performance
def edit_condition(condition_id):
    """Edit an existing medical condition"""
    condition = MedicalCondition.query.get_or_404(condition_id)

    # Check ownership
    if not _check_condition_access(condition):
        log_security_event(
            "unauthorized_condition_edit",
            {"user_id": current_user.id, "condition_id": condition_id},
        )
        flash("You don't have permission to edit this condition.", "danger")
        return redirect(url_for("records.medical_conditions_routes.list_conditions"))

    form = MedicalConditionForm(obj=condition)

    # Populate family member choices
    family_members = [(0, "Myself")] + [
        (m.id, f"{m.first_name} {m.last_name}") for m in current_user.family_members
    ]
    form.family_member.choices = family_members

    # Set current family member selection
    if condition.family_member_id:
        form.family_member.data = condition.family_member_id
    else:
        form.family_member.data = 0

    if form.validate_on_submit():
        try:
            # Update condition fields
            condition.condition_name = sanitize_html(form.condition_name.data)
            condition.condition_category = form.condition_category.data
            condition.icd_code = (
                sanitize_html(form.icd_code.data) if form.icd_code.data else None
            )
            condition.diagnosed_date = form.diagnosed_date.data
            condition.diagnosing_doctor = (
                sanitize_html(form.diagnosing_doctor.data)
                if form.diagnosing_doctor.data
                else None
            )
            condition.current_status = form.current_status.data
            condition.severity = form.severity.data
            condition.current_treatments = (
                sanitize_html(form.current_treatments.data)
                if form.current_treatments.data
                else None
            )
            condition.treatment_goals = (
                sanitize_html(form.treatment_goals.data)
                if form.treatment_goals.data
                else None
            )
            condition.treatment_effectiveness = form.treatment_effectiveness.data
            condition.prognosis = (
                sanitize_html(form.prognosis.data) if form.prognosis.data else None
            )
            condition.monitoring_plan = (
                sanitize_html(form.monitoring_plan.data)
                if form.monitoring_plan.data
                else None
            )
            condition.next_review_date = form.next_review_date.data
            condition.quality_of_life_impact = form.quality_of_life_impact.data
            condition.functional_limitations = (
                sanitize_html(form.functional_limitations.data)
                if form.functional_limitations.data
                else None
            )
            condition.work_impact = form.work_impact.data
            condition.notes = (
                sanitize_html(form.notes.data) if form.notes.data else None
            )
            condition.external_resources = (
                sanitize_html(form.external_resources.data)
                if form.external_resources.data
                else None
            )

            db.session.commit()

            current_app.logger.info(
                f"User {current_user.id} updated medical condition {condition.id}: {condition.condition_name}"
            )

            flash(
                f"Medical condition '{condition.condition_name}' has been updated successfully!",
                "success",
            )
            return redirect(
                url_for(
                    "records.medical_conditions_routes.view_condition",
                    condition_id=condition.id,
                )
            )

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating medical condition: {e}")
            flash(
                "An error occurred while updating the condition. Please try again.",
                "danger",
            )

    return render_template(
        "records/conditions/form.html",
        form=form,
        condition=condition,
        title=f"Edit: {condition.condition_name}",
        action="Update",
    )


@medical_conditions_routes.route(
    "/conditions/<int:condition_id>/progress", methods=["GET", "POST"]
)
@login_required
@limiter.limit("10 per minute")
@monitor_performance
def add_progress_note(condition_id):
    """Add a progress note for a medical condition"""
    condition = MedicalCondition.query.get_or_404(condition_id)

    # Check ownership
    if not _check_condition_access(condition):
        log_security_event(
            "unauthorized_condition_progress",
            {"user_id": current_user.id, "condition_id": condition_id},
        )
        flash(
            "You don't have permission to add progress notes for this condition.",
            "danger",
        )
        return redirect(url_for("records.medical_conditions_routes.list_conditions"))

    form = ConditionProgressForm()
    form.condition_id.choices = [(condition.id, condition.condition_name)]
    form.condition_id.data = condition.id

    if form.validate_on_submit():
        try:
            progress_note = ConditionProgressNote(
                condition_id=condition.id,
                note_date=form.note_date.data,
                progress_status=form.progress_status.data,
                symptoms_changes=(
                    sanitize_html(form.symptoms_changes.data)
                    if form.symptoms_changes.data
                    else None
                ),
                treatment_changes=(
                    sanitize_html(form.treatment_changes.data)
                    if form.treatment_changes.data
                    else None
                ),
                pain_level=form.pain_level.data,
                functional_score=form.functional_score.data,
                vital_measurements=(
                    sanitize_html(form.vital_measurements.data)
                    if form.vital_measurements.data
                    else None
                ),
                clinical_observations=(
                    sanitize_html(form.clinical_observations.data)
                    if form.clinical_observations.data
                    else None
                ),
                doctor_notes=(
                    sanitize_html(form.doctor_notes.data)
                    if form.doctor_notes.data
                    else None
                ),
                patient_reported_outcomes=(
                    sanitize_html(form.patient_reported_outcomes.data)
                    if form.patient_reported_outcomes.data
                    else None
                ),
                recorded_by=form.recorded_by.data,
            )

            db.session.add(progress_note)
            db.session.commit()

            current_app.logger.info(
                f"User {current_user.id} added progress note for condition {condition.id}"
            )

            flash("Progress note has been added successfully!", "success")
            return redirect(
                url_for(
                    "records.medical_conditions_routes.view_condition",
                    condition_id=condition.id,
                )
            )

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding progress note: {e}")
            flash(
                "An error occurred while saving the progress note. Please try again.",
                "danger",
            )

    return render_template(
        "records/conditions/progress_form.html",
        form=form,
        condition=condition,
        title=f"Add Progress Note: {condition.condition_name}",
    )


@medical_conditions_routes.route("/conditions/<int:condition_id>/analyze")
@login_required
@limiter.limit("3 per minute")
@monitor_performance
def analyze_condition(condition_id):
    """Get AI analysis of condition progression"""
    condition = MedicalCondition.query.get_or_404(condition_id)

    # Check ownership
    if not _check_condition_access(condition):
        log_security_event(
            "unauthorized_condition_analysis",
            {"user_id": current_user.id, "condition_id": condition_id},
        )
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        analysis = analyze_condition_progression(condition_id)
        return jsonify(analysis)
    except Exception as e:
        current_app.logger.error(f"Error in condition analysis: {e}")
        return jsonify({"error": "Analysis failed"}), 500


@medical_conditions_routes.route("/conditions/insights")
@login_required
@limiter.limit("2 per minute")
@monitor_performance
def get_insights():
    """Get comprehensive condition insights for user or family member"""
    family_member_id = request.args.get("family_member_id", type=int)

    try:
        insights = get_condition_insights(current_user.id, family_member_id)
        return jsonify(insights)
    except Exception as e:
        current_app.logger.error(f"Error getting condition insights: {e}")
        return jsonify({"error": "Insights generation failed"}), 500


def _check_condition_access(condition: MedicalCondition) -> bool:
    """Check if current user has access to the medical condition"""
    if condition.user_id == current_user.id:
        return True

    if condition.family_member_id:
        family_member = FamilyMember.query.get(condition.family_member_id)
        return family_member and family_member in current_user.family_members

    return False

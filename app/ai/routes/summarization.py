"""
Summarization Routes for AI Module

Contains Flask route handlers for AI-powered health record summarization.
"""

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from ... import limiter
from ...models import AISummary, HealthRecord, db
from ...utils.shared import (
    ai_audit_required,
    ai_security_required,
    log_security_event,
    monitor_performance,
    sanitize_html,
    secure_ai_response_headers,
)
from ..summarization import create_gpt_summary

summarization_bp = Blueprint("summarization", __name__)


@summarization_bp.route("/summarize/<int:record_id>", methods=["GET", "POST"])
@login_required
@limiter.limit("5 per minute")  # Rate limit AI summary generation
@monitor_performance
@ai_security_required("summarize")
@ai_audit_required(operation_type="summarize", data_classification="PHI")
@secure_ai_response_headers()
def summarize_record(record_id: int):
    """Create an AI summary of a health record"""
    try:
        record = HealthRecord.query.get_or_404(record_id)

        # Check if user has permission to view this record
        has_permission = False
        if record.user_id == current_user.id:
            has_permission = True
        elif (
            record.family_member_id
            and record.family_member in current_user.family_members
        ):
            has_permission = True

        if not has_permission:
            log_security_event(
                "unauthorized_ai_summary_attempt",
                {
                    "user_id": current_user.id,
                    "record_id": record_id,
                    "record_owner_id": record.user_id,
                    "record_family_member_id": record.family_member_id,
                },
            )
            flash("You do not have permission to view this record", "danger")
            return redirect(url_for("records.dashboard"))

        # Check if a summary already exists
        existing_summary = AISummary.query.filter_by(
            health_record_id=record.id,
            summary_type="standard",
        ).first()

        if request.method == "POST":
            try:
                summary_text = create_gpt_summary(record)

                if not summary_text:
                    log_security_event(
                        "ai_summary_generation_failed",
                        {"user_id": current_user.id, "record_id": record_id},
                    )
                    flash("Error generating summary. Please try again later.", "danger")
                    return redirect(url_for("records.view_record", record_id=record.id))

                summary_text = sanitize_html(summary_text)

                if existing_summary:
                    existing_summary.summary_text = summary_text
                    db.session.commit()
                else:
                    summary = AISummary(
                        health_record_id=record.id,
                        summary_text=summary_text,
                        summary_type="standard",
                    )
                    db.session.add(summary)
                    db.session.commit()

                log_security_event(
                    "ai_summary_generated",
                    {"user_id": current_user.id, "record_id": record_id},
                )
                flash("Summary generated successfully!", "success")
                return redirect(
                    url_for("ai.summarization.summarize_record", record_id=record.id)
                )
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error generating summary: {e}")
                flash("An error occurred while generating the summary.", "danger")
                return redirect(url_for("records.view_record", record_id=record.id))

        return render_template(
            "ai/summarize.html",
            title="AI Summary",
            record=record,
            existing_summary=existing_summary,
        )

    except Exception as e:
        current_app.logger.error(f"Error in summarize_record: {e}")
        flash("An error occurred while loading the summary page.", "danger")
        return redirect(url_for("records.dashboard"))


@summarization_bp.route("/view_summary/<int:record_id>")
@login_required
@limiter.limit("10 per minute")
@monitor_performance
@ai_security_required("view_summary")
@ai_audit_required(operation_type="view_summary", data_classification="PHI")
@secure_ai_response_headers()
def view_summary(record_id: int):
    """View an existing AI summary of a health record"""
    try:
        record = HealthRecord.query.get_or_404(record_id)

        # Check if user has permission to view this record
        has_permission = False
        if record.user_id == current_user.id:
            has_permission = True
        elif (
            record.family_member_id
            and record.family_member in current_user.family_members
        ):
            has_permission = True

        if not has_permission:
            log_security_event(
                "unauthorized_ai_summary_view_attempt",
                {
                    "user_id": current_user.id,
                    "record_id": record_id,
                    "record_owner_id": record.user_id,
                    "record_family_member_id": record.family_member_id,
                },
            )
            flash("You do not have permission to view this record", "danger")
            return redirect(url_for("records.dashboard"))

        # Get the summary
        summary = AISummary.query.filter_by(
            health_record_id=record.id,
            summary_type="standard",
        ).first()

        if not summary:
            flash("No AI summary exists for this record.", "info")
            return redirect(
                url_for("ai.summarization.summarize_record", record_id=record.id)
            )

        # Log successful summary view
        log_security_event(
            "ai_summary_viewed",
            {
                "user_id": current_user.id,
                "record_id": record_id,
                "summary_id": summary.id,
            },
        )

        return render_template(
            "ai/view_summary.html",
            title="AI Summary",
            record=record,
            summary=summary,
        )

    except Exception as e:
        current_app.logger.error(f"Error in view_summary: {e}")
        flash("An error occurred while loading the summary.", "danger")
        return redirect(url_for("records.dashboard"))

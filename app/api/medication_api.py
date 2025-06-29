"""
API routes for medication interaction checking
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from ..utils.drug_interactions import check_medication_interactions
from ..utils.shared import monitor_performance

# Create a new blueprint for medication API
medication_api_bp = Blueprint("medication_api", __name__, url_prefix="/api/medications")


@medication_api_bp.route("/check-interactions", methods=["POST"])
@login_required
@monitor_performance
def check_interactions():
    """
    Check for drug interactions in the user's current medications
    """
    try:
        data = request.get_json()
        medications = data.get("medications", [])

        if not medications:
            return jsonify({"success": False, "error": "No medications provided"}), 400

        # Check interactions
        results = check_medication_interactions(medications)

        return jsonify({"success": True, "data": results})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@medication_api_bp.route("/current-medications", methods=["GET"])
@login_required
@monitor_performance
def get_current_medications():
    """
    Get current medications for the user and family members
    """
    try:
        # Get family members
        family_members = current_user.family_members

        # Collect current medications
        current_medications = []

        # Only family members have current medications (not the user directly)
        for member in family_members:
            if hasattr(member, "current_medication_entries"):
                for med in member.current_medication_entries:
                    current_medications.append(
                        {
                            "person": f"{member.first_name} {member.last_name}",
                            "person_id": f"family_{member.id}",
                            "medicine": med.medicine,
                            "strength": med.strength,
                            "morning": med.morning,
                            "noon": med.noon,
                            "evening": med.evening,
                            "bedtime": med.bedtime,
                            "duration": med.duration,
                        }
                    )

        return jsonify(
            {
                "success": True,
                "data": {
                    "medications": current_medications,
                    "total_count": len(current_medications),
                    "family_count": len(family_members),
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@medication_api_bp.route("/interaction-summary", methods=["GET"])
@login_required
@monitor_performance
def get_interaction_summary():
    """
    Get a summary of medication interactions for dashboard
    """
    try:
        # Get current medications
        response = get_current_medications()
        if response.status_code != 200:
            return response

        medications_data = response.get_json()["data"]["medications"]

        if not medications_data:
            return jsonify(
                {
                    "success": True,
                    "data": {
                        "has_interactions": False,
                        "summary": {
                            "total_medications": 0,
                            "total_interactions": 0,
                            "high_risk": 0,
                        },
                    },
                }
            )

        # Check interactions
        results = check_medication_interactions(medications_data)

        return jsonify(
            {
                "success": True,
                "data": {
                    "has_interactions": results["summary"]["total_interactions"] > 0,
                    "summary": results["summary"],
                    "high_risk_interactions": [
                        interaction
                        for interaction in results["interactions"]
                        if interaction["severity"] in ["major", "contraindicated"]
                    ][:3],  # Limit to top 3 for dashboard
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

"""
Medical Condition AI Analysis Helpers

Specialized AI functions for analyzing medical conditions, treatment effectiveness,
and providing prognosis insights based on medical history.
"""

import json
from datetime import datetime, timezone
from typing import Any, Optional

from flask import current_app

from ..ai.routes.chat import call_ai_with_fallback
from ..models import (
    ConditionProgressNote,
    FamilyMember,
    HealthRecord,
    MedicalCondition,
    User,
)


def analyze_condition_progression(condition_id: int) -> dict[str, Any]:
    """
    Analyze the progression of a medical condition over time using AI.

    Args:
        condition_id: ID of the medical condition to analyze

    Returns:
        Dictionary containing progression analysis, trends, and recommendations
    """
    try:
        condition = MedicalCondition.query.get(condition_id)
        if not condition:
            return {"error": "Condition not found"}

        # Get recent progress notes
        recent_notes = (
            ConditionProgressNote.query.filter_by(condition_id=condition_id)
            .order_by(ConditionProgressNote.note_date.desc())
            .limit(10)
            .all()
        )

        # Get related health records
        related_records = (
            HealthRecord.query.filter_by(related_condition_id=condition_id)
            .order_by(HealthRecord.date.desc())
            .limit(5)
            .all()
        )

        # Build context for AI analysis
        context = _build_condition_context(condition, recent_notes, related_records)

        # Create specialized prompt for condition analysis
        prompt = f"""
        As a medical AI assistant, please analyze the progression of this medical condition using CMDT-style formatting where appropriate:

        CONDITION OVERVIEW:
        {context["condition_summary"]}

        RECENT PROGRESS NOTES:
        {context["progress_notes"]}

        RELATED HEALTH RECORDS:
        {context["health_records"]}

        Please provide a comprehensive analysis using this structure:

        **CONDITION PROGRESSION ANALYSIS**

        **CURRENT STATUS**
        • Overall progression trend (improving/stable/worsening)
        • Key clinical indicators and changes

        **CLINICAL FINDINGS**
        • Recent symptom patterns
        • Physical examination trends
        • Laboratory or diagnostic changes

        **TREATMENT RESPONSE**
        • Current treatment effectiveness
        • Medication adherence and response
        • Non-pharmacological interventions

        **RECOMMENDATIONS**
        • Monitoring adjustments needed
        • Care plan modifications
        • Lifestyle or treatment changes to consider

        **PROGNOSIS**
        • Short-term outlook based on current trajectory
        • Long-term considerations

        **RED FLAGS**
        • Warning signs requiring immediate attention
        • When to seek urgent medical care

        Focus on providing actionable insights while being appropriately cautious about medical recommendations.
        """

        # Get AI response
        ai_response, model_used = call_ai_with_fallback(
            "You are a medical AI assistant specializing in condition analysis and prognosis assessment.",
            prompt,
        )

        return {
            "analysis": ai_response,
            "condition_name": condition.condition_name,
            "analysis_date": datetime.now(timezone.utc).isoformat(),
            "data_points_analyzed": len(recent_notes) + len(related_records),
        }

    except Exception as e:
        current_app.logger.error(f"Error analyzing condition progression: {e}")
        return {"error": "Analysis failed", "details": str(e)}


def get_condition_insights(
    user_id: int, family_member_id: Optional[int] = None
) -> dict[str, Any]:
    """
    Get AI insights about all medical conditions for a person.

    Args:
        user_id: ID of the user
        family_member_id: Optional family member ID

    Returns:
        Dictionary containing comprehensive condition insights
    """
    try:
        # Get all conditions for the person
        if family_member_id:
            conditions = MedicalCondition.query.filter_by(
                family_member_id=family_member_id
            ).all()
            person = FamilyMember.query.get(family_member_id)
            person_context = person.get_complete_medical_context() if person else ""
        else:
            conditions = MedicalCondition.query.filter_by(user_id=user_id).all()
            user = User.query.get(user_id)
            person_context = user.get_complete_medical_context() if user else ""

        if not conditions:
            return {"message": "No medical conditions found"}

        # Build comprehensive context
        conditions_summary = []
        for condition in conditions:
            condition_data = condition.get_condition_summary()

            # Get recent progress
            recent_progress = (
                ConditionProgressNote.query.filter_by(condition_id=condition.id)
                .order_by(ConditionProgressNote.note_date.desc())
                .limit(3)
                .all()
            )

            condition_data["recent_progress"] = [
                {
                    "date": note.note_date.isoformat(),
                    "status": note.progress_status,
                    "pain_level": note.pain_level,
                    "functional_score": note.functional_score,
                }
                for note in recent_progress
            ]

            conditions_summary.append(condition_data)

        # Create comprehensive analysis prompt
        prompt = f"""
        As a medical AI assistant, please provide comprehensive insights about these medical conditions using CMDT-style formatting:

        PATIENT CONTEXT:
        {person_context}

        CURRENT MEDICAL CONDITIONS:
        {json.dumps(conditions_summary, indent=2)}

        Please provide analysis using this structure:

        **COMPREHENSIVE HEALTH ASSESSMENT**

        **OVERALL HEALTH STATUS**
        • Current health status overview
        • Disease burden assessment
        • Functional status evaluation

        **CONDITION INTERACTIONS**
        • How conditions may affect each other
        • Potential synergistic effects
        • Competing treatment priorities

        **TREATMENT BURDEN ANALYSIS**
        • Current medication load
        • Quality of life impact
        • Treatment complexity assessment

        **MEDICATION REVIEW**
        • Current medications assessment
        • Potential drug interactions
        • Optimization opportunities

        **PREVENTIVE CARE RECOMMENDATIONS**
        • Screening tests needed
        • Immunizations due
        • Monitoring requirements

        **LIFESTYLE MODIFICATIONS**
        • Diet and nutrition recommendations
        • Exercise and activity guidelines
        • Stress management strategies

        **RED FLAGS & MONITORING**
        • Warning signs requiring immediate attention
        • Routine monitoring schedule
        • Emergency action plans

        **LONG-TERM PLANNING**
        • Prognosis considerations
        • Care coordination needs
        • Family planning considerations

        Focus on providing a holistic view of the person's health status and actionable recommendations.
        """

        # Get AI response
        ai_response, model_used = call_ai_with_fallback(
            "You are a medical AI assistant specializing in comprehensive health assessment and condition management.",
            prompt,
        )

        return {
            "insights": ai_response,
            "conditions_count": len(conditions),
            "analysis_date": datetime.now(timezone.utc).isoformat(),
            "conditions_summary": conditions_summary,
        }

    except Exception as e:
        current_app.logger.error(f"Error getting condition insights: {e}")
        return {"error": "Insights generation failed", "details": str(e)}


def get_medication_analysis(condition_id: int) -> dict[str, Any]:
    """
    Analyze medications and treatments for a specific condition.

    Args:
        condition_id: ID of the medical condition

    Returns:
        Dictionary containing medication analysis and recommendations
    """
    try:
        condition = MedicalCondition.query.get(condition_id)
        if not condition:
            return {"error": "Condition not found"}

        # Get recent health records with prescription information
        recent_records = (
            HealthRecord.query.filter_by(related_condition_id=condition_id)
            .filter(HealthRecord.prescription.isnot(None))
            .order_by(HealthRecord.date.desc())
            .limit(10)
            .all()
        )

        # Build medication history
        medication_history = []
        for record in recent_records:
            if record.prescription:
                medication_history.append(
                    {
                        "date": record.date.isoformat(),
                        "prescription": record.prescription,
                        "doctor": record.doctor,
                        "diagnosis": record.diagnosis,
                        "medication_changes": record.medication_changes,
                    }
                )

        prompt = f"""
        As a medical AI assistant, please analyze the medication and treatment history for this condition:

        CONDITION: {condition.condition_name}
        CURRENT TREATMENTS: {condition.current_treatments}
        TREATMENT EFFECTIVENESS: {condition.treatment_effectiveness}

        MEDICATION HISTORY:
        {json.dumps(medication_history, indent=2)}

        Please provide analysis including:
        1. Medication adherence patterns
        2. Treatment effectiveness over time
        3. Potential drug interactions
        4. Side effects to monitor
        5. Alternative treatment options to discuss with doctor
        6. Medication optimization suggestions
        7. Cost-effective alternatives if appropriate
        8. Monitoring requirements for current medications

        Focus on providing educational information and suggestions for discussing with healthcare providers.
        """

        ai_response, model_used = call_ai_with_fallback(
            "You are a medical AI assistant specializing in medication analysis and pharmaceutical guidance.",
            prompt,
        )

        return {
            "analysis": ai_response,
            "condition_name": condition.condition_name,
            "medication_records_analyzed": len(medication_history),
            "analysis_date": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        current_app.logger.error(f"Error analyzing medications: {e}")
        return {"error": "Medication analysis failed", "details": str(e)}


def get_prognosis_assessment(condition_id: int) -> dict[str, Any]:
    """
    Get AI-based prognosis assessment for a medical condition.

    Args:
        condition_id: ID of the medical condition

    Returns:
        Dictionary containing prognosis assessment and recommendations
    """
    try:
        condition = MedicalCondition.query.get(condition_id)
        if not condition:
            return {"error": "Condition not found"}

        # Get comprehensive data for prognosis
        progress_notes = (
            ConditionProgressNote.query.filter_by(condition_id=condition_id)
            .order_by(ConditionProgressNote.note_date.desc())
            .all()
        )

        # Calculate trends
        pain_trends = [note.pain_level for note in progress_notes if note.pain_level]
        functional_trends = [
            note.functional_score for note in progress_notes if note.functional_score
        ]

        prompt = f"""
        As a medical AI assistant, please provide a prognosis assessment for this medical condition:

        CONDITION DETAILS:
        - Name: {condition.condition_name}
        - Category: {condition.condition_category}
        - Current Status: {condition.current_status}
        - Severity: {condition.severity}
        - Diagnosed: {condition.diagnosed_date}
        - Current Prognosis: {condition.prognosis}
        - Quality of Life Impact: {condition.quality_of_life_impact}

        PROGRESS TRACKING:
        - Total Progress Notes: {len(progress_notes)}
        - Pain Level Trends: {pain_trends[-5:] if pain_trends else "No data"}
        - Functional Score Trends: {functional_trends[-5:] if functional_trends else "No data"}

        Please provide:
        1. Short-term prognosis (3-6 months)
        2. Long-term prognosis (1-5 years)
        3. Factors that could influence outcomes
        4. Best-case scenario expectations
        5. Worst-case scenario preparations
        6. Quality of life considerations
        7. Family planning considerations if relevant
        8. Work/disability planning guidance

        Provide realistic, evidence-based assessments while being sensitive to the emotional impact.
        """

        ai_response, model_used = call_ai_with_fallback(
            "You are a medical AI assistant specializing in prognosis assessment and long-term health planning.",
            prompt,
        )

        return {
            "prognosis": ai_response,
            "condition_name": condition.condition_name,
            "assessment_date": datetime.now(timezone.utc).isoformat(),
            "data_points": len(progress_notes),
        }

    except Exception as e:
        current_app.logger.error(f"Error generating prognosis: {e}")
        return {"error": "Prognosis assessment failed", "details": str(e)}


def _build_condition_context(
    condition: MedicalCondition,
    progress_notes: list[ConditionProgressNote],
    health_records: list[HealthRecord],
) -> dict[str, str]:
    """
    Build comprehensive context for AI condition analysis.
    """
    # Condition summary
    condition_summary = f"""
    Condition: {condition.condition_name}
    Category: {condition.condition_category}
    Status: {condition.current_status}
    Severity: {condition.severity}
    Diagnosed: {condition.diagnosed_date}
    Current Treatments: {condition.current_treatments}
    Prognosis: {condition.prognosis}
    Quality of Life Impact: {condition.quality_of_life_impact}
    """

    # Progress notes summary
    progress_summary = ""
    for note in progress_notes:
        progress_summary += f"""
        Date: {note.note_date}
        Status: {note.progress_status}
        Pain Level: {note.pain_level}/10
        Functional Score: {note.functional_score}/10
        Symptoms: {note.symptoms_changes}
        Treatment Changes: {note.treatment_changes}
        ---
        """

    # Health records summary
    records_summary = ""
    for record in health_records:
        records_summary += f"""
        Date: {record.date}
        Doctor: {record.doctor}
        Complaint: {record.chief_complaint}
        Diagnosis: {record.diagnosis}
        Treatment: {record.prescription}
        ---
        """

    return {
        "condition_summary": condition_summary,
        "progress_notes": progress_summary,
        "health_records": records_summary,
    }


def suggest_condition_monitoring(condition_id: int) -> dict[str, Any]:
    """
    Generate AI suggestions for monitoring a medical condition.

    Args:
        condition_id: ID of the medical condition

    Returns:
        Dictionary containing monitoring recommendations
    """
    try:
        condition = MedicalCondition.query.get(condition_id)
        if not condition:
            return {"error": "Condition not found"}

        prompt = f"""
        As a medical AI assistant, please suggest a monitoring plan for this medical condition:

        CONDITION: {condition.condition_name}
        CATEGORY: {condition.condition_category}
        STATUS: {condition.current_status}
        CURRENT MONITORING: {condition.monitoring_plan}

        Please provide recommendations for:
        1. Frequency of medical check-ups
        2. Specific tests or screenings needed
        3. Symptoms to monitor at home
        4. When to seek immediate medical attention
        5. Lifestyle factors to track
        6. Medication monitoring requirements
        7. Self-assessment tools or scales to use
        8. Technology or apps that might help with monitoring

        Focus on practical, actionable monitoring strategies that empower the patient.
        """

        ai_response, model_used = call_ai_with_fallback(
            "You are a medical AI assistant specializing in patient monitoring and self-care guidance.",
            prompt,
        )

        return {
            "monitoring_plan": ai_response,
            "condition_name": condition.condition_name,
            "generated_date": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        current_app.logger.error(f"Error generating monitoring suggestions: {e}")
        return {"error": "Monitoring suggestions failed", "details": str(e)}

"""
Medication Interaction Checker

Provides basic medication interaction checking functionality.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class InteractionResult:
    """Represents a medication interaction"""

    medication1: str
    medication2: str
    severity: str  # "minor", "moderate", "major"
    description: str
    recommendation: str


class MedicationInteractionChecker:
    """Check for potential medication interactions"""

    # Basic interaction database (in production, use comprehensive drug database)
    INTERACTIONS = {
        # Blood thinners
        ("warfarin", "aspirin"): {
            "severity": "major",
            "description": "Increased bleeding risk when combining warfarin with aspirin",
            "recommendation": "Monitor INR closely and watch for bleeding signs",
        },
        ("warfarin", "ibuprofen"): {
            "severity": "major",
            "description": "NSAIDs can increase warfarin's anticoagulant effect",
            "recommendation": "Avoid combination or use with extreme caution",
        },
        # ACE inhibitors
        ("lisinopril", "potassium"): {
            "severity": "moderate",
            "description": "ACE inhibitors can increase potassium levels",
            "recommendation": "Monitor serum potassium levels regularly",
        },
        # Statins
        ("atorvastatin", "grapefruit"): {
            "severity": "moderate",
            "description": "Grapefruit can increase statin levels leading to muscle toxicity",
            "recommendation": "Avoid grapefruit products while on statins",
        },
        # Diabetes medications
        ("metformin", "alcohol"): {
            "severity": "moderate",
            "description": "Alcohol can increase risk of lactic acidosis with metformin",
            "recommendation": "Limit alcohol intake while on metformin",
        },
        # Common antibiotics
        ("ciprofloxacin", "calcium"): {
            "severity": "moderate",
            "description": "Calcium can reduce absorption of ciprofloxacin",
            "recommendation": "Take ciprofloxacin 2 hours before or 6 hours after calcium",
        },
        # Heart medications
        ("digoxin", "furosemide"): {
            "severity": "moderate",
            "description": "Diuretics can increase digoxin toxicity risk via electrolyte changes",
            "recommendation": "Monitor digoxin levels and electrolytes",
        },
    }

    def check_interactions(self, medications: list[str]) -> list[InteractionResult]:
        """
        Check for interactions between medications

        Args:
            medications: List of medication names

        Returns:
            List of interaction results
        """
        interactions = []

        # Normalize medication names
        normalized_meds = [self._normalize_medication_name(med) for med in medications]

        # Check all pairs
        for i, med1 in enumerate(normalized_meds):
            for _j, med2 in enumerate(normalized_meds[i + 1 :], i + 1):
                interaction = self._check_pair(med1, med2)
                if interaction:
                    interactions.append(interaction)

        # Sort by severity
        severity_order = {"major": 0, "moderate": 1, "minor": 2}
        interactions.sort(key=lambda x: severity_order.get(x.severity, 3))

        return interactions

    def _normalize_medication_name(self, medication: str) -> str:
        """Normalize medication name for comparison"""
        # Convert to lowercase and remove common suffixes
        normalized = medication.lower().strip()

        # Remove common dosage forms
        suffixes = ["tablet", "capsule", "mg", "ml", "suspension", "solution"]
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)].strip()

        # Remove numbers and special characters
        import re

        normalized = re.sub(r"[0-9]+", "", normalized).strip()
        normalized = re.sub(r"[^\w\s]", "", normalized).strip()

        return normalized

    def _check_pair(self, med1: str, med2: str) -> Optional[InteractionResult]:
        """Check if two medications interact"""
        # Check both directions
        interaction_data = self.INTERACTIONS.get((med1, med2)) or self.INTERACTIONS.get(
            (med2, med1)
        )

        if interaction_data:
            return InteractionResult(
                medication1=med1,
                medication2=med2,
                severity=interaction_data["severity"],
                description=interaction_data["description"],
                recommendation=interaction_data["recommendation"],
            )

        return None

    def get_interaction_summary(self, medications: list[str]) -> dict:
        """Get a summary of all interactions"""
        interactions = self.check_interactions(medications)

        summary = {
            "total_interactions": len(interactions),
            "major_interactions": len(
                [i for i in interactions if i.severity == "major"]
            ),
            "moderate_interactions": len(
                [i for i in interactions if i.severity == "moderate"]
            ),
            "minor_interactions": len(
                [i for i in interactions if i.severity == "minor"]
            ),
            "interactions": interactions,
            "risk_level": self._assess_risk_level(interactions),
        }

        return summary

    def _assess_risk_level(self, interactions: list[InteractionResult]) -> str:
        """Assess overall risk level"""
        if any(i.severity == "major" for i in interactions):
            return "high"
        elif any(i.severity == "moderate" for i in interactions):
            return "medium"
        elif interactions:
            return "low"
        else:
            return "none"


def check_medication_interactions(medications: list[str]) -> dict:
    """Convenience function to check medication interactions"""
    checker = MedicationInteractionChecker()
    return checker.get_interaction_summary(medications)

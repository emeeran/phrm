"""
Medication interaction checker utility.

This module provides functionality to check for potential interactions
between medications within a family member's current medication list.
"""

from typing import Dict, List, Optional, Tuple

from ..models.core.current_medication import CurrentMedication


class MedicineInteractionChecker:
    """Utility for checking medicine interactions"""

    def __init__(self):
        """Initialize the medicine interaction checker"""
        # In a production environment, this would connect to a proper drug interaction database
        # For now, we'll use a simple in-memory approach with common interactions
        self.interaction_db = self._initialize_interaction_db()

    def check_interactions(self, family_member_id: int) -> List[Dict]:
        """
        Check for interactions between all medications for a family member

        Args:
            family_member_id: ID of the family member

        Returns:
            List of interaction information dictionaries
        """
        # Get all current medications for the family member
        medications = CurrentMedication.query.filter_by(
            family_member_id=family_member_id
        ).all()

        if not medications or len(medications) < 2:
            return []

        # Check each pair of medications for interactions
        interactions = []
        for i in range(len(medications)):
            for j in range(i + 1, len(medications)):
                med1 = medications[i].medicine.lower()
                med2 = medications[j].medicine.lower()

                interaction = self._check_pair(med1, med2)
                if interaction:
                    interactions.append(
                        {
                            "medication1": medications[i].medicine,
                            "medication2": medications[j].medicine,
                            "severity": interaction["severity"],
                            "description": interaction["description"],
                            "recommendation": interaction["recommendation"],
                        }
                    )

        return interactions

    def check_medicine_with_list(
        self, medicine: str, medication_list: List[str]
    ) -> List[Dict]:
        """
        Check a single medicine against a list of medications

        Args:
            medicine: The medicine name to check
            medication_list: List of medication names to check against

        Returns:
            List of interaction information dictionaries
        """
        interactions = []
        med_lower = medicine.lower()

        for other_med in medication_list:
            other_lower = other_med.lower()
            interaction = self._check_pair(med_lower, other_lower)
            if interaction:
                interactions.append(
                    {
                        "medication1": medicine,
                        "medication2": other_med,
                        "severity": interaction["severity"],
                        "description": interaction["description"],
                        "recommendation": interaction["recommendation"],
                    }
                )

        return interactions

    def _check_pair(self, medicine1: str, medicine2: str) -> Optional[Dict]:
        """
        Check for interaction between two medications

        Args:
            medicine1: First medication name (lowercase)
            medicine2: Second medication name (lowercase)

        Returns:
            Interaction information or None if no interaction
        """
        # Check direct match
        pair_key = tuple(sorted([medicine1, medicine2]))
        if pair_key in self.interaction_db:
            return self.interaction_db[pair_key]

        # Check partial matches (for generic names, active ingredients)
        for db_pair, interaction in self.interaction_db.items():
            # Check if either medicine is a substring of the db entry or vice versa
            if (medicine1 in db_pair[0] or db_pair[0] in medicine1) and (
                medicine2 in db_pair[1] or db_pair[1] in medicine2
            ):
                return interaction

        return None

    def _initialize_interaction_db(self) -> Dict[Tuple[str, str], Dict]:
        """
        Initialize the interaction database with common drug interactions

        Returns:
            Dictionary mapping medicine pairs to interaction information
        """
        # This is a simplified example - a real implementation would use a proper drug interaction database
        interactions = {}

        # Format: {(drug1, drug2): {severity, description, recommendation}}
        interactions[("aspirin", "warfarin")] = {
            "severity": "high",
            "description": "Increased risk of bleeding when taken together",
            "recommendation": "Avoid combination unless directed by doctor. Monitor for signs of bleeding.",
        }

        interactions[("ibuprofen", "aspirin")] = {
            "severity": "moderate",
            "description": "May reduce aspirin's heart benefits and increase risk of GI problems",
            "recommendation": "Take aspirin at least 30 minutes before or 8 hours after ibuprofen",
        }

        interactions[("ciprofloxacin", "calcium")] = {
            "severity": "moderate",
            "description": "Calcium can reduce the absorption of ciprofloxacin",
            "recommendation": "Take ciprofloxacin 2 hours before or 6 hours after calcium supplements",
        }

        interactions[("omeprazole", "clopidogrel")] = {
            "severity": "high",
            "description": "Omeprazole can reduce the effectiveness of clopidogrel",
            "recommendation": "Consider alternative acid-reducing medication like pantoprazole",
        }

        interactions[("simvastatin", "amlodipine")] = {
            "severity": "moderate",
            "description": "Amlodipine can increase simvastatin levels, raising risk of muscle problems",
            "recommendation": "Limit simvastatin dose to 20mg daily when taking amlodipine",
        }

        interactions[("lisinopril", "spironolactone")] = {
            "severity": "moderate",
            "description": "Combination increases risk of high potassium levels",
            "recommendation": "Monitor potassium levels regularly",
        }

        interactions[("metformin", "furosemide")] = {
            "severity": "low",
            "description": "Furosemide may temporarily reduce metformin clearance",
            "recommendation": "Monitor blood glucose more frequently when starting/stopping furosemide",
        }

        interactions[("digoxin", "amiodarone")] = {
            "severity": "high",
            "description": "Amiodarone increases digoxin levels significantly",
            "recommendation": "Reduce digoxin dose by 50% and monitor levels",
        }

        interactions[("levothyroxine", "calcium")] = {
            "severity": "moderate",
            "description": "Calcium supplements can reduce levothyroxine absorption",
            "recommendation": "Take levothyroxine at least 4 hours apart from calcium supplements",
        }

        interactions[("methotrexate", "ibuprofen")] = {
            "severity": "high",
            "description": "NSAIDs can increase methotrexate toxicity",
            "recommendation": "Avoid NSAIDs within 48 hours of methotrexate dose",
        }

        # Convert keys to ensure they are always in alphabetical order
        return {tuple(sorted(key)): value for key, value in interactions.items()}

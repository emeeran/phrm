"""
Drug Interaction Checker Module

This module provides functionality to check for potential drug interactions
between medications using a comprehensive database of known interactions.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class InteractionSeverity(Enum):
    """Severity levels for drug interactions"""

    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CONTRAINDICATED = "contraindicated"


@dataclass
class DrugInteraction:
    """Represents a drug interaction"""

    drug1: str
    drug2: str
    severity: InteractionSeverity
    description: str
    mechanism: str
    management: str
    references: List[str] = None


class DrugInteractionChecker:
    """
    Comprehensive drug interaction checker
    """

    def __init__(self):
        self.interactions = self._load_interaction_database()
        self.drug_aliases = self._load_drug_aliases()

    def _load_interaction_database(self) -> List[DrugInteraction]:
        """Load comprehensive drug interaction database"""
        return [
            # Anticoagulant interactions
            DrugInteraction(
                drug1="warfarin",
                drug2="aspirin",
                severity=InteractionSeverity.MAJOR,
                description="Increased risk of bleeding due to additive anticoagulant effects",
                mechanism="Warfarin inhibits vitamin K synthesis, aspirin inhibits platelet aggregation",
                management="Monitor INR closely, consider gastroprotection, watch for bleeding signs",
            ),
            DrugInteraction(
                drug1="warfarin",
                drug2="ibuprofen",
                severity=InteractionSeverity.MAJOR,
                description="Increased bleeding risk and potential warfarin displacement",
                mechanism="NSAIDs can displace warfarin from protein binding and affect platelet function",
                management="Avoid combination if possible, use acetaminophen alternative",
            ),
            # Diabetes medication interactions
            DrugInteraction(
                drug1="metformin",
                drug2="alcohol",
                severity=InteractionSeverity.MODERATE,
                description="Increased risk of lactic acidosis",
                mechanism="Both can affect lactate metabolism",
                management="Limit alcohol consumption, monitor for signs of lactic acidosis",
            ),
            DrugInteraction(
                drug1="insulin",
                drug2="alcohol",
                severity=InteractionSeverity.MODERATE,
                description="Increased hypoglycemia risk",
                mechanism="Alcohol can mask hypoglycemia symptoms and affect glucose metabolism",
                management="Monitor blood glucose closely, educate patient on signs",
            ),
            # Cardiovascular medication interactions
            DrugInteraction(
                drug1="digoxin",
                drug2="furosemide",
                severity=InteractionSeverity.MODERATE,
                description="Increased digoxin toxicity risk due to potassium depletion",
                mechanism="Furosemide causes hypokalemia which increases digoxin sensitivity",
                management="Monitor potassium levels, consider potassium supplementation",
            ),
            DrugInteraction(
                drug1="amlodipine",
                drug2="simvastatin",
                severity=InteractionSeverity.MODERATE,
                description="Increased risk of myopathy and rhabdomyolysis",
                mechanism="Amlodipine inhibits CYP3A4 metabolism of simvastatin",
                management="Limit simvastatin dose to 20mg daily, monitor for muscle symptoms",
            ),
            # Antibiotic interactions
            DrugInteraction(
                drug1="ciprofloxacin",
                drug2="warfarin",
                severity=InteractionSeverity.MODERATE,
                description="Enhanced anticoagulant effect",
                mechanism="Ciprofloxacin inhibits warfarin metabolism",
                management="Monitor INR closely during and after antibiotic course",
            ),
            DrugInteraction(
                drug1="clarithromycin",
                drug2="atorvastatin",
                severity=InteractionSeverity.MAJOR,
                description="Increased statin levels and myopathy risk",
                mechanism="Clarithromycin inhibits CYP3A4 metabolism",
                management="Consider statin suspension during antibiotic course",
            ),
            # Psychiatric medication interactions
            DrugInteraction(
                drug1="sertraline",
                drug2="tramadol",
                severity=InteractionSeverity.MAJOR,
                description="Increased risk of serotonin syndrome",
                mechanism="Both drugs increase serotonin levels",
                management="Monitor for serotonin syndrome symptoms, consider alternatives",
            ),
            DrugInteraction(
                drug1="lithium",
                drug2="hydrochlorothiazide",
                severity=InteractionSeverity.MAJOR,
                description="Increased lithium levels and toxicity risk",
                mechanism="Thiazides decrease lithium clearance",
                management="Monitor lithium levels closely, adjust dose as needed",
            ),
            # ACE inhibitor interactions
            DrugInteraction(
                drug1="lisinopril",
                drug2="potassium",
                severity=InteractionSeverity.MODERATE,
                description="Increased risk of hyperkalemia",
                mechanism="ACE inhibitors reduce potassium excretion",
                management="Monitor potassium levels, avoid potassium supplements",
            ),
            DrugInteraction(
                drug1="enalapril",
                drug2="spironolactone",
                severity=InteractionSeverity.MODERATE,
                description="Increased hyperkalemia risk",
                mechanism="Both drugs can increase potassium levels",
                management="Monitor potassium levels closely",
            ),
            # Proton pump inhibitor interactions
            DrugInteraction(
                drug1="omeprazole",
                drug2="clopidogrel",
                severity=InteractionSeverity.MODERATE,
                description="Reduced antiplatelet effect of clopidogrel",
                mechanism="Omeprazole inhibits CYP2C19 activation of clopidogrel",
                management="Consider pantoprazole alternative or H2 blocker",
            ),
            # Additional important interactions
            DrugInteraction(
                drug1="phenytoin",
                drug2="warfarin",
                severity=InteractionSeverity.MODERATE,
                description="Variable effects on anticoagulation",
                mechanism="Complex interaction affecting warfarin metabolism",
                management="Monitor INR closely, adjust warfarin dose as needed",
            ),
            DrugInteraction(
                drug1="carbamazepine",
                drug2="birth_control",
                severity=InteractionSeverity.MAJOR,
                description="Reduced contraceptive efficacy",
                mechanism="Carbamazepine induces hepatic metabolism of hormones",
                management="Use additional contraceptive methods",
            ),
        ]

    def _load_drug_aliases(self) -> Dict[str, List[str]]:
        """Load drug name aliases and generic/brand name mappings"""
        return {
            "warfarin": ["coumadin", "jantoven"],
            "aspirin": ["acetylsalicylic acid", "asa", "bayer", "bufferin"],
            "ibuprofen": ["advil", "motrin", "nuprin"],
            "metformin": ["glucophage", "fortamet", "riomet"],
            "insulin": ["humulin", "novolin", "lantus", "humalog", "novolog"],
            "digoxin": ["lanoxin", "digitek"],
            "furosemide": ["lasix"],
            "amlodipine": ["norvasc"],
            "simvastatin": ["zocor"],
            "ciprofloxacin": ["cipro"],
            "clarithromycin": ["biaxin"],
            "atorvastatin": ["lipitor"],
            "sertraline": ["zoloft"],
            "tramadol": ["ultram", "conzip"],
            "lithium": ["lithobid", "eskalith"],
            "hydrochlorothiazide": ["hctz", "microzide"],
            "lisinopril": ["prinivil", "zestril"],
            "enalapril": ["vasotec"],
            "spironolactone": ["aldactone"],
            "omeprazole": ["prilosec"],
            "clopidogrel": ["plavix"],
            "phenytoin": ["dilantin"],
            "carbamazepine": ["tegretol"],
            "birth_control": [
                "oral contraceptive",
                "contraceptive pill",
                "birth control pill",
            ],
        }

    def normalize_drug_name(self, drug_name: str) -> str:
        """Normalize drug name to standard form"""
        drug_name = drug_name.lower().strip()

        # Remove common suffixes and dosage information
        drug_name = re.sub(r"\s+\d+\s*mg.*$", "", drug_name)
        drug_name = re.sub(r"\s+\d+\s*mcg.*$", "", drug_name)
        drug_name = re.sub(r"\s+tablet.*$", "", drug_name)
        drug_name = re.sub(r"\s+capsule.*$", "", drug_name)
        drug_name = re.sub(r"\s+injection.*$", "", drug_name)

        # Check aliases
        for standard_name, aliases in self.drug_aliases.items():
            if drug_name in aliases or drug_name == standard_name:
                return standard_name

        return drug_name

    def check_interactions(self, medications: List[str]) -> List[Dict[str, Any]]:
        """
        Check for interactions between a list of medications

        Args:
            medications: List of medication names

        Returns:
            List of interaction dictionaries with details
        """
        interactions_found = []
        normalized_meds = [self.normalize_drug_name(med) for med in medications]

        # Check each pair of medications
        for i, med1 in enumerate(normalized_meds):
            for j, med2 in enumerate(normalized_meds):
                if i >= j:  # Avoid duplicate checks
                    continue

                # Check for direct interactions
                interaction = self._find_interaction(med1, med2)
                if interaction:
                    interactions_found.append(
                        {
                            "original_drug1": medications[i],
                            "original_drug2": medications[j],
                            "normalized_drug1": med1,
                            "normalized_drug2": med2,
                            "severity": interaction.severity.value,
                            "description": interaction.description,
                            "mechanism": interaction.mechanism,
                            "management": interaction.management,
                            "severity_level": self._get_severity_level(
                                interaction.severity
                            ),
                        }
                    )

        # Sort by severity (most severe first)
        interactions_found.sort(
            key=lambda x: ["contraindicated", "major", "moderate", "minor"].index(
                x["severity"]
            )
        )

        return interactions_found

    def _find_interaction(self, drug1: str, drug2: str) -> DrugInteraction:
        """Find interaction between two drugs"""
        for interaction in self.interactions:
            if (interaction.drug1 == drug1 and interaction.drug2 == drug2) or (
                interaction.drug1 == drug2 and interaction.drug2 == drug1
            ):
                return interaction
        return None

    def _get_severity_level(self, severity: InteractionSeverity) -> int:
        """Get numeric severity level for sorting"""
        levels = {
            InteractionSeverity.MINOR: 1,
            InteractionSeverity.MODERATE: 2,
            InteractionSeverity.MAJOR: 3,
            InteractionSeverity.CONTRAINDICATED: 4,
        }
        return levels.get(severity, 0)

    def get_severity_color(self, severity: str) -> str:
        """Get CSS color class for severity"""
        colors = {
            "minor": "text-info",
            "moderate": "text-warning",
            "major": "text-danger",
            "contraindicated": "text-dark bg-danger",
        }
        return colors.get(severity, "text-muted")

    def check_medication_list(
        self, medication_list: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Check interactions for a structured medication list

        Args:
            medication_list: List of dicts with 'person', 'medicine', etc.

        Returns:
            Dict with interaction results and summary
        """
        # Extract unique medications
        medications = []
        med_to_persons = {}

        for med_entry in medication_list:
            medicine = med_entry.get("medicine", "").strip()
            person = med_entry.get("person", "Unknown")

            if medicine:
                medications.append(medicine)
                if medicine not in med_to_persons:
                    med_to_persons[medicine] = []
                med_to_persons[medicine].append(person)

        # Check interactions
        interactions = self.check_interactions(medications)

        # Add person information to interactions
        for interaction in interactions:
            interaction["drug1_persons"] = med_to_persons.get(
                interaction["original_drug1"], []
            )
            interaction["drug2_persons"] = med_to_persons.get(
                interaction["original_drug2"], []
            )

        # Generate summary
        summary = {
            "total_medications": len(set(medications)),
            "total_interactions": len(interactions),
            "severity_counts": {
                "minor": len([i for i in interactions if i["severity"] == "minor"]),
                "moderate": len(
                    [i for i in interactions if i["severity"] == "moderate"]
                ),
                "major": len([i for i in interactions if i["severity"] == "major"]),
                "contraindicated": len(
                    [i for i in interactions if i["severity"] == "contraindicated"]
                ),
            },
            "high_risk": len(
                [
                    i
                    for i in interactions
                    if i["severity"] in ["major", "contraindicated"]
                ]
            ),
        }

        return {
            "interactions": interactions,
            "summary": summary,
            "medications_by_person": med_to_persons,
        }


# Global instance
drug_checker = DrugInteractionChecker()


def check_drug_interactions(medications: List[str]) -> List[Dict[str, Any]]:
    """Convenience function to check drug interactions"""
    return drug_checker.check_interactions(medications)


def check_medication_interactions(
    medication_list: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Convenience function to check interactions in medication list"""
    return drug_checker.check_medication_list(medication_list)

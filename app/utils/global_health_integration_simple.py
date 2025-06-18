"""
Global Health Data Integration System
Simplified version providing basic integration with international health standards
"""

import logging
import sqlite3
from datetime import datetime
from threading import Lock
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Standard health data formats and codes
HEALTH_STANDARDS = {
    "HL7_FHIR": {
        "version": "R4",
        "base_url": "http://hl7.org/fhir/",
        "resources": ["Patient", "Observation", "Condition", "Medication", "Procedure"],
    },
    "ICD_11": {
        "version": "2022-02",
        "base_url": "https://icd.who.int/browse11/",
        "language": "en",
    },
    "SNOMED_CT": {
        "version": "international",
        "base_url": "http://snomed.info/sct/",
        "edition": "900000000000207008",
    },
    "LOINC": {
        "version": "2.73",
        "base_url": "https://loinc.org/",
        "system": "http://loinc.org",
    },
}

# Global health database lock
_db_lock = Lock()
_initialized = False


def init_global_health_integration():
    """Initialize global health integration system"""
    global _initialized

    try:
        if _initialized:
            logger.info("Global health integration already initialized")
            return True

        logger.info("Initializing global health integration system...")

        # Create database tables if needed
        _create_health_tables()

        # Load basic health standards
        _load_basic_standards()

        _initialized = True
        logger.info("Global health integration system initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize global health integration: {e}")
        return False


def _create_health_tables():
    """Create necessary database tables"""
    try:
        from flask import current_app

        db_path = current_app.config.get(
            "GLOBAL_HEALTH_DB_PATH", "instance/global_health.db"
        )

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Health standards table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS health_standards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    version TEXT NOT NULL,
                    description TEXT,
                    base_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Health codes table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS health_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    standard_name TEXT NOT NULL,
                    code TEXT NOT NULL,
                    display TEXT NOT NULL,
                    system TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (standard_name) REFERENCES health_standards (name)
                )
            """
            )

            conn.commit()
            logger.info("Global health database tables created/verified")

    except Exception as e:
        logger.error(f"Error creating health tables: {e}")
        raise


def _load_basic_standards():
    """Load basic health standards into database"""
    try:
        from flask import current_app

        db_path = current_app.config.get(
            "GLOBAL_HEALTH_DB_PATH", "instance/global_health.db"
        )

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Insert basic standards
            for name, config in HEALTH_STANDARDS.items():
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO health_standards
                    (name, version, description, base_url)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        name,
                        config.get("version", ""),
                        f"{name} Health Standard",
                        config.get("base_url", ""),
                    ),
                )

            conn.commit()
            logger.info(f"Loaded {len(HEALTH_STANDARDS)} basic health standards")

    except Exception as e:
        logger.error(f"Error loading basic standards: {e}")
        raise


def get_health_standard(name: str) -> Optional[Dict[str, Any]]:
    """Get information about a health standard"""
    try:
        return HEALTH_STANDARDS.get(name)
    except Exception as e:
        logger.error(f"Error getting health standard {name}: {e}")
        return None


def validate_health_code(standard: str, code: str) -> bool:
    """Basic validation of health code format"""
    try:
        if not standard or not code:
            return False

        # Basic format validation based on standard
        if standard == "ICD_11":
            # ICD-11 codes typically start with letters followed by numbers
            return len(code) >= 3 and any(c.isalpha() for c in code)
        elif standard == "SNOMED_CT":
            # SNOMED CT codes are typically numeric
            return code.isdigit() and len(code) >= 6
        elif standard == "LOINC":
            # LOINC codes are typically numeric with dash
            return "-" in code and any(c.isdigit() for c in code.split("-"))

        return True  # Default to valid for unknown standards

    except Exception as e:
        logger.error(f"Error validating health code {code} for {standard}: {e}")
        return False


def format_health_data_fhir(data: Dict[str, Any]) -> Dict[str, Any]:
    """Format health data according to FHIR standard"""
    try:
        fhir_data = {
            "resourceType": "Observation",
            "id": data.get("id", f"obs-{datetime.now().timestamp()}"),
            "status": "final",
            "subject": {"reference": f"Patient/{data.get('patient_id', 'unknown')}"},
            "effectiveDateTime": data.get("date", datetime.now().isoformat()),
            "valueString": data.get("value", ""),
        }

        if data.get("code"):
            fhir_data["code"] = {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": data["code"],
                        "display": data.get("display", ""),
                    }
                ]
            }

        return fhir_data

    except Exception as e:
        logger.error(f"Error formatting FHIR data: {e}")
        return {}


def get_integration_status() -> Dict[str, Any]:
    """Get current status of global health integration"""
    return {
        "initialized": _initialized,
        "standards_available": list(HEALTH_STANDARDS.keys()),
        "standards_count": len(HEALTH_STANDARDS),
        "last_check": datetime.now().isoformat(),
    }


# Export main functions
__all__ = [
    "format_health_data_fhir",
    "get_health_standard",
    "get_integration_status",
    "init_global_health_integration",
    "validate_health_code",
]

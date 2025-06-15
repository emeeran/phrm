"""
Export Utilities

Provides export functionality for health records to various formats.
"""

import io
import json
from datetime import datetime

from ..models import HealthRecord, User


class HealthRecordExporter:
    """Export health records to various formats"""

    def export_user_records_pdf(
        self, user: User, include_family: bool = False
    ) -> io.BytesIO:
        """
        Export user's health records to PDF (simplified text version)

        Args:
            user: User whose records to export
            include_family: Whether to include family member records

        Returns:
            BytesIO buffer containing a simple text report
        """
        buffer = io.BytesIO()

        # Create a simple text report instead of PDF
        report_lines = []
        report_lines.append("HEALTH RECORDS EXPORT")
        report_lines.append(f"Patient: {user.first_name} {user.last_name}")
        report_lines.append(
            f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        )
        report_lines.append("=" * 60)
        report_lines.append("")

        # User's own records
        records = (
            HealthRecord.query.filter_by(user_id=user.id, family_member_id=None)
            .order_by(HealthRecord.date.desc())
            .all()
        )

        report_lines.append("PERSONAL HEALTH RECORDS")
        report_lines.append("-" * 40)

        if not records:
            report_lines.append("No health records found.")
        else:
            for record in records:
                report_lines.append(
                    f"Date: {record.date.strftime('%m/%d/%Y') if record.date else 'N/A'}"
                )
                report_lines.append(f"Type: {record.record_type or 'General'}")
                if record.provider:
                    report_lines.append(f"Provider: {record.provider}")
                if record.summary:
                    report_lines.append(f"Summary: {record.summary}")
                report_lines.append("-" * 20)

        # Family records if requested
        if include_family and user.family_members:
            report_lines.append("")
            report_lines.append("FAMILY HEALTH RECORDS")
            report_lines.append("-" * 40)

            for family_member in user.family_members:
                report_lines.append(
                    f"\n{family_member.first_name} {family_member.last_name} ({family_member.relationship})"
                )

                family_records = (
                    HealthRecord.query.filter_by(family_member_id=family_member.id)
                    .order_by(HealthRecord.date.desc())
                    .all()
                )

                if not family_records:
                    report_lines.append("No health records found.")
                else:
                    for record in family_records:
                        report_lines.append(
                            f"  Date: {record.date.strftime('%m/%d/%Y') if record.date else 'N/A'}"
                        )
                        report_lines.append(
                            f"  Type: {record.record_type or 'General'}"
                        )
                        if record.summary:
                            report_lines.append(f"  Summary: {record.summary}")
                        report_lines.append("  " + "-" * 15)

        # Write to buffer
        report_content = "\n".join(report_lines)
        buffer.write(report_content.encode("utf-8"))
        buffer.seek(0)
        return buffer

    def export_single_record_pdf(self, record: HealthRecord) -> io.BytesIO:
        """Export a single health record to text format"""
        buffer = io.BytesIO()

        report_lines = []
        report_lines.append("HEALTH RECORD EXPORT")
        report_lines.append(
            f"Date: {record.date.strftime('%B %d, %Y') if record.date else 'No Date'}"
        )
        report_lines.append("=" * 40)
        report_lines.append("")

        if record.record_type:
            report_lines.append(f"Type: {record.record_type}")
        if record.provider:
            report_lines.append(f"Provider: {record.provider}")
        if record.location:
            report_lines.append(f"Location: {record.location}")

        report_lines.append("")

        if record.summary:
            report_lines.append("SUMMARY")
            report_lines.append("-" * 20)
            report_lines.append(record.summary)
            report_lines.append("")

        if record.symptoms:
            report_lines.append("SYMPTOMS")
            report_lines.append("-" * 20)
            report_lines.append(record.symptoms)
            report_lines.append("")

        if record.diagnosis:
            report_lines.append("DIAGNOSIS")
            report_lines.append("-" * 20)
            report_lines.append(record.diagnosis)
            report_lines.append("")

        if record.treatment:
            report_lines.append("TREATMENT")
            report_lines.append("-" * 20)
            report_lines.append(record.treatment)
            report_lines.append("")

        if record.notes:
            report_lines.append("NOTES")
            report_lines.append("-" * 20)
            report_lines.append(record.notes)

        report_content = "\n".join(report_lines)
        buffer.write(report_content.encode("utf-8"))
        buffer.seek(0)
        return buffer

    def export_user_records_json(self, user: User, include_family: bool = False) -> str:
        """Export user's health records to JSON format"""
        data = {
            "export_info": {
                "patient_name": f"{user.first_name} {user.last_name}",
                "export_date": datetime.now().isoformat(),
                "include_family": include_family,
            },
            "personal_records": [],
            "family_records": {},
        }

        # User's own records
        records = (
            HealthRecord.query.filter_by(user_id=user.id, family_member_id=None)
            .order_by(HealthRecord.date.desc())
            .all()
        )

        for record in records:
            record_data = {
                "id": record.id,
                "date": record.date.isoformat() if record.date else None,
                "record_type": record.record_type,
                "provider": record.provider,
                "location": record.location,
                "summary": record.summary,
                "symptoms": record.symptoms,
                "diagnosis": record.diagnosis,
                "treatment": record.treatment,
                "notes": record.notes,
                "created_at": (
                    record.created_at.isoformat() if record.created_at else None
                ),
            }
            data["personal_records"].append(record_data)

        # Family records if requested
        if include_family and user.family_members:
            for family_member in user.family_members:
                member_key = f"{family_member.first_name}_{family_member.last_name}"
                data["family_records"][member_key] = {
                    "member_info": {
                        "name": f"{family_member.first_name} {family_member.last_name}",
                        "relationship": family_member.relationship,
                        "date_of_birth": (
                            family_member.date_of_birth.isoformat()
                            if family_member.date_of_birth
                            else None
                        ),
                    },
                    "records": [],
                }

                family_records = (
                    HealthRecord.query.filter_by(family_member_id=family_member.id)
                    .order_by(HealthRecord.date.desc())
                    .all()
                )

                for record in family_records:
                    record_data = {
                        "id": record.id,
                        "date": record.date.isoformat() if record.date else None,
                        "record_type": record.record_type,
                        "provider": record.provider,
                        "summary": record.summary,
                        "symptoms": record.symptoms,
                        "diagnosis": record.diagnosis,
                        "treatment": record.treatment,
                    }
                    data["family_records"][member_key]["records"].append(record_data)

        return json.dumps(data, indent=2, ensure_ascii=False)


def export_health_records_pdf(user: User, include_family: bool = False) -> io.BytesIO:
    """Convenience function to export health records to text format"""
    exporter = HealthRecordExporter()
    return exporter.export_user_records_pdf(user, include_family)


def export_single_record_pdf(record: HealthRecord) -> io.BytesIO:
    """Convenience function to export single record to text format"""
    exporter = HealthRecordExporter()
    return exporter.export_single_record_pdf(record)


def export_health_records_json(user: User, include_family: bool = False) -> str:
    """Convenience function to export health records to JSON"""
    exporter = HealthRecordExporter()
    return exporter.export_user_records_json(user, include_family)

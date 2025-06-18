#!/usr/bin/env python3
"""
Initialize the database with tables for family health records.

This script creates all necessary tables and adds sample data for testing.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Ensure the application directory is in the path
app_path = str(Path(__file__).resolve().parent)
if app_path not in sys.path:
    sys.path.insert(0, app_path)

from app import create_app
from app.models import db
from app.models.core.appointment import Appointment
from app.models.core.current_medication import CurrentMedication
from app.models.core.family_member import FamilyMember
from app.models.core.health_record import HealthRecord
from app.models.core.medical_condition import MedicalCondition
from app.models.core.user import User

app = create_app()


def init_db():
    """Initialize the database with tables and sample data"""
    with app.app_context():
        db.create_all()

        # Check if we already have users
        if User.query.first():
            print("Database already contains data. Skipping initialization.")
            return

        # Create a test user
        test_user = User(
            username="testuser",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            date_of_birth=datetime(1980, 1, 15),
        )
        test_user.set_password("password")
        db.session.add(test_user)
        db.session.commit()

        # Create family members
        wife = FamilyMember(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1982, 5, 10),
            relationship="Spouse",
            gender="Female",
            blood_group="O+",
            height=165,
            weight=60,
        )

        daughter = FamilyMember(
            first_name="Emily",
            last_name="Doe",
            date_of_birth=datetime(2010, 3, 22),
            relationship="Daughter",
            gender="Female",
            blood_group="A+",
            height=140,
            weight=35,
        )

        son = FamilyMember(
            first_name="Michael",
            last_name="Doe",
            date_of_birth=datetime(2015, 11, 5),
            relationship="Son",
            gender="Male",
            blood_group="B+",
            height=110,
            weight=25,
        )

        # Add family members to user
        test_user.family_members.append(wife)
        test_user.family_members.append(daughter)
        test_user.family_members.append(son)
        db.session.commit()

        # Create some health records
        records = [
            # Records for Jane (wife)
            HealthRecord(
                user_id=None,
                family_member_id=wife.id,
                date=datetime.now() - timedelta(days=10),
                chief_complaint="Persistent migraine headaches",
                doctor="Dr. Smith",
                doctor_specialty="Neurology",
                clinic_hospital="City Medical Center",
                diagnosis="Chronic migraine",
                prescription="Sumatriptan 50mg as needed",
                notes="Patient reports triggers include stress and lack of sleep",
            ),
            HealthRecord(
                user_id=None,
                family_member_id=wife.id,
                date=datetime.now() - timedelta(days=60),
                chief_complaint="Annual checkup",
                doctor="Dr. Johnson",
                doctor_specialty="Family Medicine",
                clinic_hospital="Community Health Clinic",
                diagnosis="Healthy, normal blood work",
                notes="Continue regular exercise and healthy diet",
            ),
            # Records for Emily (daughter)
            HealthRecord(
                user_id=None,
                family_member_id=daughter.id,
                date=datetime.now() - timedelta(days=5),
                chief_complaint="Sore throat and fever",
                doctor="Dr. Patel",
                doctor_specialty="Pediatrics",
                clinic_hospital="Children's Hospital",
                diagnosis="Strep throat",
                prescription="Amoxicillin 250mg 3x daily for 10 days",
                notes="Rest and plenty of fluids",
            ),
            # Records for Michael (son)
            HealthRecord(
                user_id=None,
                family_member_id=son.id,
                date=datetime.now() - timedelta(days=30),
                chief_complaint="Routine vaccination",
                doctor="Dr. Patel",
                doctor_specialty="Pediatrics",
                clinic_hospital="Children's Hospital",
                notes="Received scheduled vaccinations, no concerns",
            ),
            # Records for self (John)
            HealthRecord(
                user_id=test_user.id,
                family_member_id=None,
                date=datetime.now() - timedelta(days=45),
                chief_complaint="Lower back pain",
                doctor="Dr. Martinez",
                doctor_specialty="Orthopedics",
                clinic_hospital="Spine Specialists",
                diagnosis="Lumbar strain",
                prescription="Naproxen 500mg twice daily",
                notes="Recommended physical therapy and ergonomic chair",
            ),
        ]

        for record in records:
            db.session.add(record)
        db.session.commit()

        # Create medical conditions
        conditions = [
            # Condition for Jane
            MedicalCondition(
                user_id=None,
                family_member_id=wife.id,
                condition_name="Chronic Migraine",
                condition_category="Neurological",
                diagnosed_date=datetime.now() - timedelta(days=180),
                diagnosing_doctor="Dr. Smith",
                current_status="managed",
                severity="moderate",
                current_treatments="Sumatriptan, stress management techniques",
                monitoring_plan="Monthly follow-ups",
            ),
            # Condition for Emily
            MedicalCondition(
                user_id=None,
                family_member_id=daughter.id,
                condition_name="Seasonal Allergies",
                condition_category="Immunological",
                diagnosed_date=datetime.now() - timedelta(days=365),
                diagnosing_doctor="Dr. Patel",
                current_status="managed",
                severity="mild",
                current_treatments="Loratadine during spring-summer",
                monitoring_plan="As needed during allergy season",
            ),
            # Condition for self (John)
            MedicalCondition(
                user_id=test_user.id,
                family_member_id=None,
                condition_name="Hypertension",
                condition_category="Cardiovascular",
                diagnosed_date=datetime.now() - timedelta(days=730),
                diagnosing_doctor="Dr. Johnson",
                current_status="managed",
                severity="moderate",
                current_treatments="Lisinopril 10mg daily, low sodium diet",
                monitoring_plan="Blood pressure checks twice weekly",
            ),
        ]

        for condition in conditions:
            db.session.add(condition)
        db.session.commit()

        # Create current medications
        medications = [
            # Medications for Jane
            CurrentMedication(
                family_member_id=wife.id,
                medicine="Sumatriptan",
                strength="50mg",
                morning=None,
                noon=None,
                evening=None,
                bedtime="As needed",
                duration="Ongoing",
                notes="Take at first sign of migraine",
            ),
            # Medications for Emily
            CurrentMedication(
                family_member_id=daughter.id,
                medicine="Amoxicillin",
                strength="250mg",
                morning="1 tablet",
                noon=None,
                evening="1 tablet",
                bedtime=None,
                duration="10 days",
                notes="Take with food",
            ),
            CurrentMedication(
                family_member_id=daughter.id,
                medicine="Loratadine",
                strength="5mg",
                morning="1 tablet",
                noon=None,
                evening=None,
                bedtime=None,
                duration="During allergy season",
                notes="Take as needed for allergies",
            ),
            # Medications for self (John) would be added to a personal medications table
            # which is not yet implemented
        ]

        for medication in medications:
            db.session.add(medication)
        db.session.commit()

        # Create appointments
        appointments = [
            # Appointment for Jane
            Appointment(
                user_id=test_user.id,
                family_member_id=wife.id,
                title="Neurologist Follow-up",
                doctor_name="Dr. Smith",
                doctor_specialty="Neurology",
                clinic_hospital="City Medical Center",
                appointment_date=datetime.now() + timedelta(days=14),
                duration_minutes=45,
                status="scheduled",
                purpose="Follow-up on migraine treatment",
            ),
            # Appointment for Emily
            Appointment(
                user_id=test_user.id,
                family_member_id=daughter.id,
                title="Strep Throat Follow-up",
                doctor_name="Dr. Patel",
                doctor_specialty="Pediatrics",
                clinic_hospital="Children's Hospital",
                appointment_date=datetime.now() + timedelta(days=7),
                duration_minutes=30,
                status="scheduled",
                purpose="Follow-up after antibiotics",
            ),
            # Appointment for self (John)
            Appointment(
                user_id=test_user.id,
                family_member_id=None,
                title="Annual Physical",
                doctor_name="Dr. Johnson",
                doctor_specialty="Family Medicine",
                clinic_hospital="Community Health Clinic",
                appointment_date=datetime.now() + timedelta(days=30),
                duration_minutes=60,
                status="scheduled",
                purpose="Annual physical examination",
            ),
        ]

        for appointment in appointments:
            db.session.add(appointment)
        db.session.commit()

        print("Database initialized successfully with sample data.")


if __name__ == "__main__":
    init_db()

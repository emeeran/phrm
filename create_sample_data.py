#!/usr/bin/env python3
"""
Create sample data for the Personal Health Record Manager demo.
"""

from datetime import date, datetime, timedelta

from app import create_app
from app.models import (
    Appointment,
    CurrentMedication,
    FamilyMember,
    HealthRecord,
    User,
    db,
)


def create_sample_data():
    """Create sample users, family members, records, appointments, and medications."""

    app = create_app()
    with app.app_context():
        # Create a sample user
        user = User(
            email="demo@example.com",
            username="demouser",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 5, 15),
            is_active=True,
        )
        user.set_password("demo123")
        db.session.add(user)
        db.session.commit()

        print(f"Created user: {user.username}")

        # Create family members
        family_members_data = [
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "date_of_birth": date(1985, 8, 22),
                "relationship": "Spouse",
                "gender": "Female",
                "blood_type": "A+",
                "height": 165.0,
                "weight": 65.0,
                "allergies": "Penicillin",
                "chronic_conditions": "None",
                "current_medications": "Birth control pills",
            },
            {
                "first_name": "Emma",
                "last_name": "Doe",
                "date_of_birth": date(2010, 3, 10),
                "relationship": "Daughter",
                "gender": "Female",
                "blood_type": "O+",
                "height": 140.0,
                "weight": 35.0,
                "allergies": "None known",
                "chronic_conditions": "None",
                "current_medications": "Vitamin D supplements",
            },
            {
                "first_name": "Michael",
                "last_name": "Doe",
                "date_of_birth": date(2012, 11, 5),
                "relationship": "Son",
                "gender": "Male",
                "blood_type": "A+",
                "height": 130.0,
                "weight": 30.0,
                "allergies": "Tree nuts",
                "chronic_conditions": "Mild asthma",
                "current_medications": "Albuterol inhaler",
            },
        ]

        family_members = []
        for member_data in family_members_data:
            member = FamilyMember(**member_data)
            db.session.add(member)
            family_members.append(member)

        db.session.commit()

        # Associate family members with the user
        for member in family_members:
            user.family_members.append(member)

        db.session.commit()
        print(f"Created {len(family_members)} family members")

        # Create sample health records
        health_records_data = [
            {
                "family_member": family_members[0],  # Jane
                "record_type": "Doctor Visit",
                "title": "Annual Checkup",
                "description": "Routine annual physical examination. Blood pressure: 120/80. All vital signs normal.",
                "date": date.today() - timedelta(days=30),
                "doctor_name": "Dr. Smith",
                "is_emergency": False,
            },
            {
                "family_member": family_members[1],  # Emma
                "record_type": "Vaccination",
                "title": "School Immunizations",
                "description": "Updated school immunizations including TDaP booster.",
                "date": date.today() - timedelta(days=60),
                "doctor_name": "Dr. Johnson",
                "is_emergency": False,
            },
            {
                "family_member": family_members[2],  # Michael
                "record_type": "Allergy Test",
                "title": "Allergy Panel Results",
                "description": "Confirmed tree nut allergy. Prescribed EpiPen for emergencies.",
                "date": date.today() - timedelta(days=90),
                "doctor_name": "Dr. Wilson",
                "is_emergency": False,
            },
        ]

        for record_data in health_records_data:
            record = HealthRecord(
                user_id=user.id,
                family_member_id=record_data["family_member"].id,
                record_type=record_data["record_type"],
                title=record_data["title"],
                description=record_data["description"],
                date=record_data["date"],
                doctor_name=record_data["doctor_name"],
                is_emergency=record_data["is_emergency"],
            )
            db.session.add(record)

        db.session.commit()
        print("Created sample health records")

        # Create sample appointments
        appointments_data = [
            {
                "family_member": family_members[0],  # Jane
                "title": "Gynecologist Appointment",
                "description": "Annual gynecological checkup",
                "appointment_date": datetime.now() + timedelta(days=7),
                "doctor_name": "Dr. Brown",
                "location": "Women's Health Center",
                "status": "scheduled",
            },
            {
                "family_member": family_members[1],  # Emma
                "title": "Dentist Appointment",
                "description": "Routine dental cleaning and checkup",
                "appointment_date": datetime.now() + timedelta(days=14),
                "doctor_name": "Dr. Davis",
                "location": "Family Dental Care",
                "status": "scheduled",
            },
            {
                "family_member": family_members[2],  # Michael
                "title": "Asthma Follow-up",
                "description": "Follow-up for asthma management",
                "appointment_date": datetime.now() + timedelta(days=21),
                "doctor_name": "Dr. Wilson",
                "location": "Children's Clinic",
                "status": "scheduled",
            },
        ]

        for appt_data in appointments_data:
            appointment = Appointment(
                user_id=user.id,
                family_member_id=appt_data["family_member"].id,
                title=appt_data["title"],
                description=appt_data["description"],
                appointment_date=appt_data["appointment_date"],
                doctor_name=appt_data["doctor_name"],
                location=appt_data["location"],
                status=appt_data["status"],
            )
            db.session.add(appointment)

        db.session.commit()
        print("Created sample appointments")

        # Create sample current medications
        medications_data = [
            {
                "family_member": family_members[0],  # Jane
                "medication_name": "Birth Control Pills",
                "dosage": "1 tablet daily",
                "frequency": "Daily",
                "prescribing_doctor": "Dr. Brown",
                "notes": "Take at the same time each day",
            },
            {
                "family_member": family_members[1],  # Emma
                "medication_name": "Vitamin D3",
                "dosage": "1000 IU",
                "frequency": "Daily",
                "prescribing_doctor": "Dr. Johnson",
                "notes": "Take with food",
            },
            {
                "family_member": family_members[2],  # Michael
                "medication_name": "Albuterol Inhaler",
                "dosage": "2 puffs as needed",
                "frequency": "As needed",
                "prescribing_doctor": "Dr. Wilson",
                "notes": "Use for asthma symptoms or before exercise",
            },
        ]

        for med_data in medications_data:
            medication = CurrentMedication(
                user_id=user.id,
                family_member_id=med_data["family_member"].id,
                medication_name=med_data["medication_name"],
                dosage=med_data["dosage"],
                frequency=med_data["frequency"],
                prescribing_doctor=med_data["prescribing_doctor"],
                notes=med_data["notes"],
            )
            db.session.add(medication)

        db.session.commit()
        print("Created sample medications")

        print("\n✅ Sample data created successfully!")
        print("Demo login credentials:")
        print("  Email: demo@example.com")
        print("  Password: demo123")


if __name__ == "__main__":
    create_sample_data()

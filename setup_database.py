#!/usr/bin/env python3
"""
PHRM Database Setup and Sample Data Generator

This script initializes the Personal Health Records Manager database
and creates sample data for demonstration purposes.
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


def init_and_seed_database():
    """Initialize the database and create sample data."""

    app = create_app()
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        print("✅ Database tables created")

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

        print(f"✅ Created user: {user.username}")

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
        print(f"✅ Created {len(family_members)} family members")

        # Create sample health records
        health_records_data = [
            {
                "family_member": family_members[0],  # Jane
                "appointment_type": "Annual Checkup",
                "chief_complaint": "Routine physical examination",
                "doctor": "Dr. Smith",
                "diagnosis": "Good health, all vital signs normal",
                "notes": "Blood pressure: 120/80. Recommended annual mammogram.",
                "date": datetime.now() - timedelta(days=30),
                "clinic_hospital": "General Health Center",
            },
            {
                "family_member": family_members[1],  # Emma
                "appointment_type": "Vaccination",
                "chief_complaint": "School immunization requirements",
                "doctor": "Dr. Johnson",
                "diagnosis": "Vaccinations up to date",
                "notes": "Administered TDaP booster. No adverse reactions.",
                "date": datetime.now() - timedelta(days=60),
                "clinic_hospital": "Pediatric Clinic",
            },
            {
                "family_member": family_members[2],  # Michael
                "appointment_type": "Allergy Testing",
                "chief_complaint": "Suspected food allergies",
                "doctor": "Dr. Wilson",
                "diagnosis": "Tree nut allergy confirmed",
                "prescription": "EpiPen prescribed for emergency use",
                "notes": "Avoid all tree nuts. Carry emergency medication at all times.",
                "date": datetime.now() - timedelta(days=90),
                "clinic_hospital": "Children's Allergy Center",
            },
        ]

        for record_data in health_records_data:
            record = HealthRecord(
                user_id=user.id,
                family_member_id=record_data["family_member"].id,
                appointment_type=record_data["appointment_type"],
                chief_complaint=record_data["chief_complaint"],
                doctor=record_data["doctor"],
                diagnosis=record_data.get("diagnosis"),
                prescription=record_data.get("prescription"),
                notes=record_data["notes"],
                date=record_data["date"],
                clinic_hospital=record_data["clinic_hospital"],
            )
            db.session.add(record)

        db.session.commit()
        print("✅ Created sample health records")

        # Create sample appointments
        appointments_data = [
            {
                "family_member": family_members[0],  # Jane
                "title": "Gynecologist Appointment",
                "purpose": "Annual gynecological checkup",
                "appointment_date": datetime.now() + timedelta(days=7),
                "doctor_name": "Dr. Brown",
                "clinic_hospital": "Women's Health Center",
                "status": "scheduled",
            },
            {
                "family_member": family_members[1],  # Emma
                "title": "Dentist Appointment",
                "purpose": "Routine dental cleaning and checkup",
                "appointment_date": datetime.now() + timedelta(days=14),
                "doctor_name": "Dr. Davis",
                "clinic_hospital": "Family Dental Care",
                "status": "scheduled",
            },
            {
                "family_member": family_members[2],  # Michael
                "title": "Asthma Follow-up",
                "purpose": "Follow-up for asthma management",
                "appointment_date": datetime.now() + timedelta(days=21),
                "doctor_name": "Dr. Wilson",
                "clinic_hospital": "Children's Clinic",
                "status": "scheduled",
            },
        ]

        for appt_data in appointments_data:
            appointment = Appointment(
                user_id=user.id,
                family_member_id=appt_data["family_member"].id,
                title=appt_data["title"],
                purpose=appt_data["purpose"],
                appointment_date=appt_data["appointment_date"],
                doctor_name=appt_data["doctor_name"],
                clinic_hospital=appt_data["clinic_hospital"],
                status=appt_data["status"],
            )
            db.session.add(appointment)

        db.session.commit()
        print("✅ Created sample appointments")

        # Create sample current medications
        medications_data = [
            {
                "family_member": family_members[0],  # Jane
                "medicine": "Birth Control Pills",
                "strength": "0.02mg/0.1mg",
                "evening": "1 tablet",
                "duration": "Ongoing",
                "notes": "Take at the same time each day",
            },
            {
                "family_member": family_members[1],  # Emma
                "medicine": "Vitamin D3",
                "strength": "1000 IU",
                "morning": "1 tablet",
                "duration": "Ongoing",
                "notes": "Take with breakfast",
            },
            {
                "family_member": family_members[2],  # Michael
                "medicine": "Albuterol Inhaler",
                "strength": "90 mcg/dose",
                "duration": "As needed",
                "notes": "2 puffs as needed for asthma symptoms or before exercise",
            },
        ]

        for med_data in medications_data:
            medication = CurrentMedication(
                family_member_id=med_data["family_member"].id,
                medicine=med_data["medicine"],
                strength=med_data["strength"],
                morning=med_data.get("morning"),
                noon=med_data.get("noon"),
                evening=med_data.get("evening"),
                bedtime=med_data.get("bedtime"),
                duration=med_data["duration"],
                notes=med_data["notes"],
            )
            db.session.add(medication)

        db.session.commit()
        print("✅ Created sample medications")

        print("\n🎉 Database initialized and sample data created successfully!")
        print("Demo login credentials:")
        print("  Email: demo@example.com")
        print("  Password: demo123")


def main():
    """Main function to setup the database and create sample data."""
    print("🏥 PHRM Database Setup")
    print("=" * 50)

    try:
        init_and_seed_database()
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run: python run_family_health.py")
        print("2. Open: http://localhost:5000")
        print("3. Login: demo@example.com / demo123")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback

        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()

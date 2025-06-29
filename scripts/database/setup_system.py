#!/usr/bin/env python3
"""
PHRM Comprehensive Setup Script

This script provides a unified setup process for the Personal Health Records Manager,
combining database initialization, admin user setup, and sample data creation.
"""

import os
import sys
from datetime import date, datetime, timedelta

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app
from app.models import (
    Appointment, CurrentMedication, FamilyMember, HealthRecord, User, db
)


class PHRMSetup:
    """Comprehensive setup manager for PHRM system"""
    
    def __init__(self):
        """Initialize setup manager"""
        self.app = create_app()
        self.setup_steps = []
        
    def log_step(self, message):
        """Log a setup step"""
        print(f"✅ {message}")
        self.setup_steps.append(message)
    
    def log_warning(self, message):
        """Log a warning"""
        print(f"⚠️  {message}")
        
    def log_error(self, message):
        """Log an error"""
        print(f"❌ {message}")
    
    def setup_database(self, force_recreate=False):
        """Initialize database tables"""
        with self.app.app_context():
            try:
                if force_recreate:
                    db.drop_all()
                    self.log_step("Dropped existing database tables")
                
                db.create_all()
                self.log_step("Created database tables")
                return True
            except Exception as e:
                self.log_error(f"Database setup failed: {e}")
                return False
    
    def setup_admin_user(self, admin_email="admin@phrm.local", admin_password="admin123"):
        """Create or update admin user"""
        with self.app.app_context():
            try:
                # Check for existing admin user
                admin_user = User.query.filter_by(username='Admin').first()
                
                if admin_user:
                    # Update existing admin
                    admin_user.is_admin = True
                    admin_user.is_active = True
                    if admin_user.email != admin_email:
                        admin_user.email = admin_email
                    admin_user.set_password(admin_password)
                    self.log_step(f"Updated existing admin user: {admin_user.username}")
                else:
                    # Create new admin user
                    admin_user = User(
                        username='Admin',
                        email=admin_email,
                        first_name='System',
                        last_name='Administrator',
                        is_admin=True,
                        is_active=True,
                        date_of_birth=date(1990, 1, 1)  # Default date
                    )
                    admin_user.set_password(admin_password)
                    db.session.add(admin_user)
                    self.log_step(f"Created new admin user: {admin_user.username}")
                
                db.session.commit()
                self.log_step(f"Admin login: {admin_email} / {admin_password}")
                return True
            except Exception as e:
                self.log_error(f"Admin user setup failed: {e}")
                return False
    
    def setup_demo_user(self, demo_email="demo@example.com", demo_password="demo123"):
        """Create or update demo user with sample data"""
        with self.app.app_context():
            try:
                # Check for existing demo user
                demo_user = User.query.filter_by(email=demo_email).first()
                
                if demo_user:
                    self.log_step(f"Demo user already exists: {demo_user.username}")
                else:
                    # Create demo user
                    demo_user = User(
                        username='DemoUser',
                        email=demo_email,
                        first_name='John',
                        last_name='Doe',
                        date_of_birth=date(1980, 5, 15),
                        is_active=True,
                        is_admin=False
                    )
                    demo_user.set_password(demo_password)
                    db.session.add(demo_user)
                    db.session.commit()
                    self.log_step(f"Created demo user: {demo_user.username}")
                
                # Create family members for demo user
                self._create_demo_family_members(demo_user)
                
                self.log_step(f"Demo login: {demo_email} / {demo_password}")
                return True
            except Exception as e:
                self.log_error(f"Demo user setup failed: {e}")
                return False
    
    def _create_demo_family_members(self, user):
        """Create sample family members for demo user"""
        family_members_data = [
            {
                "name": "Meeran Esmail",
                "relationship": "Self",
                "date_of_birth": date(1985, 3, 15),
                "gender": "Male",
                "blood_type": "O+",
                "height": 175.0,
                "weight": 70.0,
                "allergies": "None known",
                "chronic_conditions": "None",
                "emergency_contact": "Jane Doe - 555-1234"
            },
            {
                "name": "Jane Doe",
                "relationship": "Spouse",
                "date_of_birth": date(1985, 8, 22),
                "gender": "Female",
                "blood_type": "A+",
                "height": 165.0,
                "weight": 65.0,
                "allergies": "Penicillin",
                "chronic_conditions": "None",
                "emergency_contact": "Meeran Esmail - 555-5678"
            },
            {
                "name": "Emma Doe",
                "relationship": "Daughter",
                "date_of_birth": date(2010, 3, 10),
                "gender": "Female",
                "blood_type": "O+",
                "height": 140.0,
                "weight": 35.0,
                "allergies": "None known",
                "chronic_conditions": "None",
                "emergency_contact": "Jane Doe - 555-1234"
            }
        ]
        
        created_members = []
        for member_data in family_members_data:
            # Only create if doesn't exist
            existing = FamilyMember.query.filter_by(
                user_id=user.id,
                name=member_data["name"]
            ).first()
            
            if not existing:
                member = FamilyMember(user_id=user.id, **member_data)
                db.session.add(member)
                created_members.append(member)
        
        if created_members:
            db.session.commit()
            self.log_step(f"Created {len(created_members)} family members")
            
            # Add medications for Meeran Esmail
            meeran = next((m for m in created_members if m.name == "Meeran Esmail"), None)
            if meeran:
                self._create_demo_medications(meeran)
    
    def _create_demo_medications(self, family_member):
        """Create sample medications for demo family member"""
        medications_data = [
            {"medication_name": "Metformin", "dosage": "500mg", "frequency": "Twice daily", "prescribed_by": "Dr. Smith"},
            {"medication_name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily", "prescribed_by": "Dr. Johnson"},
            {"medication_name": "Atorvastatin", "dosage": "20mg", "frequency": "Once daily", "prescribed_by": "Dr. Smith"},
            {"medication_name": "Amlodipine", "dosage": "5mg", "frequency": "Once daily", "prescribed_by": "Dr. Johnson"},
            {"medication_name": "Omeprazole", "dosage": "20mg", "frequency": "Once daily", "prescribed_by": "Dr. Wilson"},
            {"medication_name": "Aspirin", "dosage": "81mg", "frequency": "Once daily", "prescribed_by": "Dr. Smith"},
            {"medication_name": "Vitamin D3", "dosage": "1000 IU", "frequency": "Once daily", "prescribed_by": "Dr. Wilson"},
            {"medication_name": "Multivitamin", "dosage": "1 tablet", "frequency": "Once daily", "prescribed_by": "Self"},
            {"medication_name": "Fish Oil", "dosage": "1000mg", "frequency": "Twice daily", "prescribed_by": "Self"},
            {"medication_name": "Probiotics", "dosage": "1 capsule", "frequency": "Once daily", "prescribed_by": "Self"},
            {"medication_name": "Magnesium", "dosage": "400mg", "frequency": "Once daily", "prescribed_by": "Dr. Wilson"},
            {"medication_name": "Coenzyme Q10", "dosage": "100mg", "frequency": "Once daily", "prescribed_by": "Self"},
            {"medication_name": "Turmeric", "dosage": "500mg", "frequency": "Twice daily", "prescribed_by": "Self"},
            {"medication_name": "Glucosamine", "dosage": "1500mg", "frequency": "Once daily", "prescribed_by": "Self"},
            {"medication_name": "Zinc", "dosage": "15mg", "frequency": "Once daily", "prescribed_by": "Dr. Wilson"}
        ]
        
        # Import the correct model
        from app.models import CurrentMedicationEntry
        
        created_meds = []
        for med_data in medications_data:
            # Only create if doesn't exist
            existing = CurrentMedicationEntry.query.filter_by(
                family_member_id=family_member.id,
                medication_name=med_data["medication_name"]
            ).first()
            
            if not existing:
                medication = CurrentMedicationEntry(
                    family_member_id=family_member.id,
                    start_date=date.today() - timedelta(days=30),
                    **med_data
                )
                db.session.add(medication)
                created_meds.append(medication)
        
        if created_meds:
            db.session.commit()
            self.log_step(f"Created {len(created_meds)} medications for {family_member.name}")
    
    def verify_setup(self):
        """Verify that setup was successful"""
        with self.app.app_context():
            try:
                # Check users
                users = User.query.all()
                admin_users = User.query.filter_by(is_admin=True).all()
                family_members = FamilyMember.query.all()
                
                print("\n" + "=" * 60)
                print("📋 SETUP VERIFICATION")
                print("=" * 60)
                print(f"✅ Total users: {len(users)}")
                print(f"✅ Admin users: {len(admin_users)}")
                print(f"✅ Family members: {len(family_members)}")
                
                # Check medications
                from app.models import CurrentMedicationEntry
                medications = CurrentMedicationEntry.query.all()
                print(f"✅ Medications: {len(medications)}")
                
                # Show login details
                print("\n🔑 LOGIN CREDENTIALS:")
                for user in users:
                    role = "Admin" if user.is_admin else "User"
                    print(f"   {role}: {user.email} (Check setup script for password)")
                
                print("\n🌐 ACCESS URLS:")
                print("   Main Dashboard: http://localhost:5010/dashboard")
                print("   Admin Dashboard: http://localhost:5010/auth/admin/dashboard")
                print("   Health Check: http://localhost:5010/api/health")
                
                return True
            except Exception as e:
                self.log_error(f"Setup verification failed: {e}")
                return False
    
    def run_full_setup(self, force_recreate=False):
        """Run complete setup process"""
        print("🚀 STARTING PHRM SYSTEM SETUP")
        print("=" * 60)
        
        # Step 1: Database setup
        if not self.setup_database(force_recreate):
            return False
        
        # Step 2: Admin user setup
        if not self.setup_admin_user():
            return False
        
        # Step 3: Demo user setup
        if not self.setup_demo_user():
            return False
        
        # Step 4: Verification
        if not self.verify_setup():
            return False
        
        print(f"\n🎉 SETUP COMPLETE! Completed {len(self.setup_steps)} steps successfully.")
        return True


def main():
    """Main entry point for setup script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PHRM System Setup')
    parser.add_argument('--force', action='store_true', help='Force recreate database')
    parser.add_argument('--admin-only', action='store_true', help='Setup admin user only')
    parser.add_argument('--verify-only', action='store_true', help='Verify setup only')
    
    args = parser.parse_args()
    
    setup = PHRMSetup()
    
    if args.verify_only:
        setup.verify_setup()
    elif args.admin_only:
        setup.setup_database()
        setup.setup_admin_user()
        setup.verify_setup()
    else:
        setup.run_full_setup(force_recreate=args.force)


if __name__ == "__main__":
    main()

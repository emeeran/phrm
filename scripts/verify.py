#!/usr/bin/env python3
"""
Verify PHRM installation and functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_installation():
    """Verify the PHRM installation is working correctly."""
    print("🔍 PHRM Installation Verification")
    print("=" * 50)

    try:
        # Test imports
        print("📦 Testing imports...")
        from app import create_app
        from app.models import (
            Appointment,
            CurrentMedication,
            FamilyMember,
            HealthRecord,
            User,
        )

        print("✅ All imports successful")

        # Test app creation
        print("🏗️ Testing app creation...")
        app = create_app()
        print("✅ App creation successful")

        # Test database connectivity
        print("🗄️ Testing database...")
        with app.app_context():
            user_count = User.query.count()
            member_count = FamilyMember.query.count()
            record_count = HealthRecord.query.count()
            appointment_count = Appointment.query.count()
            medication_count = CurrentMedication.query.count()

            print("✅ Database connectivity successful")
            print("   📊 Data Summary:")
            print(f"      Users: {user_count}")
            print(f"      Family Members: {member_count}")
            print(f"      Health Records: {record_count}")
            print(f"      Appointments: {appointment_count}")
            print(f"      Medications: {medication_count}")

        # Test routes
        print("🛣️ Testing routes...")
        route_count = len(list(app.url_map.iter_rules()))
        print(f"✅ {route_count} routes registered")

        print("\n🎉 All verification tests passed!")
        print("\n📋 Next Steps:")
        print("   1. Run: python start_phrm.py")
        print("   2. Open: http://localhost:5000")
        print("   3. Login: demo@example.com / [check DEMO_PASSWORD env var or use 'development_password']")

        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_installation()
    sys.exit(0 if success else 1)

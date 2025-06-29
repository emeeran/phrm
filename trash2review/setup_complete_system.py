#!/usr/bin/env python3
"""
Setup Complete Admin/User System
Creates proper admin and user accounts with full functionality separation.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app, db
from app.models import User

def setup_complete_system():
    """Setup complete admin/user system with known passwords"""
    app = create_app()
    
    with app.app_context():
        print("🔧 SETTING UP COMPLETE ADMIN/USER SYSTEM")
        print("=" * 50)
        
        # Ensure admin exists with correct settings
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            admin.email = 'emeeranjp@gmail.com'
            admin.username = 'Admin'
            admin.first_name = 'System'
            admin.last_name = 'Administrator'
            admin.set_password('admin123')
            admin.is_active = True
            print(f"✅ Admin user updated: {admin.email}")
        else:
            admin = User(
                username='Admin',
                email='emeeranjp@gmail.com',
                first_name='System',
                last_name='Administrator',
                is_admin=True,
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("✅ Admin user created")
        
        # Ensure regular user exists with known password
        user = User.query.filter_by(email='emeeran@hotmail.com').first()
        if user:
            user.username = 'Meeran'
            user.first_name = 'Meeran'
            user.last_name = 'Esmail'
            user.set_password('user123')
            user.is_admin = False
            user.is_active = True
            print(f"✅ Regular user updated: {user.email}")
        else:
            user = User(
                username='Meeran',
                email='emeeran@hotmail.com',
                first_name='Meeran',
                last_name='Esmail',
                is_admin=False,
                is_active=True
            )
            user.set_password('user123')
            db.session.add(user)
            print("✅ Regular user created")
        
        # Commit changes
        db.session.commit()
        
        print("\n🎯 SYSTEM CAPABILITIES:")
        print("\n🛡️  ADMIN CAPABILITIES:")
        print("   ✅ View all users in system")
        print("   ✅ Add/edit/delete any user")
        print("   ✅ View all family members across all users")
        print("   ✅ Add/edit/delete family members for any user")
        print("   ✅ View all medical records across all users")
        print("   ✅ Add/edit/delete medical records for any user")
        print("   ✅ View all medications across all users")
        print("   ✅ Manage system-wide settings")
        print("   ✅ Access admin dashboard with full system overview")
        
        print("\n👤 USER CAPABILITIES:")
        print("   ✅ View only their own profile")
        print("   ✅ Edit only their own profile")
        print("   ✅ View only their own family members")
        print("   ✅ Add/edit/delete only their own family members")
        print("   ✅ View only their own medical records")
        print("   ✅ Add/edit/delete only their own medical records")
        print("   ✅ View only their own medications")
        print("   ✅ Access user dashboard with personal overview")
        
        print("\n🔐 LOGIN CREDENTIALS:")
        print("   🛡️  Admin Login: http://localhost:5010/auth/admin/login")
        print("      Email: emeeranjp@gmail.com")
        print("      Password: admin123")
        print("\n   👤 User Login: http://localhost:5010/auth/login")
        print("      Email: emeeran@hotmail.com")
        print("      Password: user123")
        
        return True

if __name__ == "__main__":
    if setup_complete_system():
        print("\n✅ COMPLETE ADMIN/USER SYSTEM READY!")
    else:
        print("\n❌ SYSTEM SETUP FAILED!")
        sys.exit(1)

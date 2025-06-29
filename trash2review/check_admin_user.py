#!/usr/bin/env python3
"""
Check Admin User Details
Checks the current admin user details in the database.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app, db
from app.models import User

def check_admin_user():
    """Check admin user details"""
    app = create_app()
    
    with app.app_context():
        # Find admin user
        admin_user = User.query.filter_by(is_admin=True).first()
        
        if admin_user:
            print(f"🔑 Admin User Found:")
            print(f"   ID: {admin_user.id}")
            print(f"   Username: {admin_user.username}")
            print(f"   Email: {admin_user.email}")
            print(f"   Is Admin: {admin_user.is_admin}")
            print(f"   Is Active: {admin_user.is_active}")
            
            # Test password verification
            print(f"\n🔐 Testing Password:")
            test_passwords = ['admin123', 'admin', 'password', 'Admin123']
            
            for pwd in test_passwords:
                if admin_user.check_password(pwd):
                    print(f"   ✅ Password '{pwd}' works!")
                    return pwd
                else:
                    print(f"   ❌ Password '{pwd}' failed")
            
            print(f"\n⚠️  None of the test passwords worked!")
            return None
        else:
            print("❌ No admin user found!")
            return None

if __name__ == "__main__":
    pwd = check_admin_user()
    if pwd:
        print(f"\n✅ Use username 'Admin' with password '{pwd}' for admin login")
    else:
        print("\n❌ Admin login credentials unknown - need to reset admin user")

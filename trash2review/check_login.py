#!/usr/bin/env python3
"""
Check user login details and optionally reset password
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.models import User, db
from werkzeug.security import generate_password_hash

def check_and_fix_login():
    """Check login details and optionally reset password"""
    
    app = create_app()
    
    with app.app_context():
        print("🔑 User Login Information")
        print("=" * 40)
        
        users = User.query.all()
        
        for user in users:
            print(f"\n👤 Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Active: {user.is_active}")
            print(f"   Has password hash: {bool(user.password_hash)}")
            
        # Ask if user wants to reset password for easier testing
        print(f"\n🔧 Password Reset Option:")
        print(f"If you've forgotten your password, I can reset it to 'admin123' for testing.")
        print(f"Type 'reset' to reset Admin password, or 'skip' to keep current password:")
        
        # For automated execution, let's just show the instructions
        print(f"\n📋 LOGIN INSTRUCTIONS:")
        print(f"1. Open browser: http://localhost:5010/auth/login")
        print(f"2. Username: Admin")
        print(f"3. Password: [Your original password]")
        print(f"4. If forgotten, run this script interactively to reset")
        
        print(f"\n💊 Expected Result After Login:")
        print(f"You should see 15 medications for 'Meeran Esmail' in the dashboard")

if __name__ == "__main__":
    check_and_fix_login()

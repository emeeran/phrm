#!/usr/bin/env python3
"""
Reset Admin password to 'admin123' for easy testing
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.models import User, db
from werkzeug.security import generate_password_hash

def reset_admin_password():
    """Reset Admin password"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 Resetting Admin Password")
        print("=" * 40)
        
        admin_user = User.query.filter_by(username='Admin').first()
        
        if admin_user:
            # Reset password to 'admin123'
            admin_user.password_hash = generate_password_hash('admin123')
            db.session.commit()
            
            print("✅ Password reset successful!")
            print("📋 New Login Credentials:")
            print("   Username: Admin")
            print("   Password: admin123")
            print("")
            print("🌐 Now you can login at: http://localhost:5010/auth/login")
            print("💊 After login, visit: http://localhost:5010/dashboard")
            print("   You should see all 15 medications for Meeran Esmail")
            
        else:
            print("❌ Admin user not found!")

if __name__ == "__main__":
    reset_admin_password()

#!/usr/bin/env python3
"""
Set up admin user and convert existing users to regular users
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.models import User, db
from werkzeug.security import generate_password_hash

def setup_admin_user():
    """Set up admin user and configure user roles"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 Setting up Admin User and User Roles")
        print("=" * 50)
        
        # Find existing Admin user
        admin_user = User.query.filter_by(username='Admin').first()
        
        if admin_user:
            # Set admin flag
            admin_user.is_admin = True
            print(f"✅ Set {admin_user.username} as admin")
            
            # Set a default password if needed
            if admin_user.email == 'emeeranjp@gmail.com':
                # Set a default admin password
                admin_user.password_hash = generate_password_hash('admin123')
                print(f"✅ Set default password for admin: admin123")
        else:
            # Create new admin user
            admin_user = User(
                username='Admin',
                email='admin@phrm.local',
                password_hash=generate_password_hash('admin123'),
                first_name='System',
                last_name='Administrator', 
                is_admin=True,
                is_active=True
            )
            db.session.add(admin_user)
            print(f"✅ Created new admin user: Admin (password: admin123)")
        
        # Make sure all other users are not admin
        other_users = User.query.filter(User.username != 'Admin').all()
        for user in other_users:
            if user.is_admin:
                user.is_admin = False
                print(f"✅ Removed admin privileges from {user.username}")
            else:
                print(f"✅ {user.username} is already a regular user")
        
        # Commit changes
        db.session.commit()
        
        print(f"\n📋 Final User Status:")
        all_users = User.query.all()
        for user in all_users:
            role = "Admin" if user.is_admin else "User"
            family_count = len(user.family_members)
            print(f"   {user.username} ({user.email}) - {role} - {family_count} family members")
        
        print(f"\n🔑 Login Information:")
        print(f"Admin Login: http://localhost:5010/auth/admin/login")
        print(f"  Username: Admin")
        print(f"  Password: admin123")
        print(f"")
        print(f"User Login: http://localhost:5010/auth/login")
        for user in other_users:
            print(f"  Username: {user.username} (email: {user.email})")
        
        print(f"\n✅ Setup complete!")

if __name__ == "__main__":
    setup_admin_user()

#!/usr/bin/env python3
"""
Comprehensive verification of the admin/user separation system
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.models import User, FamilyMember, CurrentMedication

def verify_admin_user_system():
    """Verify the admin/user system is working correctly"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 ADMIN/USER SYSTEM VERIFICATION")
        print("=" * 60)
        
        # Check user roles
        print("\n1️⃣ User Roles:")
        print("-" * 30)
        
        all_users = User.query.all()
        admin_users = []
        regular_users = []
        
        for user in all_users:
            if user.is_admin:
                admin_users.append(user)
                print(f"   🔑 ADMIN: {user.username} ({user.email})")
            else:
                regular_users.append(user)
                print(f"   👤 USER:  {user.username} ({user.email})")
        
        print(f"\n   Total: {len(admin_users)} admin(s), {len(regular_users)} user(s)")
        
        # Check family member assignments
        print("\n2️⃣ Family Member Assignments:")
        print("-" * 40)
        
        for user in all_users:
            family_count = len(user.family_members)
            print(f"   {user.username}: {family_count} family members")
            
            for member in user.family_members:
                med_count = len(member.current_medication_entries) if hasattr(member, 'current_medication_entries') else 0
                print(f"     - {member.first_name} {member.last_name}: {med_count} medications")
        
        # Check medication data
        print("\n3️⃣ Medication Data:")
        print("-" * 25)
        
        total_medications = CurrentMedication.query.count()
        print(f"   Total medications in database: {total_medications}")
        
        for user in regular_users:
            user_med_count = 0
            for member in user.family_members:
                if hasattr(member, 'current_medication_entries'):
                    user_med_count += len(member.current_medication_entries)
            print(f"   {user.username} manages {user_med_count} medications")
        
        # Check admin isolation
        print("\n4️⃣ Admin Isolation Check:")
        print("-" * 30)
        
        for admin in admin_users:
            if admin.family_members:
                print(f"   ⚠️  ISSUE: Admin {admin.username} has {len(admin.family_members)} family members")
            else:
                print(f"   ✅ Admin {admin.username} correctly has no family members")
        
        # System status
        print("\n5️⃣ System Status:")
        print("-" * 25)
        
        issues = []
        
        if len(admin_users) == 0:
            issues.append("No admin users found")
        elif len(admin_users) > 1:
            issues.append(f"Multiple admin users found ({len(admin_users)})")
        
        if len(regular_users) == 0:
            issues.append("No regular users found")
        
        if any(admin.family_members for admin in admin_users):
            issues.append("Admin users have family members")
        
        if total_medications == 0:
            issues.append("No medications in database")
        
        if issues:
            print("   ❌ Issues found:")
            for issue in issues:
                print(f"      - {issue}")
        else:
            print("   ✅ All checks passed!")
        
        # Login instructions
        print("\n6️⃣ Login Instructions:")
        print("-" * 30)
        
        print("   Admin Login: http://localhost:5010/auth/admin/login")
        for admin in admin_users:
            print(f"     Username: {admin.username}")
            print(f"     Password: admin123")
        
        print("\n   User Login: http://localhost:5010/auth/login")
        for user in regular_users:
            print(f"     Username: {user.username}")
            print(f"     Email: {user.email}")
        
        print(f"\n✅ Verification complete!")
        
        # Expected behavior
        print(f"\n7️⃣ Expected Behavior:")
        print("-" * 30)
        print("   ✅ Admin can:")
        print("      - View all users and family members")
        print("      - Add/edit/delete any family member")
        print("      - See all medications across all users")
        print("      - Manage the entire system")
        print("\n   ✅ Users can:")
        print("      - Only see their own family members")
        print("      - Only see medications for their family members")
        print("      - Add/edit/delete their own family members")
        print("      - View their own dashboard")
        print("\n   🚫 Admins cannot:")
        print("      - Be assigned as family members")
        print("      - Have medications tracked for themselves")
        print("      - Access user-specific views")

if __name__ == "__main__":
    verify_admin_user_system()

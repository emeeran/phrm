#!/usr/bin/env python3
"""
Move family members from Admin user to regular users and clean up admin associations
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.models import User, FamilyMember, db

def migrate_admin_family_members():
    """Move family members from admin to regular user"""
    
    app = create_app()
    
    with app.app_context():
        print("🔄 Migrating Family Members from Admin")
        print("=" * 50)
        
        # Find admin user
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            print("❌ No admin user found")
            return
        
        print(f"👤 Admin user: {admin_user.username}")
        print(f"   Family members: {len(admin_user.family_members)}")
        
        # Find regular users
        regular_users = User.query.filter_by(is_admin=False).all()
        if not regular_users:
            print("❌ No regular users found")
            return
        
        # Choose the first regular user or create one if needed
        target_user = regular_users[0]
        print(f"🎯 Target user: {target_user.username}")
        
        # Move family members from admin to regular user
        moved_count = 0
        for family_member in list(admin_user.family_members):
            # Remove from admin user
            admin_user.family_members.remove(family_member)
            
            # Add to regular user (only if not already there)
            if family_member not in target_user.family_members:
                target_user.family_members.append(family_member)
                moved_count += 1
                print(f"   ✅ Moved: {family_member.first_name} {family_member.last_name}")
        
        db.session.commit()
        
        print(f"\n📊 Migration Summary:")
        print(f"   Moved {moved_count} family members")
        print(f"   Admin now has {len(admin_user.family_members)} family members")
        print(f"   {target_user.username} now has {len(target_user.family_members)} family members")
        
        # Show medications count
        total_medications = 0
        for member in target_user.family_members:
            if hasattr(member, 'current_medication_entries'):
                med_count = len(member.current_medication_entries)
                total_medications += med_count
                print(f"   - {member.first_name} {member.last_name}: {med_count} medications")
        
        print(f"\n💊 Total medications now under {target_user.username}: {total_medications}")
        print(f"✅ Migration complete!")

if __name__ == "__main__":
    migrate_admin_family_members()

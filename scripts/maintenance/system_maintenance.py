#!/usr/bin/env python3
"""
PHRM Maintenance Utilities

Consolidated maintenance tasks for the PHRM system including:
- Password reset functionality
- User management
- Database maintenance
- System verification
"""

import os
import sys
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app
from app.models import User, FamilyMember, CurrentMedicationEntry, db


class PHRMMaintenance:
    """Maintenance utilities for PHRM system"""
    
    def __init__(self):
        """Initialize maintenance utility"""
        self.app = create_app()
    
    def reset_user_password(self, username_or_email, new_password):
        """Reset password for a specific user"""
        with self.app.app_context():
            try:
                # Find user by username or email
                user = User.query.filter(
                    (User.username == username_or_email) |
                    (User.email == username_or_email)
                ).first()
                
                if not user:
                    print(f"❌ User not found: {username_or_email}")
                    return False
                
                # Reset password
                user.set_password(new_password)
                db.session.commit()
                
                print(f"✅ Password reset successful for {user.username}")
                print(f"   Email: {user.email}")
                print(f"   New password: {new_password}")
                return True
                
            except Exception as e:
                print(f"❌ Password reset failed: {e}")
                return False
    
    def list_all_users(self):
        """List all users in the system"""
        with self.app.app_context():
            try:
                users = User.query.all()
                
                print("\n👥 SYSTEM USERS")
                print("=" * 50)
                
                for user in users:
                    role = "Admin" if user.is_admin else "User"
                    status = "Active" if user.is_active else "Inactive"
                    family_count = len(user.family_members)
                    
                    print(f"   {role} - {user.username}")
                    print(f"      Email: {user.email}")
                    print(f"      Status: {status}")
                    print(f"      Family Members: {family_count}")
                    print()
                
                return True
            except Exception as e:
                print(f"❌ Failed to list users: {e}")
                return False
    
    def check_data_integrity(self):
        """Check system data integrity"""
        with self.app.app_context():
            try:
                print("\n🔍 DATA INTEGRITY CHECK")
                print("=" * 50)
                
                # Check users
                users = User.query.all()
                print(f"✅ Users: {len(users)}")
                
                # Check family members
                family_members = FamilyMember.query.all()
                print(f"✅ Family Members: {len(family_members)}")
                
                # Check medications
                medications = CurrentMedicationEntry.query.all()
                print(f"✅ Medications: {len(medications)}")
                
                # Check for orphaned records
                orphaned_family = FamilyMember.query.filter(
                    ~FamilyMember.user_id.in_([u.id for u in users])
                ).all()
                
                if orphaned_family:
                    print(f"⚠️  Found {len(orphaned_family)} orphaned family members")
                else:
                    print("✅ No orphaned family member records")
                
                # Check for orphaned medications
                family_ids = [fm.id for fm in family_members]
                orphaned_meds = CurrentMedicationEntry.query.filter(
                    ~CurrentMedicationEntry.family_member_id.in_(family_ids)
                ).all()
                
                if orphaned_meds:
                    print(f"⚠️  Found {len(orphaned_meds)} orphaned medication records")
                else:
                    print("✅ No orphaned medication records")
                
                return True
            except Exception as e:
                print(f"❌ Data integrity check failed: {e}")
                return False
    
    def backup_database(self):
        """Create a database backup"""
        try:
            import shutil
            
            # Define backup paths
            db_path = 'instance/phrm.db'
            backup_dir = 'instance/backups'
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f'{backup_dir}/phrm_backup_{timestamp}.db'
            
            # Create backup directory if it doesn't exist
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copy database file
            shutil.copy2(db_path, backup_path)
            
            print(f"✅ Database backup created: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"❌ Database backup failed: {e}")
            return None
    
    def show_system_info(self):
        """Show system information"""
        with self.app.app_context():
            try:
                print("\n🏥 PHRM SYSTEM INFORMATION")
                print("=" * 50)
                
                # Basic info
                users = User.query.all()
                admins = User.query.filter_by(is_admin=True).all()
                family_members = FamilyMember.query.all()
                medications = CurrentMedicationEntry.query.all()
                
                print(f"Total Users: {len(users)}")
                print(f"Admin Users: {len(admins)}")
                print(f"Family Members: {len(family_members)}")
                print(f"Medication Entries: {len(medications)}")
                
                # Configuration info
                print(f"\nConfiguration:")
                print(f"  Debug Mode: {self.app.debug}")
                print(f"  Database URI: {self.app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')}")
                print(f"  Secret Key: {'Set' if 'SECRET_KEY' in self.app.config else 'Not set'}")
                
                # File system info
                print(f"\nFile System:")
                print(f"  Instance folder: {self.app.instance_path}")
                print(f"  Static folder: {self.app.static_folder}")
                print(f"  Template folder: {self.app.template_folder}")
                
                return True
            except Exception as e:
                print(f"❌ Failed to get system info: {e}")
                return False


def main():
    """Main entry point for maintenance script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PHRM Maintenance Utilities')
    parser.add_argument('--reset-password', nargs=2, metavar=('USER', 'PASSWORD'),
                       help='Reset password for user (username/email, new_password)')
    parser.add_argument('--list-users', action='store_true',
                       help='List all users in the system')
    parser.add_argument('--check-integrity', action='store_true',
                       help='Check data integrity')
    parser.add_argument('--backup', action='store_true',
                       help='Create database backup')
    parser.add_argument('--system-info', action='store_true',
                       help='Show system information')
    
    args = parser.parse_args()
    
    maintenance = PHRMMaintenance()
    
    if args.reset_password:
        username, password = args.reset_password
        maintenance.reset_user_password(username, password)
    elif args.list_users:
        maintenance.list_all_users()
    elif args.check_integrity:
        maintenance.check_data_integrity()
    elif args.backup:
        maintenance.backup_database()
    elif args.system_info:
        maintenance.show_system_info()
    else:
        # Interactive mode
        print("🔧 PHRM MAINTENANCE UTILITIES")
        print("=" * 40)
        print("Available operations:")
        print("1. List all users")
        print("2. Reset user password")
        print("3. Check data integrity")
        print("4. Create database backup")
        print("5. Show system information")
        
        try:
            choice = input("\nSelect operation (1-5): ").strip()
            
            if choice == '1':
                maintenance.list_all_users()
            elif choice == '2':
                user = input("Enter username or email: ").strip()
                password = input("Enter new password: ").strip()
                maintenance.reset_user_password(user, password)
            elif choice == '3':
                maintenance.check_data_integrity()
            elif choice == '4':
                maintenance.backup_database()
            elif choice == '5':
                maintenance.show_system_info()
            else:
                print("Invalid choice")
        except KeyboardInterrupt:
            print("\nOperation cancelled")


if __name__ == "__main__":
    main()

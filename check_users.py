#!/usr/bin/env python3
"""
Script to check the number of users in the PHRM database.
Shows multiple ways to count and view user information.
"""

import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app import create_app
from app.models import User


def count_users():
    """Count users using different methods"""

    # Create app context
    app = create_app()

    with app.app_context():
        print("=== PHRM Database User Statistics ===\n")

        # Method 1: Simple count
        total_users = User.query.count()
        print(f"📊 Total Users: {total_users}")

        # Method 2: Count active users
        active_users = User.query.filter_by(is_active=True).count()
        print(f"✅ Active Users: {active_users}")

        # Method 3: Count inactive users
        inactive_users = User.query.filter_by(is_active=False).count()
        print(f"❌ Inactive Users: {inactive_users}")

        # Method 4: Count admin users
        admin_users = User.query.filter_by(is_admin=True).count()
        print(f"👑 Admin Users: {admin_users}")

        print("\n" + "=" * 50)

        # Show detailed user list if there are users
        if total_users > 0:
            print(f"\n📝 User Details ({total_users} users):")
            print("-" * 80)
            users = User.query.all()

            for i, user in enumerate(users, 1):
                status = "Active" if user.is_active else "Inactive"
                role = "Admin" if user.is_admin else "User"
                created = (
                    user.created_at.strftime("%Y-%m-%d %H:%M")
                    if user.created_at
                    else "Unknown"
                )

                print(
                    f"{i:2}. {user.email:30} | {user.username:15} | {status:8} | {role:5} | Created: {created}"
                )

                # Show full name if available
                if user.first_name or user.last_name:
                    full_name = (
                        f"{user.first_name or ''} {user.last_name or ''}".strip()
                    )
                    print(f"    Name: {full_name}")

                # Show date of birth if available
                if user.date_of_birth:
                    print(f"    DOB: {user.date_of_birth}")

                print()
        else:
            print("\n📭 No users found in the database.")
            print("\n💡 You can create a user using:")
            print("   - The web interface at http://127.0.0.1:5000/auth/register")
            print("   - Using Flask shell commands")


if __name__ == "__main__":
    count_users()

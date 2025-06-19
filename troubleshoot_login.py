#!/usr/bin/env python3
"""
Comprehensive login troubleshooting script for PHRM
"""

import sys
from app.models import User, db
from app import create_app

def check_database():
    """Check database connectivity and user data"""
    print("📋 Checking database...")
    try:
        app = create_app()
        with app.app_context():
            users = User.query.all()
            print(f"   ✅ Database connected")
            print(f"   ✅ Found {len(users)} user(s)")
            
            for user in users:
                print(f"      - {user.email} (username: {user.username})")
            return True
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False

def create_test_user():
    """Create a test user if none exists"""
    print("👤 Creating/updating test user...")
    try:
        app = create_app()
        with app.app_context():
            # Check if demo user exists
            user = User.query.filter_by(email='demo@example.com').first()
            
            if not user:
                # Create new demo user
                from datetime import date
                user = User(
                    username='demouser',
                    email='demo@example.com',
                    first_name='Demo',
                    last_name='User',
                    date_of_birth=date(1990, 1, 1)
                )
                user.set_password('demo123')
                db.session.add(user)
                db.session.commit()
                print("   ✅ Created new demo user")
            else:
                # Update existing user password
                user.set_password('demo123')
                db.session.commit()
                print("   ✅ Updated existing demo user password")
            
            print(f"      Email: {user.email}")
            print(f"      Password: demo123")
            return True
    except Exception as e:
        print(f"   ❌ User creation error: {e}")
        return False

def test_authentication():
    """Test authentication logic"""
    print("🔐 Testing authentication...")
    try:
        app = create_app()
        with app.app_context():
            user = User.query.filter_by(email='demo@example.com').first()
            if not user:
                print("   ❌ Demo user not found")
                return False
            
            # Test correct password
            if user.check_password('demo123'):
                print("   ✅ Password verification works")
            else:
                print("   ❌ Password verification failed")
                return False
            
            # Test incorrect password
            if not user.check_password('wrongpassword'):
                print("   ✅ Incorrect password properly rejected")
            else:
                print("   ❌ Security issue: incorrect password accepted")
                return False
            
            return True
    except Exception as e:
        print(f"   ❌ Authentication test error: {e}")
        return False

def check_server_status():
    """Check if server is running"""
    print("🌐 Checking server status...")
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 5000))
        sock.close()
        
        if result == 0:
            print("   ✅ Server is running on localhost:5000")
            return True
        else:
            print("   ❌ Server is not running on localhost:5000")
            return False
    except Exception as e:
        print(f"   ❌ Server check error: {e}")
        return False

def main():
    print("🔍 PHRM Login Troubleshooter")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Run all checks
    checks = [
        check_database,
        create_test_user,
        test_authentication,
        check_server_status
    ]
    
    for check in checks:
        if not check():
            all_checks_passed = False
        print()
    
    # Summary
    print("📊 SUMMARY")
    print("=" * 50)
    
    if all_checks_passed:
        print("🎉 All checks passed! You should be able to login with:")
        print("   URL: http://localhost:5000/auth/login")
        print("   Email: demo@example.com")
        print("   Password: demo123")
        print()
        print("💡 If you still can't login, check:")
        print("   1. Browser console for JavaScript errors")
        print("   2. Browser network tab for failed requests")
        print("   3. Flask application logs for error messages")
        print("   4. Clear browser cache and cookies")
    else:
        print("❌ Some checks failed. Please address the issues above.")
    
    return all_checks_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

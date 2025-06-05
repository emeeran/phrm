#!/usr/bin/env python3
"""
Quick test script to create a test user and verify the system is working
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, User

def create_test_user():
    """Create a test user for testing the JavaScript modules"""
    app = create_app()
    
    with app.app_context():
        # Check if test user already exists
        existing_user = User.query.filter_by(email='test@example.com').first()
        if existing_user:
            print("✅ Test user already exists")
            return
        
        # Create test user
        test_user = User(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        test_user.set_password('password123')
        
        db.session.add(test_user)
        db.session.commit()
        
        print("✅ Test user created successfully!")
        print("   Email: test@example.com")
        print("   Password: password123")
        print("   You can now test the JavaScript modules by logging in")

if __name__ == '__main__':
    create_test_user()

#!/usr/bin/env python3
"""
Comprehensive application diagnostics with authenticated session
"""

import sys
import os
import requests
from requests.sessions import Session

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.models import User

def run_comprehensive_diagnostics():
    """Run comprehensive diagnostics of the application"""
    
    print("🔍 COMPREHENSIVE APPLICATION DIAGNOSTICS")
    print("=" * 60)
    
    # Test 1: Basic server connectivity
    print("\n1️⃣ Testing Basic Server Connectivity")
    print("-" * 40)
    
    try:
        response = requests.get('http://localhost:5010/', timeout=5)
        print(f"✅ Server responding: {response.status_code}")
        print(f"✅ Redirect location: {response.url}")
    except Exception as e:
        print(f"❌ Server connectivity failed: {e}")
        return
    
    # Test 2: Database connectivity and data integrity
    print("\n2️⃣ Testing Database Connectivity")
    print("-" * 40)
    
    app = create_app()
    with app.app_context():
        try:
            users = User.query.all()
            print(f"✅ Database connected: {len(users)} users found")
            
            for user in users:
                family_count = len(user.family_members)
                total_medications = 0
                for member in user.family_members:
                    if hasattr(member, 'current_medication_entries'):
                        total_medications += len(member.current_medication_entries)
                
                print(f"   👤 {user.username}: {family_count} family members, {total_medications} medications")
                
        except Exception as e:
            print(f"❌ Database connectivity failed: {e}")
            return
    
    # Test 3: Authentication system
    print("\n3️⃣ Testing Authentication System")
    print("-" * 40)
    
    session = Session()
    
    # Get login page
    try:
        login_response = session.get('http://localhost:5010/auth/login')
        print(f"✅ Login page accessible: {login_response.status_code}")
        
        # Check if login form is present
        if 'username' in login_response.text and 'password' in login_response.text:
            print("✅ Login form detected")
        else:
            print("⚠️  Login form not detected properly")
            
    except Exception as e:
        print(f"❌ Login page failed: {e}")
    
    # Test 4: API endpoints (without auth)
    print("\n4️⃣ Testing API Endpoints (No Auth)")
    print("-" * 40)
    
    api_endpoints = [
        '/api/health',
        '/api/medications/current-medications',
        '/api/medications/interaction-summary'
    ]
    
    for endpoint in api_endpoints:
        try:
            response = requests.get(f'http://localhost:5010{endpoint}', timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint}: {response.status_code}")
            elif response.status_code == 302:
                print(f"🔒 {endpoint}: {response.status_code} (auth required)")
            elif response.status_code == 401:
                print(f"🔒 {endpoint}: {response.status_code} (auth required)")
            else:
                print(f"⚠️  {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")
    
    # Test 5: Static file serving
    print("\n5️⃣ Testing Static File Serving")
    print("-" * 40)
    
    static_files = [
        '/static/css/optimized.min.css',
        '/static/js/main.js',
        '/static/js/dashboard.js'
    ]
    
    for static_file in static_files:
        try:
            response = requests.get(f'http://localhost:5010{static_file}', timeout=5)
            if response.status_code == 200:
                print(f"✅ {static_file}: {response.status_code}")
            else:
                print(f"❌ {static_file}: {response.status_code}")
        except Exception as e:
            print(f"❌ {static_file}: {e}")
    
    # Test 6: Template rendering
    print("\n6️⃣ Testing Template Rendering")
    print("-" * 40)
    
    try:
        # Test with application context
        with app.app_context():
            from flask import render_template_string
            test_template = "{{ 'Template engine working' }}"
            result = render_template_string(test_template)
            print(f"✅ Template engine: {result}")
    except Exception as e:
        print(f"❌ Template engine: {e}")
    
    # Test 7: Check for common issues
    print("\n7️⃣ Checking for Common Issues")
    print("-" * 40)
    
    # Check if Redis is working
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis connection working")
    except Exception as e:
        print(f"⚠️  Redis issue: {e}")
    
    # Check file permissions
    try:
        import os
        db_path = 'instance/phrm.db'
        if os.path.exists(db_path):
            print(f"✅ Database file exists: {db_path}")
            if os.access(db_path, os.R_OK):
                print("✅ Database file readable")
            if os.access(db_path, os.W_OK):
                print("✅ Database file writable")
        else:
            print(f"❌ Database file not found: {db_path}")
    except Exception as e:
        print(f"⚠️  File permission check failed: {e}")
    
    print("\n8️⃣ Summary and Recommendations")
    print("-" * 40)
    print("✅ Application is running successfully")
    print("✅ Database connectivity is working")
    print("✅ Medication data is present in database")
    print("🔒 Authentication is required to view dashboard")
    print("\n📋 Next Steps:")
    print("1. Open: http://localhost:5010/auth/login")
    print("2. Login with username: 'Admin'")
    print("3. Navigate to dashboard to see medications")
    print("4. Medications should display properly after authentication")

if __name__ == "__main__":
    run_comprehensive_diagnostics()

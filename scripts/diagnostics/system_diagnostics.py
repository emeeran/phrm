#!/usr/bin/env python3
"""
PHRM System Diagnostics - Combined diagnostic tool for the PHRM system

This script performs comprehensive diagnostics on the Personal Health Record Manager system,
including server accessibility, database connectivity, authentication flow, API endpoints,
static files, and configuration checks.
"""

import sys
import os
import requests
from requests.sessions import Session
import time

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app
from app.models import User


class SystemDiagnostics:
    """Class to perform comprehensive diagnostics on the PHRM system"""
    
    def __init__(self, base_url="http://localhost:5010"):
        """Initialize diagnostic tool with configuration"""
        self.base_url = base_url
        self.app = create_app()
        self.session = Session()
        self.issues_found = []
        
    def run_all_tests(self):
        """Run all diagnostic tests and return results"""
        self.print_header()
        
        # Run tests in sequence, stopping on critical failures
        if not self.test_server_accessibility():
            return False
            
        self.test_database_connectivity()
        self.test_authentication()
        self.test_api_endpoints()
        self.test_static_files()
        self.test_templates()
        self.test_configuration()
        self.test_dependencies()
        
        self.print_summary()
        return len(self.issues_found) == 0

    def print_header(self):
        """Print diagnostic header"""
        print("\n" + "=" * 70)
        print("🏥 PHRM SYSTEM DIAGNOSTICS")
        print("=" * 70)
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base URL: {self.base_url}")
        print("-" * 70)
        
    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "=" * 70)
        print("📋 DIAGNOSTIC SUMMARY")
        print("=" * 70)
        
        if not self.issues_found:
            print("✅ All systems operational. No issues detected.")
        else:
            print(f"⚠️  {len(self.issues_found)} issue(s) found:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"{i}. {issue}")
            
        print("\n💊 NEXT STEPS:")
        print("1. For medication access: http://localhost:5010/dashboard")
        print("2. For user management: http://localhost:5010/auth/admin/dashboard")
        print("3. For API access: http://localhost:5010/api/health")
        print("=" * 70)
    
    def test_server_accessibility(self):
        """Test if the server is accessible"""
        print("\n1️⃣ Testing Server Accessibility")
        print("-" * 50)
        
        try:
            response = requests.get(f'{self.base_url}/', timeout=5)
            print(f"✅ Server responding: {response.status_code}")
            print(f"✅ Redirect location: {response.url}")
            return True
        except Exception as e:
            print(f"❌ Server not accessible: {e}")
            self.issues_found.append(f"Server accessibility: {e}")
            print("\n⚠️  CRITICAL ERROR: Server not accessible. Please check that:")
            print("   - The application is running (python start_phrm.py)")
            print("   - The port (5010) is not in use by another service")
            print("   - No firewall is blocking access to the port")
            return False
    
    def test_database_connectivity(self):
        """Test database connectivity and data integrity"""
        print("\n2️⃣ Testing Database Connectivity")
        print("-" * 50)
        
        try:
            with self.app.app_context():
                users = User.query.all()
                print(f"✅ Database accessible: {len(users)} users found")
                
                # Check each user's data integrity
                for user in users:
                    family_count = len(user.family_members)
                    total_meds = sum(len(fm.current_medication_entries) 
                                      for fm in user.family_members 
                                      if hasattr(fm, 'current_medication_entries'))
                    print(f"   👤 {user.username}: {family_count} family members, {total_meds} medications")
                
                return True
        except Exception as e:
            print(f"❌ Database error: {e}")
            self.issues_found.append(f"Database connectivity: {e}")
            return False
    
    def test_authentication(self):
        """Test authentication system"""
        print("\n3️⃣ Testing Authentication System")
        print("-" * 50)
        
        # Test login page access
        try:
            login_response = self.session.get(f'{self.base_url}/auth/login')
            print(f"✅ Login page accessible: {login_response.status_code}")
            
            # Check for CSRF protection
            if 'csrf_token' in login_response.text:
                print("✅ CSRF protection active")
            else:
                print("⚠️  No CSRF token found in login form")
                self.issues_found.append("CSRF protection not detected")
                
            # Check for login form elements
            form_elements = ['username', 'password', 'submit']
            missing_elements = [elem for elem in form_elements if elem not in login_response.text.lower()]
            
            if not missing_elements:
                print("✅ Login form contains all required elements")
            else:
                print(f"⚠️  Login form missing elements: {', '.join(missing_elements)}")
                self.issues_found.append(f"Login form incomplete: missing {', '.join(missing_elements)}")
                
            return True
        except Exception as e:
            print(f"❌ Authentication system error: {e}")
            self.issues_found.append(f"Authentication system: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n4️⃣ Testing API Endpoints")
        print("-" * 50)
        
        api_endpoints = [
            '/api/health',
            '/api/medications/current-medications',
            '/api/medications/interaction-summary',
            '/api/user/info',
            '/dashboard',
            '/records/dashboard'
        ]
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(f'{self.base_url}{endpoint}', allow_redirects=False, timeout=5)
                if response.status_code == 302:
                    print(f"✅ {endpoint}: Redirect to auth (expected)")
                elif response.status_code == 200:
                    print(f"✅ {endpoint}: Accessible")
                elif response.status_code == 401:
                    print(f"✅ {endpoint}: Auth required (expected)")
                else:
                    print(f"⚠️  {endpoint}: Unexpected status code {response.status_code}")
                    self.issues_found.append(f"API endpoint {endpoint}: Status code {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint}: Error - {e}")
                self.issues_found.append(f"API endpoint {endpoint}: {e}")
    
    def test_static_files(self):
        """Test static file serving"""
        print("\n5️⃣ Testing Static File Serving")
        print("-" * 50)
        
        static_files = [
            '/static/css/optimized.min.css',
            '/static/js/main.js',
            '/static/js/dashboard.js',
            '/static/img/logo.png'
        ]
        
        for static_file in static_files:
            try:
                response = requests.get(f'{self.base_url}{static_file}', timeout=5)
                if response.status_code == 200:
                    file_size = len(response.content)
                    print(f"✅ {static_file}: {response.status_code} ({file_size} bytes)")
                else:
                    print(f"❌ {static_file}: {response.status_code}")
                    self.issues_found.append(f"Static file {static_file}: Status code {response.status_code}")
            except Exception as e:
                print(f"❌ {static_file}: {e}")
                self.issues_found.append(f"Static file {static_file}: {e}")
        
        # Also check directories
        base_path = os.path.join(os.path.dirname(__file__), '../..', 'app', 'static')
        static_dirs = ['css', 'js', 'img']
        for directory in static_dirs:
            path = os.path.join(base_path, directory)
            if os.path.exists(path):
                file_count = len(os.listdir(path)) if os.path.isdir(path) else 0
                print(f"✅ Static directory '{directory}': {file_count} files")
            else:
                print(f"❌ Static directory '{directory}': Missing")
                self.issues_found.append(f"Static directory '{directory}' not found")
    
    def test_templates(self):
        """Test template files and rendering"""
        print("\n6️⃣ Testing Templates")
        print("-" * 50)
        
        template_files = [
            'app/templates/records/enhanced_dashboard.html',
            'app/templates/auth/login.html',
            'app/templates/base.html'
        ]
        
        base_path = os.path.join(os.path.dirname(__file__), '../..')
        for template in template_files:
            full_path = os.path.join(base_path, template)
            if os.path.exists(full_path):
                print(f"✅ {template}: Found")
            else:
                print(f"❌ {template}: Missing")
                self.issues_found.append(f"Template file {template} not found")
        
        # Test template rendering
        try:
            with self.app.app_context():
                from flask import render_template_string
                test_template = "{{ 'Template engine working' }}"
                result = render_template_string(test_template)
                print(f"✅ Template engine: {result}")
        except Exception as e:
            print(f"❌ Template engine: {e}")
            self.issues_found.append(f"Template rendering: {e}")
    
    def test_configuration(self):
        """Test application configuration"""
        print("\n7️⃣ Testing Configuration")
        print("-" * 50)
        
        try:
            with self.app.app_context():
                print(f"✅ Flask app created successfully")
                print(f"📊 Debug mode: {self.app.debug}")
                print(f"🔑 Secret key configured: {'SECRET_KEY' in self.app.config}")
                print(f"💾 Database URI: {'SQLALCHEMY_DATABASE_URI' in self.app.config}")
                
                # Check config values that should always be set
                required_configs = ['SECRET_KEY', 'SQLALCHEMY_DATABASE_URI']
                missing_configs = [config for config in required_configs if config not in self.app.config]
                
                if missing_configs:
                    print(f"❌ Missing configuration values: {', '.join(missing_configs)}")
                    self.issues_found.append(f"Configuration missing: {', '.join(missing_configs)}")
                
                # Check AI provider configuration
                ai_providers = self.app.config.get('AI_PROVIDERS', {})
                if ai_providers:
                    print(f"✅ AI providers configured: {len(ai_providers)}")
                else:
                    print("⚠️  No AI providers configured")
                    self.issues_found.append("No AI providers configured")
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            self.issues_found.append(f"Configuration: {e}")
    
    def test_dependencies(self):
        """Test external dependencies"""
        print("\n8️⃣ Testing External Dependencies")
        print("-" * 50)
        
        # Check if Redis is working
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            print("✅ Redis connection working")
        except ImportError:
            print("⚠️  Redis package not installed")
            self.issues_found.append("Redis package not installed")
        except Exception as e:
            print(f"⚠️  Redis issue: {e}")
            self.issues_found.append(f"Redis connectivity: {e}")


def run_diagnostics():
    """Entry point for running diagnostics"""
    diagnostics = SystemDiagnostics()
    diagnostics.run_all_tests()


if __name__ == "__main__":
    run_diagnostics()

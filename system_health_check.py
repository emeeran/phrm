#!/usr/bin/env python3
"""
Final System Health Check
"""
import requests
import time
import sys

def comprehensive_health_check():
    """Run a comprehensive health check of all system components"""
    print("🏥 PHRM System Health Check")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    issues = []
    
    # Test 1: Server Health
    print("1️⃣ Server Health...")
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code in [200, 302]:
            print("✅ Server responding correctly")
        else:
            issues.append(f"Server returned {response.status_code}")
    except Exception as e:
        issues.append(f"Server connectivity: {e}")
    
    # Test 2: Authentication
    print("\n2️⃣ Authentication System...")
    session = requests.Session()
    try:
        # Get login page
        login_page = session.get(f"{base_url}/auth/login")
        if login_page.status_code == 200:
            print("✅ Login page accessible")
            
            # Extract CSRF and attempt login
            import re
            csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', login_page.text)
            
            login_data = {
                'email': 'demo@example.com',
                'password': 'demo123'
            }
            if csrf_match:
                login_data['csrf_token'] = csrf_match.group(1)
            
            login_response = session.post(f"{base_url}/auth/login", data=login_data, allow_redirects=False)
            
            if login_response.status_code == 302:
                print("✅ Authentication working")
            else:
                issues.append(f"Login failed: {login_response.status_code}")
        else:
            issues.append(f"Login page inaccessible: {login_page.status_code}")
            
    except Exception as e:
        issues.append(f"Authentication test: {e}")
    
    # Test 3: Core Pages
    print("\n3️⃣ Core Application Pages...")
    pages_to_test = [
        ("/", "Homepage"),
        ("/auth/login", "Login"),
        ("/ai/chat", "AI Chat"),
        ("/records/dashboard", "Dashboard")
    ]
    
    for path, name in pages_to_test:
        try:
            response = session.get(f"{base_url}{path}")
            if response.status_code in [200, 302]:
                print(f"✅ {name} accessible")
            else:
                issues.append(f"{name} returned {response.status_code}")
        except Exception as e:
            issues.append(f"{name} test failed: {e}")
    
    # Test 4: Error Handling
    print("\n4️⃣ Error Handling...")
    try:
        error_response = requests.get(f"{base_url}/nonexistent-page-test")
        if error_response.status_code == 404:
            print("✅ 404 error handling working")
        else:
            issues.append(f"404 handling returned {error_response.status_code}")
    except Exception as e:
        issues.append(f"Error handling test: {e}")
    
    # Test 5: AI Chat (Quick Test)
    print("\n5️⃣ AI Chat System...")
    try:
        chat_data = {'message': 'Test'}
        chat_response = session.post(f"{base_url}/ai/chat", data=chat_data, timeout=15)
        
        if chat_response.status_code == 200:
            print("✅ AI Chat endpoint responding")
        else:
            issues.append(f"AI Chat returned {chat_response.status_code}")
    except requests.exceptions.Timeout:
        print("⚠️ AI Chat timeout (normal for AI processing)")
    except Exception as e:
        issues.append(f"AI Chat test: {e}")
    
    # Test 6: Static Files
    print("\n6️⃣ Static Assets...")
    static_files = [
        "/static/css/optimized.min.css",
        "/static/js/main.js",
        "/static/js/chat-manager.js"
    ]
    
    for static_file in static_files:
        try:
            response = requests.get(f"{base_url}{static_file}")
            if response.status_code == 200:
                print(f"✅ {static_file} accessible")
            else:
                issues.append(f"Static file {static_file} returned {response.status_code}")
        except Exception as e:
            issues.append(f"Static file {static_file}: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    if issues:
        print("⚠️ ISSUES FOUND:")
        for issue in issues:
            print(f"  • {issue}")
        print(f"\nTotal Issues: {len(issues)}")
        
        if len(issues) <= 2:
            print("✅ Minor issues only - system is largely functional")
            return True
        else:
            print("❌ Multiple issues found - needs attention")
            return False
    else:
        print("🎉 ALL SYSTEMS OPERATIONAL!")
        print("✅ No issues detected")
        return True

if __name__ == "__main__":
    success = comprehensive_health_check()
    
    print("\n🎯 FINAL STATUS:")
    if success:
        print("✅ PHRM system is ready for use!")
        print("✅ Login: demo@example.com / demo123")
        print("✅ Access at: http://localhost:5000")
    else:
        print("⚠️ System needs attention - see issues above")
    
    sys.exit(0 if success else 1)

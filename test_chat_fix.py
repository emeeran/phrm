#!/usr/bin/env python3
"""
Test script to verify the chat functionality fix
Tests both public and private modes to ensure target_records is properly initialized
"""

import requests
import json
from time import sleep

BASE_URL = "http://127.0.0.1:5000"

def test_chat_public_mode():
    """Test chat in public mode - should not cause target_records error"""
    print("🧪 Testing chat in PUBLIC mode...")
    
    # First, we need to register/login to get a session
    session = requests.Session()
    
    # Test registration
    register_data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'test@example.com',
        'password': 'TestPass123!',
        'confirm_password': 'TestPass123!'
    }
    
    try:
        # Try to register
        response = session.post(f"{BASE_URL}/auth/register", data=register_data)
        print(f"   Registration response: {response.status_code}")
        
        # If registration fails, try to login instead
        if response.status_code != 200:
            login_data = {
                'email': 'test@example.com',
                'password': 'TestPass123!'
            }
            response = session.post(f"{BASE_URL}/auth/login", data=login_data)
            print(f"   Login response: {response.status_code}")
        
        # Now test the chat endpoint in public mode
        chat_data = {
            'message': 'What are common symptoms of a cold?',
            'mode': 'public'
        }
        
        response = session.post(
            f"{BASE_URL}/ai/chat", 
            json=chat_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   Chat response status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ PUBLIC mode chat works correctly!")
            result = response.json()
            print(f"   Response preview: {result.get('response', 'No response')[:100]}...")
        else:
            print(f"   ❌ PUBLIC mode chat failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing public mode: {e}")
        return False
    
    return True

def test_chat_private_mode():
    """Test chat in private mode"""
    print("\n🧪 Testing chat in PRIVATE mode...")
    
    session = requests.Session()
    
    try:
        # Login
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        response = session.post(f"{BASE_URL}/auth/login", data=login_data)
        print(f"   Login response: {response.status_code}")
        
        # Test chat in private mode
        chat_data = {
            'message': 'What are my recent health records?',
            'mode': 'private',
            'patient': 'self'
        }
        
        response = session.post(
            f"{BASE_URL}/ai/chat", 
            json=chat_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   Chat response status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ PRIVATE mode chat works correctly!")
            result = response.json()
            print(f"   Response preview: {result.get('response', 'No response')[:100]}...")
        else:
            print(f"   ❌ PRIVATE mode chat failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing private mode: {e}")
        return False
    
    return True

def main():
    print("🚀 Testing Chat Functionality Fix")
    print("=" * 50)
    
    # Wait a moment for the server to be ready
    sleep(2)
    
    # Test both modes
    public_success = test_chat_public_mode()
    private_success = test_chat_private_mode()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Public Mode:  {'✅ PASS' if public_success else '❌ FAIL'}")
    print(f"   Private Mode: {'✅ PASS' if private_success else '❌ FAIL'}")
    
    if public_success and private_success:
        print("\n🎉 All tests passed! The target_records fix is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()

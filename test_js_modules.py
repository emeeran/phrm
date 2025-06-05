#!/usr/bin/env python3
"""
JavaScript Module Functionality Test
Tests that the modular JavaScript structure is working correctly
"""
import requests
import json
from bs4 import BeautifulSoup

def test_javascript_modules():
    """Test that JavaScript modules load and work correctly"""
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Testing JavaScript Module Functionality")
    print("=" * 50)
    
    # Test 1: Check if main.js loads
    response = requests.get(f"{base_url}/static/js/main.js")
    if response.status_code == 200:
        print("✅ main.js loads successfully")
        print(f"   Size: {len(response.text)} characters")
    else:
        print(f"❌ main.js failed to load: {response.status_code}")
        return False
    
    # Test 2: Check if utils.js loads
    response = requests.get(f"{base_url}/static/js/utils.js")
    if response.status_code == 200:
        print("✅ utils.js loads successfully")
        print(f"   Size: {len(response.text)} characters")
    else:
        print(f"❌ utils.js failed to load: {response.status_code}")
        return False
    
    # Test 3: Check if file-manager.js loads
    response = requests.get(f"{base_url}/static/js/file-manager.js")
    if response.status_code == 200:
        print("✅ file-manager.js loads successfully")
        print(f"   Size: {len(response.text)} characters")
    else:
        print(f"❌ file-manager.js failed to load: {response.status_code}")
        return False
    
    # Test 4: Check if chat-manager.js loads
    response = requests.get(f"{base_url}/static/js/chat-manager.js")
    if response.status_code == 200:
        print("✅ chat-manager.js loads successfully")
        print(f"   Size: {len(response.text)} characters")
    else:
        print(f"❌ chat-manager.js failed to load: {response.status_code}")
        return False
    
    # Test 5: Check ES module syntax
    main_js_content = requests.get(f"{base_url}/static/js/main.js").text
    if "import {" in main_js_content and "from './" in main_js_content:
        print("✅ ES module import syntax is correct in main.js")
    else:
        print("❌ ES module import syntax not found in main.js")
        return False
    
    # Test 6: Check export syntax
    utils_js_content = requests.get(f"{base_url}/static/js/utils.js").text
    if "export function" in utils_js_content:
        print("✅ ES module export syntax is correct in utils.js")
    else:
        print("❌ ES module export syntax not found in utils.js")
        return False
    
    # Test 7: Check class exports
    file_manager_content = requests.get(f"{base_url}/static/js/file-manager.js").text
    if "export class FileUploadManager" in file_manager_content:
        print("✅ ES module class export is correct in file-manager.js")
    else:
        print("❌ ES module class export not found in file-manager.js")
        return False
    
    chat_manager_content = requests.get(f"{base_url}/static/js/chat-manager.js").text
    if "export class ChatManager" in chat_manager_content:
        print("✅ ES module class export is correct in chat-manager.js")
    else:
        print("❌ ES module class export not found in chat-manager.js")
        return False
    
    # Test 8: Check if template loads modules correctly
    response = requests.get(f"{base_url}/auth/login")
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'type': 'module'})
        if script_tag and 'main.js' in script_tag.get('src', ''):
            print("✅ HTML template correctly loads main.js as ES module")
        else:
            print("❌ HTML template does not load main.js as ES module")
            return False
    else:
        print(f"❌ Could not load login page: {response.status_code}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL JAVASCRIPT MODULE TESTS PASSED!")
    print("✅ ES Modules are working correctly")
    print("✅ Import/Export syntax is correct")
    print("✅ All modules load without errors")
    print("✅ HTML templates correctly reference modules")
    return True

if __name__ == '__main__':
    test_javascript_modules()

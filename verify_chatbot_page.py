#!/usr/bin/env python3
"""
Script to verify that the enhanced-chat.css file is accessible.
"""

import requests
import sys
import time

def verify_css_file():
    """Verify that the enhanced-chat.css file can be loaded directly."""
    # Wait for server to fully start
    time.sleep(2)
    
    # Try to access the CSS file directly
    try:
        css_url = "http://localhost:5010/static/css/enhanced-chat.css"
        css_response = requests.get(css_url)
        
        if css_response.status_code == 200:
            print(f"✅ SUCCESS: CSS file loaded successfully (size: {len(css_response.text)} bytes)")
            print("✅ CSS content sample (first 100 chars):")
            print(f"   {css_response.text[:100]}...")
            return True
        else:
            print(f"❌ ERROR: CSS file returned status code {css_response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ ERROR connecting to server: {e}")
        return False

def main():
    """Main function to run verification."""
    print("Verifying enhanced-chat.css file accessibility...")
    
    result = verify_css_file()
    
    if result:
        print("\n✅ All checks passed! The enhanced-chat.css is correctly loaded.")
        return 0
    else:
        print("\n❌ Some checks failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

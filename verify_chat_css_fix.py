#!/usr/bin/env python3
"""
Script to verify that the enhanced-chat.css file exists and is accessible.
"""

import os
import sys
from pathlib import Path

def verify_chat_css():
    """Verify that enhanced-chat.css exists in the correct location."""
    # Get base directory
    base_dir = Path(__file__).parent.resolve()
    
    # Check if the CSS file exists
    css_path = base_dir / "app" / "static" / "css" / "enhanced-chat.css"
    
    if css_path.exists():
        print(f"✅ SUCCESS: enhanced-chat.css exists at {css_path}")
        print(f"File size: {os.path.getsize(css_path)} bytes")
        return True
    else:
        print(f"❌ ERROR: enhanced-chat.css does not exist at {css_path}")
        return False

def check_template_reference():
    """Check that the template correctly references the CSS file."""
    # Get base directory
    base_dir = Path(__file__).parent.resolve()
    
    # Check the template file
    template_path = base_dir / "app" / "templates" / "ai" / "chatbot.html"
    
    if not template_path.exists():
        print(f"❌ ERROR: Template file does not exist at {template_path}")
        return False
    
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    if "url_for('static', filename='css/enhanced-chat.css')" in template_content:
        print(f"✅ SUCCESS: Template correctly references the CSS file")
        return True
    else:
        print(f"❌ ERROR: Template does not correctly reference the CSS file")
        return False

def main():
    """Main function to run all verification checks."""
    print("Verifying enhanced-chat.css fix...")
    
    css_exists = verify_chat_css()
    template_correct = check_template_reference()
    
    if css_exists and template_correct:
        print("\n✅ All checks passed! The enhanced-chat.css issue has been fixed.")
        return 0
    else:
        print("\n❌ Some checks failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Verify patient selector template implementation
"""

def check_template_implementation():
    """Check if the chatbot template has proper patient selector hiding"""
    try:
        with open('app/templates/ai/chatbot.html', 'r') as f:
            content = f.read()
            
        print("🧪 Checking Template Implementation")
        print("=" * 50)
        
        # Check 1: Patient container has display: none
        if 'id="patient-selector-container"' in content:
            print("✅ Patient selector container found")
            
            # Check for display: none
            if 'style="display: none' in content:
                print("✅ Patient selector has display: none in style")
            else:
                print("❌ Patient selector missing display: none")
                
            # Check for hidden-public class
            if 'hidden-public' in content:
                print("✅ Patient selector has hidden-public CSS class")
            else:
                print("❌ Patient selector missing hidden-public class")
                
        else:
            print("❌ Patient selector container not found")
            
        # Check 2: Mode selector defaults to public
        if 'value="public" selected' in content:
            print("✅ Mode selector defaults to public")
        else:
            print("❌ Mode selector doesn't default to public")
            
        # Check 3: JavaScript fallback exists
        if 'togglePatientSelector' in content:
            print("✅ JavaScript fallback function found")
        else:
            print("❌ JavaScript fallback missing")
            
        # Check 4: CSS override exists
        if 'display: none !important' in content:
            print("✅ CSS !important override found")
        else:
            print("❌ CSS !important override missing")
            
        print("\n📋 Summary:")
        print("The patient selector should be hidden by multiple layers:")
        print("1. Inline style: display: none !important")
        print("2. CSS class: hidden-public")
        print("3. JavaScript fallback in template")
        print("4. Main ChatManager JavaScript")
        
    except Exception as e:
        print(f"❌ Error checking template: {e}")

if __name__ == "__main__":
    check_template_implementation()

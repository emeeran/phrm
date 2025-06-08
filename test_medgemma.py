#!/usr/bin/env python3
"""
Test script to verify MedGemma access via Hugging Face API
"""

import os
import sys
sys.path.append('.')

from app.utils.ai_helpers import call_huggingface_api, get_huggingface_api_key

def test_medgemma():
    """Test MedGemma API access"""
    print("🧪 Testing MedGemma API access...")
    
    # Check if API key is available
    api_key = get_huggingface_api_key()
    if not api_key:
        print("❌ No Hugging Face API key found!")
        return False
    
    print(f"✅ Hugging Face API key found: {api_key[:8]}...")
    
    # Test system message for medical AI
    system_message = """You are MedGemma, a medical AI assistant. Provide accurate, evidence-based medical information while emphasizing the importance of professional medical consultation."""
    
    # Test prompt
    prompt = "What are the common symptoms of type 2 diabetes?"
    
    print(f"📤 Sending test request to MedGemma...")
    print(f"Model: google/medgemma-4b-it")
    print(f"Prompt: {prompt}")
    
    try:
        response = call_huggingface_api(
            system_message=system_message,
            prompt=prompt,
            temperature=0.3,
            max_tokens=500,
            model="google/medgemma-4b-it"
        )
        
        if response:
            print(f"✅ MedGemma API call successful!")
            print(f"📥 Response ({len(response)} chars):")
            print("-" * 50)
            print(response)
            print("-" * 50)
            return True
        else:
            print("❌ MedGemma API call failed - no response received")
            return False
            
    except Exception as e:
        print(f"❌ MedGemma API call failed with error: {e}")
        return False

if __name__ == "__main__":
    print("🏥 PHRM MedGemma Integration Test")
    print("=" * 40)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = test_medgemma()
    
    if success:
        print("\n🎉 MedGemma integration test PASSED!")
        print("✅ The PHRM application can now use MedGemma as the primary AI provider.")
    else:
        print("\n❌ MedGemma integration test FAILED!")
        print("⚠️  The application will fall back to GROQ and DEEPSEEK providers.")
    
    print("\n📋 Provider Hierarchy:")
    print("1. 🥇 HuggingFace MedGemma (Primary)")
    print("2. 🥈 GROQ (Secondary)")  
    print("3. 🥉 DEEPSEEK (Fallback)")

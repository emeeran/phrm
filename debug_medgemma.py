#!/usr/bin/env python3
"""
Debug script to test MedGemma model access and URL construction
"""

import os
import sys
import requests
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

def debug_medgemma_access():
    """Debug MedGemma model access step by step"""
    
    print("🔍 DEBUG: MedGemma Access Investigation")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv('HUGGINGFACE_ACCESS_TOKEN')
    if not api_key:
        print("❌ No Hugging Face API key found!")
        return
    
    print(f"✅ API Key: {api_key[:8]}...{api_key[-4:]}")
    
    # Test different model names
    model_variants = [
        "google/medgemma-4b-it",
        "google/medgemma-7b-it", 
        "google/gemma-2b-it",
        "google/gemma-7b-it",
        "microsoft/DialoGPT-medium"  # Control test
    ]
    
    base_url = "https://api-inference.huggingface.co/models/"
    
    for model in model_variants:
        print(f"\n🧪 Testing model: {model}")
        full_url = f"{base_url}{model}"
        print(f"📡 URL: {full_url}")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Simple test payload
        payload = {
            "inputs": "Hello, how are you?",
            "parameters": {
                "max_new_tokens": 50,
                "temperature": 0.7
            }
        }
        
        try:
            response = requests.post(full_url, headers=headers, json=payload, timeout=30)
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS! Response: {str(result)[:100]}...")
            elif response.status_code == 404:
                print(f"❌ 404 - Model not found or no access")
                print(f"Response: {response.text[:200]}")
            elif response.status_code == 503:
                print(f"⏳ 503 - Model loading")
            else:
                print(f"❓ Status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test model info endpoint
    print(f"\n🔍 Testing model info endpoint...")
    info_url = f"https://huggingface.co/api/models/google/medgemma-4b-it"
    try:
        response = requests.get(info_url)
        print(f"📊 Model info status: {response.status_code}")
        if response.status_code == 200:
            info = response.json()
            print(f"✅ Model exists and accessible")
            print(f"Pipeline tag: {info.get('pipeline_tag', 'Unknown')}")
            print(f"Model type: {info.get('modelType', 'Unknown')}")
        else:
            print(f"❌ Model info failed: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Model info error: {e}")

if __name__ == "__main__":
    debug_medgemma_access()

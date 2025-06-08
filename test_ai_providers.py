#!/usr/bin/env python3
"""
AI Providers Test Script
========================

Test the AI providers (GROQ and DEEPSEEK) to ensure they're working correctly.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_groq_api():
    """Test GROQ API"""
    print("🧪 Testing GROQ API...")
    
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("   ❌ GROQ API key not found")
        return False
    
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-r1-distill-llama-70b",
            "messages": [
                {"role": "system", "content": "You are a helpful medical AI assistant."},
                {"role": "user", "content": "What is diabetes? Give a brief medical explanation."}
            ],
            "temperature": 0.3,
            "max_tokens": 200
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"   ✅ GROQ API working - Generated {len(content)} characters")
                print(f"   📝 Sample response: {content[:100]}...")
                return True
            else:
                print(f"   ❌ Unexpected response format: {result}")
                return False
        else:
            print(f"   ❌ API call failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ GROQ API test failed: {e}")
        return False

def test_deepseek_api():
    """Test DEEPSEEK API"""
    print("🧪 Testing DEEPSEEK API...")
    
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("   ❌ DEEPSEEK API key not found")
        return False
    
    try:
        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a helpful medical AI assistant."},
                {"role": "user", "content": "What is hypertension? Give a brief medical explanation."}
            ],
            "temperature": 0.3,
            "max_tokens": 200
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"   ✅ DEEPSEEK API working - Generated {len(content)} characters")
                print(f"   📝 Sample response: {content[:100]}...")
                return True
            else:
                print(f"   ❌ Unexpected response format: {result}")
                return False
        else:
            print(f"   ❌ API call failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ DEEPSEEK API test failed: {e}")
        return False

def test_huggingface_api():
    """Test Hugging Face API with multiple MedGemma models"""
    print("🧪 Testing Hugging Face API...")
    
    api_token = os.getenv('HUGGINGFACE_ACCESS_TOKEN')
    if not api_token:
        print("   ❌ Hugging Face API token not found")
        return False
    
    # Try multiple MedGemma models in order of preference
    models_to_try = [
        "google/medgemma-4b-it",  # Primary: instruction-tuned 4B
        "google/medgemma-27b-it", # Secondary: larger text-only model
        "google/medgemma-4b-pt",  # Tertiary: pre-trained 4B
        "google/gemma-2b-it",     # Control: Standard Gemma model
    ]
    
    for i, model in enumerate(models_to_try):
        try:
            print(f"   🔄 Trying model {i+1}/{len(models_to_try)}: {model}")
            url = f"https://api-inference.huggingface.co/models/{model}"
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            
            # Use simple text generation format
            payload = {
                "inputs": "Question: What is asthma? Give a brief medical explanation.\nAnswer:",
                "parameters": {
                    "max_new_tokens": 200,
                    "temperature": 0.3,
                    "do_sample": True,
                    "return_full_text": False
                },
                "options": {
                    "wait_for_model": True
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                
                # Handle different response formats
                content = ""
                if isinstance(result, list) and len(result) > 0:
                    if 'generated_text' in result[0]:
                        content = result[0]['generated_text']
                    elif 'text' in result[0]:
                        content = result[0]['text']
                elif isinstance(result, dict):
                    content = result.get('generated_text', result.get('text', ''))
                
                if content and len(content.strip()) > 10:
                    print(f"   ✅ Hugging Face API working with {model}")
                    print(f"   📝 Generated {len(content)} characters")
                    print(f"   📄 Sample response: {content[:100]}...")
                    return True
                else:
                    print(f"   ⚠️ Model {model} returned empty or minimal response: {result}")
                    continue
                    
            elif response.status_code == 503:
                print(f"   ⏳ Model {model} is loading, this may take a moment...")
                continue
            elif response.status_code == 403:
                print(f"   🚫 Access denied to {model} - check permissions")
                continue
            else:
                print(f"   ❌ Model {model} failed with status {response.status_code}: {response.text}")
                continue
                
        except Exception as e:
            print(f"   ❌ Error testing {model}: {e}")
            continue
    
    print("   ❌ All Hugging Face MedGemma models failed")
    return False

def test_medgemma_local():
    """Test MedGemma model locally using transformers (if available)"""
    print("🧪 Testing MedGemma model locally with transformers...")
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
        model_name = "google/medgemma-4b-it"
        print(f"   🔄 Loading model: {model_name} (this may take a while and requires >8GB VRAM)")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        prompt = "Question: What is asthma? Give a brief medical explanation.\nAnswer:"
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            output = model.generate(**inputs, max_new_tokens=200, temperature=0.3, do_sample=True)
        response = tokenizer.decode(output[0], skip_special_tokens=True)
        print(f"   ✅ MedGemma local model generated response:")
        print(f"   📄 {response}")
        return True
    except ImportError:
        print("   ⚠️ transformers or torch not installed. Run: pip install transformers torch")
        return False
    except Exception as e:
        print(f"   ❌ MedGemma local test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🏥 PHRM AI Providers Test")
    print("=" * 40)
    print()
    
    # Test all providers
    groq_working = test_groq_api()
    print()
    
    deepseek_working = test_deepseek_api()
    print()
    
    hf_working = test_huggingface_api()
    print()
    
    medgemma_local_working = test_medgemma_local()
    print()
    
    # Summary
    print("📊 Test Results")
    print("=" * 40)
    working_providers = []
    if hf_working:
        working_providers.append("🥇 Hugging Face (MedGemma)")
    if groq_working:
        working_providers.append("🥈 GROQ")
    if deepseek_working:
        working_providers.append("🥉 DEEPSEEK")
    if medgemma_local_working:
        working_providers.append("🏅 MedGemma (local)")
    
    if working_providers:
        print("✅ Working AI Providers:")
        for provider in working_providers:
            print(f"   {provider}")
        print()
        print(f"🎉 {len(working_providers)} out of 4 AI providers are working!")
        print("   The PHRM application has reliable AI fallback coverage.")
    else:
        print("❌ No AI providers are working")
        print("   Please check your API keys, local model, and network connection.")
    
    print()
    print("💡 Next Steps:")
    print("   → Test the web application at http://127.0.0.1:5001")
    print("   → Register/login and test AI chat and symptom checker")
    print("   → Create health records and generate AI summaries")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Research script to test alternative medical AI models on Hugging Face
"""

import os
import sys
sys.path.append('.')

from app.utils.ai_helpers import call_huggingface_api, get_huggingface_api_key

def test_medical_models():
    """Test various medical AI models available on Hugging Face"""
    
    print("🔬 Researching accessible medical AI models...")
    
    # Check if API key is available
    api_key = get_huggingface_api_key()
    if not api_key:
        print("❌ No Hugging Face API key found!")
        return
    
    print(f"✅ Hugging Face API key found: {api_key[:8]}...")
    
    # List of medical AI models to test (publicly accessible)
    medical_models = [
        "microsoft/DialoGPT-medium",  # General conversational AI that can be medical-focused
        "facebook/blenderbot-400M-distill",  # General conversational AI
        "microsoft/BioGPT",  # Biomedical text generation
        "dmis-lab/biobert-base-cased-v1.1",  # Biomedical BERT (but for embeddings)
        "allenai/scibert_scivocab_uncased",  # Scientific BERT
        "emilyalsentzer/Bio_ClinicalBERT",  # Clinical BERT
        "google/flan-t5-base",  # General instruction-following model
        "google/flan-t5-large",  # Larger instruction-following model
        "microsoft/GODEL-v1_1-base-seq2seq",  # Goal-oriented dialog
        "Salesforce/blip-image-captioning-base",  # For medical image analysis
    ]
    
    # Test system message for medical AI
    system_message = """You are a medical AI assistant. Provide accurate, evidence-based medical information while emphasizing the importance of professional medical consultation. Always include appropriate disclaimers."""
    
    # Test prompt
    prompt = "What are the common symptoms of type 2 diabetes? Please provide a brief overview."
    
    successful_models = []
    failed_models = []
    
    for model in medical_models:
        print(f"\n🧪 Testing model: {model}")
        try:
            response = call_huggingface_api(
                system_message=system_message,
                prompt=prompt,
                temperature=0.3,
                max_tokens=300,
                model=model
            )
            
            if response and len(response) > 10:
                print(f"✅ SUCCESS - {model}")
                print(f"📥 Response preview: {response[:100]}...")
                successful_models.append(model)
            else:
                print(f"❌ FAILED - {model} (empty/short response)")
                failed_models.append(model)
                
        except Exception as e:
            print(f"❌ FAILED - {model}: {e}")
            failed_models.append(model)
    
    print("\n" + "="*60)
    print("📊 RESULTS SUMMARY")
    print("="*60)
    
    if successful_models:
        print(f"\n✅ SUCCESSFUL MODELS ({len(successful_models)}):")
        for model in successful_models:
            print(f"  • {model}")
    
    if failed_models:
        print(f"\n❌ FAILED MODELS ({len(failed_models)}):")
        for model in failed_models:
            print(f"  • {model}")
    
    # Recommend best alternatives
    if successful_models:
        print(f"\n💡 RECOMMENDATION:")
        print(f"Consider using: {successful_models[0]}")
        print(f"This can serve as a fallback while we resolve MedGemma access.")
    
    return successful_models

if __name__ == "__main__":
    print("🏥 PHRM Medical AI Model Research")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    successful_models = test_medical_models()
    
    if successful_models:
        print(f"\n🎉 Found {len(successful_models)} working medical AI alternatives!")
    else:
        print(f"\n😞 No accessible medical AI models found. Will rely on GROQ/DEEPSEEK fallbacks.")

#!/usr/bin/env python3
"""
Test MedGemma using Transformers library directly instead of Inference API
"""

import os
import sys
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

def test_medgemma_transformers():
    """Test MedGemma using transformers library directly"""
    
    print("🔬 Testing MedGemma with Transformers Library")
    print("=" * 50)
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
        
        print("✅ Transformers library imported successfully")
        
        # Check if we have a token
        token = os.getenv('HUGGINGFACE_ACCESS_TOKEN')
        if not token:
            print("❌ No Hugging Face token found")
            return False
        
        print(f"✅ Token found: {token[:8]}...")
        
        model_name = "google/medgemma-4b-it"
        print(f"📦 Loading model: {model_name}")
        
        # Try to load tokenizer first
        print("📝 Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            token=token,
            trust_remote_code=True
        )
        print("✅ Tokenizer loaded successfully")
        
        # Try to load model (this might take a while or fail due to size)
        print("🧠 Loading model...")
        print("⚠️  This may take a while or fail due to model size...")
        
        try:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                token=token,
                trust_remote_code=True,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            print("✅ Model loaded successfully")
            
            # Test generation
            print("🧪 Testing text generation...")
            test_prompt = "What are the common symptoms of diabetes?"
            inputs = tokenizer(test_prompt, return_tensors="pt")
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response.replace(test_prompt, "").strip()
            
            print(f"✅ Generation successful!")
            print(f"📝 Response: {response}")
            return True
            
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            print("💡 This might be due to model size or hardware limitations")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 You might need to install: pip install transformers torch")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_medgemma_transformers()

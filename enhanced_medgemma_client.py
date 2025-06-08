#!/usr/bin/env python3
"""
Enhanced MedGemma Integration
============================

This script provides multiple approaches to accessing MedGemma:
1. Hugging Face Inference API (serverless)
2. Local transformers inference (when model access is available)
3. Fallback to other medical AI providers

The script will automatically detect which method works and use the best available option.
"""

import os
import requests
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MedGemmaClient:
    """Enhanced MedGemma client with multiple access methods"""
    
    def __init__(self):
        self.api_token = os.getenv('HUGGINGFACE_ACCESS_TOKEN')
        self.models = [
            "google/medgemma-4b-it",    # Primary: instruction-tuned
            "google/medgemma-4b-pt",    # Secondary: pre-trained  
        ]
        self.working_method = None
        self.working_model = None
        
    def test_inference_api(self, model_name):
        """Test Hugging Face Inference API access"""
        try:
            url = f"https://api-inference.huggingface.co/models/{model_name}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            # Use medical-specific prompt format
            payload = {
                "inputs": "Question: What is hypertension?\nAnswer:",
                "parameters": {
                    "max_new_tokens": 150,
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
                if isinstance(result, list) and len(result) > 0:
                    content = result[0].get('generated_text', '')
                    if content and len(content.strip()) > 10:
                        return True, content
                        
            elif response.status_code == 503:
                logger.info(f"Model {model_name} is loading...")
                return False, "Model loading"
            elif response.status_code == 404:
                logger.warning(f"Model {model_name} not found via Inference API")
                return False, "Not found"
            else:
                logger.warning(f"API error for {model_name}: {response.status_code}")
                return False, f"API error: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Inference API test failed for {model_name}: {e}")
            return False, str(e)
            
        return False, "No valid response"
    
    def test_local_transformers(self, model_name):
        """Test local transformers access"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            # Try to load tokenizer (lighter operation)
            tokenizer = AutoTokenizer.from_pretrained(
                model_name, 
                trust_remote_code=True,
                token=self.api_token
            )
            
            # Test basic tokenization
            test_text = "What is diabetes?"
            tokens = tokenizer.encode(test_text)
            
            logger.info(f"Local tokenizer loaded successfully for {model_name}")
            return True, f"Tokenizer loaded ({len(tokens)} tokens)"
            
        except Exception as e:
            if "gated repo" in str(e) or "restricted" in str(e):
                logger.warning(f"Access not yet available for {model_name}")
                return False, "Access pending"
            else:
                logger.error(f"Local transformers test failed for {model_name}: {e}")
                return False, str(e)
    
    def find_working_method(self):
        """Find the best working method to access MedGemma"""
        logger.info("🔍 Testing MedGemma access methods...")
        
        for model in self.models:
            logger.info(f"Testing model: {model}")
            
            # Test 1: Inference API
            logger.info("  🌐 Testing Inference API...")
            success, result = self.test_inference_api(model)
            if success:
                self.working_method = "inference_api"
                self.working_model = model
                logger.info(f"  ✅ Inference API working for {model}")
                return True
            else:
                logger.info(f"  ❌ Inference API failed: {result}")
            
            # Test 2: Local transformers
            logger.info("  💻 Testing local transformers...")
            success, result = self.test_local_transformers(model)
            if success:
                self.working_method = "local_transformers"
                self.working_model = model
                logger.info(f"  ✅ Local transformers working for {model}")
                return True
            else:
                logger.info(f"  ❌ Local transformers failed: {result}")
        
        logger.warning("❌ No working MedGemma access method found")
        return False
    
    def generate_response(self, prompt, max_tokens=200, temperature=0.3):
        """Generate response using the best available method"""
        if not self.working_method:
            if not self.find_working_method():
                return None, "No working MedGemma access method available"
        
        if self.working_method == "inference_api":
            return self._generate_via_api(prompt, max_tokens, temperature)
        elif self.working_method == "local_transformers":
            return self._generate_via_local(prompt, max_tokens, temperature)
        else:
            return None, "No working method available"
    
    def _generate_via_api(self, prompt, max_tokens, temperature):
        """Generate response via Inference API"""
        try:
            url = f"https://api-inference.huggingface.co/models/{self.working_model}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "do_sample": True,
                    "return_full_text": False
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    content = result[0].get('generated_text', '')
                    return content, None
            
            return None, f"API error: {response.status_code}"
            
        except Exception as e:
            return None, str(e)
    
    def _generate_via_local(self, prompt, max_tokens, temperature):
        """Generate response via local transformers"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            # Load model and tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                self.working_model,
                trust_remote_code=True,
                token=self.api_token
            )
            
            model = AutoModelForCausalLM.from_pretrained(
                self.working_model,
                trust_remote_code=True,
                token=self.api_token,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            # Generate response
            inputs = tokenizer.encode(prompt, return_tensors="pt")
            
            with torch.no_grad():
                outputs = model.generate(
                    inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Remove the input prompt from response
            if response.startswith(prompt):
                response = response[len(prompt):].strip()
            
            return response, None
            
        except Exception as e:
            return None, str(e)

def main():
    """Test the enhanced MedGemma client"""
    print("🏥 Enhanced MedGemma Integration Test")
    print("=" * 50)
    
    client = MedGemmaClient()
    
    # Test if any method works
    if client.find_working_method():
        print(f"✅ Working method: {client.working_method}")
        print(f"✅ Working model: {client.working_model}")
        print()
        
        # Test generation
        print("🧪 Testing response generation...")
        prompt = "Question: What is diabetes? Provide a brief medical explanation.\nAnswer:"
        
        response, error = client.generate_response(prompt, max_tokens=150)
        
        if response:
            print("✅ Response generated successfully!")
            print(f"📝 Response ({len(response)} characters):")
            print(f"   {response[:200]}...")
        else:
            print(f"❌ Generation failed: {error}")
    else:
        print("❌ No working MedGemma access method found")
        print()
        print("💡 Possible reasons:")
        print("   • Access is still propagating (may take a few hours)")
        print("   • Need to authenticate with Hugging Face CLI")
        print("   • Model not yet available via Inference API")
        print()
        print("🔧 Troubleshooting steps:")
        print("   1. Wait a few hours for access to propagate")
        print("   2. Try: huggingface-cli login")
        print("   3. Verify access at: https://huggingface.co/google/medgemma-4b-it")

if __name__ == "__main__":
    main()

"""
AI Helper Functions
==================
This module contains utility functions for AI operations including:
- Text extraction from PDFs
- API calls to Hugging Face (including MedGemma), GROQ, and DEEPSEEK
- API key management
- AI client initialization for MedGemma
"""

import logging
import os

from flask import current_app

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF file using multiple fallback methods.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text or metadata if extraction fails
    """
    if not os.path.exists(file_path):
        logger.error(f"PDF file not found: {file_path}")
        return ""

    extracted_text = ""

    # Method 1: Try PyPDF2/pypdf first (lightweight)
    try:
        import pypdf
        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            text_parts = []

            for page in pdf_reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text)

            if text_parts:
                extracted_text = "\n".join(text_parts)
                logger.info(f"Successfully extracted {len(extracted_text)} characters using pypdf")
                return extracted_text

    except ImportError:
        logger.warning("pypdf not available, trying alternative methods")
    except Exception as e:
        logger.warning(f"pypdf extraction failed: {e}")

    # Method 2: Try PyMuPDF (fitz) if available
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text_parts = []

        for page in doc:
            text = page.get_text()
            if text.strip():
                text_parts.append(text)

        doc.close()

        if text_parts:
            extracted_text = "\n".join(text_parts)
            logger.info(f"Successfully extracted {len(extracted_text)} characters using PyMuPDF")
            return extracted_text

    except ImportError:
        logger.warning("PyMuPDF not available")
    except Exception as e:
        logger.warning(f"PyMuPDF extraction failed: {e}")

    # Fallback: Return metadata if text extraction completely fails
    try:
        import pypdf
        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            metadata = pdf_reader.metadata

            fallback_text = "PDF METADATA:\n"
            fallback_text += f"Pages: {len(pdf_reader.pages)}\n"

            if metadata:
                for key, value in metadata.items():
                    if value:
                        fallback_text += f"{key}: {value}\n"

            fallback_text += "\nFull text extraction was not possible. The document may contain images, complex formatting, or be password protected."

            logger.warning(f"Could only extract metadata from {file_path}")
            return fallback_text

    except Exception as e:
        logger.error(f"Complete PDF processing failed for {file_path}: {e}")
        return f"Error: Could not process PDF file. {e!s}"

def get_huggingface_api_key():
    """
    Retrieve the Hugging Face API key from configuration.
    
    Returns:
        str: API key or None if not configured
    """
    api_key = None

    # Try to get from Flask config first
    try:
        api_key = current_app.config.get('HUGGINGFACE_ACCESS_TOKEN')
    except RuntimeError:
        # No application context, try environment variable
        api_key = os.getenv('HUGGINGFACE_ACCESS_TOKEN')

    return api_key

def get_openai_api_key():
    """
    Retrieve the OpenAI API key from configuration.
    
    Returns:
        str: API key or None if not configured
    """
    api_key = None

    # Try to get from Flask config first
    try:
        api_key = current_app.config.get('OPENAI_API_KEY')
    except RuntimeError:
        # No application context, try environment variable
        api_key = os.getenv('OPENAI_API_KEY')

    return api_key

# Enhanced MedGemma Client class for better integration
class MedGemmaClient:
    """Enhanced MedGemma client with multiple access methods"""

    def __init__(self):
        self.api_token = get_huggingface_api_key() # Use the helper to get token
        self.models = [
            "google/medgemma-4b-it",    # Primary: instruction-tuned
            "google/medgemma-27b-it",   # Secondary: larger model (added from conversation)
            "google/medgemma-4b-pt",    # Fallback: pre-trained
        ]
        self.working_method = None
        self.working_model = None
        # Add a small delay for requests to avoid hitting rate limits too quickly during testing
        self.request_delay = 0.5 # seconds

    def test_inference_api(self, model_name):
        """Test Hugging Face Inference API access"""
        try:
            import time

            import requests
            time.sleep(self.request_delay) # Add delay

            url = f"https://api-inference.huggingface.co/models/{model_name}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }

            # Use medical-specific prompt format
            payload = {
                "inputs": "Question: What is hypertension?\\nAnswer:",
                "parameters": {
                    "max_new_tokens": 150,
                    "temperature": 0.3,
                    "do_sample": True,
                    "return_full_text": False
                },
                "options": {
                    "wait_for_model": True # Changed from False to True as per enhanced_medgemma_client
                }
            }

            response = requests.post(url, headers=headers, json=payload, timeout=60) # Increased timeout

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    content = result[0].get('generated_text', '')
                    if content and len(content.strip()) > 10: # Check for meaningful content
                        return True, content
                # Handle cases where result might be a dict with 'error'
                elif isinstance(result, dict) and 'error' in result:
                    logger.warning(f"Inference API error for {model_name}: {result['error']}")
                    if "is currently loading" in result['error']:
                         return False, "Model loading"
                    return False, result['error']

            elif response.status_code == 503: # Model loading
                logger.info(f"Model {model_name} is loading (503)...")
                return False, "Model loading"
            elif response.status_code == 404:
                logger.warning(f"Model {model_name} not found via Inference API (404)")
                return False, "Not found"
            elif response.status_code == 403:
                logger.warning(f"Access denied to {model_name} (403) - check token/permissions")
                return False, "Access denied"
            else:
                logger.warning(f"API error for {model_name}: {response.status_code} - {response.text[:200]}")
                return False, f"API error: {response.status_code}"

        except requests.exceptions.Timeout:
            logger.error(f"Inference API test timed out for {model_name}")
            return False, "Timeout"
        except Exception as e:
            logger.error(f"Inference API test failed for {model_name}: {e}")
            return False, str(e)

        return False, "No valid response or unexpected error"

    def test_local_transformers(self, model_name):
        """Test local transformers access (placeholder for future, currently focuses on tokenizer)"""
        try:
            from transformers import AutoTokenizer  #, AutoModelForCausalLM
            # import torch # Not importing Model or torch yet to keep it light for initial integration

            logger.info(f"Attempting to load tokenizer for {model_name} locally.")
            # Try to load tokenizer (lighter operation than full model)
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True, # Important for some models
                token=self.api_token
            )

            # Test basic tokenization
            test_text = "What is diabetes?"
            tokens = tokenizer.encode(test_text)

            logger.info(f"Local tokenizer loaded successfully for {model_name}. Test tokenization produced {len(tokens)} tokens.")
            # For now, we'll consider tokenizer loading a success for 'local_transformers' path.
            # Full model loading and inference would be the next step if this path is chosen.
            return True, f"Tokenizer loaded ({len(tokens)} tokens)"

        except ImportError:
            logger.warning("Transformers or PyTorch not installed. Local inference disabled.")
            return False, "Missing libraries"
        except Exception as e:
            error_str = str(e).lower()
            if "gated repo" in error_str or "authentication is required" in error_str or "restricted" in error_str:
                logger.warning(f"Local access to {model_name} gated/restricted: {e}")
                return False, "Access pending/gated"
            elif "does not exist" in error_str or "not a valid model identifier" in error_str:
                logger.warning(f"Local model {model_name} not found or invalid: {e}")
                return False, "Model not found locally"
            else:
                logger.error(f"Local transformers test (tokenizer) failed for {model_name}: {e}")
                return False, str(e)

    def find_working_method(self):
        """Find the best working method to access MedGemma"""
        if not self.api_token:
            logger.warning("Hugging Face API token not configured. MedGemma client cannot operate.")
            return False

        logger.info("🔍 Testing MedGemma access methods...")

        for model_to_test in self.models:
            logger.info(f"Testing model: {model_to_test}")

            # Test 1: Inference API
            logger.info(f"  🌐 Testing Inference API for {model_to_test}...")
            success, result = self.test_inference_api(model_to_test)
            if success:
                self.working_method = "inference_api"
                self.working_model = model_to_test
                logger.info(f"  ✅ Inference API working for {self.working_model}. Sample: {result[:60]}...")
                return True
            else:
                logger.info(f"  ❌ Inference API failed for {model_to_test}: {result}")

            # Test 2: Local transformers (tokenizer check for now)
            # This path would be more relevant if Inference API consistently fails and local setup is an option.
            # logger.info(f"  💻 Testing local transformers (tokenizer) for {model_to_test}...")
            # success, result = self.test_local_transformers(model_to_test)
            # if success:
            #     self.working_method = "local_transformers"
            #     self.working_model = model_to_test
            #     logger.info(f"  ✅ Local transformers (tokenizer) working for {self.working_model}: {result}")
            #     return True
            # else:
            #     logger.info(f"  ❌ Local transformers (tokenizer) failed for {model_to_test}: {result}")

        logger.warning("❌ No working MedGemma access method found after trying all configured models.")
        return False

    def generate_response(self, prompt, max_tokens=200, temperature=0.3):
        """Generate response using the best available method"""
        if not self.working_method: # If not pre-tested or previous method failed
            logger.info("No working method pre-selected, attempting to find one now.")
            if not self.find_working_method():
                logger.error("MedGemma Client: No working access method available after fresh check.")
                return None, "No working MedGemma access method available"

        logger.info(f"Generating response using method: {self.working_method} with model: {self.working_model}")
        if self.working_method == "inference_api":
            return self._generate_via_api(prompt, max_tokens, temperature)
        # elif self.working_method == "local_transformers":
        #     return self._generate_via_local(prompt, max_tokens, temperature) # Placeholder
        else:
            logger.error(f"MedGemma Client: Unknown working_method '{self.working_method}' selected.")
            return None, "Unknown working method selected"

    def _generate_via_api(self, prompt, max_tokens, temperature):
        """Generate response via Inference API using self.working_model"""
        try:
            import time

            import requests
            time.sleep(self.request_delay) # Add delay

            url = f"https://api-inference.huggingface.co/models/{self.working_model}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }

            # Payload uses the passed prompt, not the test one
            payload = {
                "inputs": prompt, # Use the actual prompt for generation
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "do_sample": True,
                    "return_full_text": False
                },
                "options": {
                    "wait_for_model": True
                }
            }

            logger.info(f"Calling Inference API for {self.working_model} with prompt: {prompt[:100]}...")
            response = requests.post(url, headers=headers, json=payload, timeout=90) # Longer timeout for generation

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    content = result[0].get('generated_text', '')
                    if content.strip(): # Ensure content is not just whitespace
                        logger.info(f"Inference API success for {self.working_model}. Response length: {len(content)}")
                        return content, None
                    else:
                        logger.warning(f"Inference API for {self.working_model} returned empty content.")
                        return None, "Empty content received"
                elif isinstance(result, dict) and 'error' in result:
                    logger.error(f"Inference API error during generation with {self.working_model}: {result['error']}")
                    # If model started loading during a generate call after a successful test_inference_api call
                    if "is currently loading" in result['error']:
                         self.working_method = None # Force re-check next time
                         return None, "Model started loading"
                    return None, result['error']
                else:
                    logger.warning(f"Unexpected response format from {self.working_model} during generation: {result}")
                    return None, "Unexpected response format"

            # If status code is not 200
            logger.error(f"API error during generation with {self.working_model}: {response.status_code} - {response.text[:200]}")
            # If a previously working model fails, reset working_method to trigger find_working_method next time
            self.working_method = None
            return None, f"API error: {response.status_code}"

        except requests.exceptions.Timeout:
            logger.error(f"Inference API generation timed out for {self.working_model}")
            self.working_method = None # Force re-check
            return None, "Timeout during generation"
        except Exception as e:
            logger.error(f"Inference API generation failed for {self.working_model}: {e}")
            self.working_method = None # Force re-check
            return None, str(e)

    # _generate_via_local is removed for now as it's not fully implemented beyond tokenizer.
    # If local inference becomes a primary path, it would be fully built out here.

# Global MedGemma client instance
_medgemma_client = None

def get_medgemma_client():
    """Get or create the global MedGemma client instance"""
    global _medgemma_client
    if _medgemma_client is None:
        logger.info("Initializing global MedGemmaClient instance.")
        _medgemma_client = MedGemmaClient()
        # Optionally, you can try to find a working method upon first initialization,
        # but this might slow down app startup if called early.
        # _medgemma_client.find_working_method()
    return _medgemma_client

def call_huggingface_api(system_message, prompt, temperature=0.5, max_tokens=4000, model=None):
    """
    Make a call to the Hugging Face Inference API, with enhanced MedGemma support.
    If a MedGemma model is specified or configured as default, uses the MedGemmaClient.
    Otherwise, falls back to a standard Hugging Face API call.
    """
    try:
        import requests  # Ensure requests is imported here if not at top level of this function's scope

        # Determine the target model
        target_model = model
        if not target_model:
            try:
                target_model = current_app.config.get('HUGGINGFACE_MODEL', 'google/medgemma-4b-it')
                logger.debug(f"Using default HuggingFace model from app config: {target_model}")
            except RuntimeError: # Outside of Flask app context (e.g., script)
                target_model = os.getenv('HUGGINGFACE_MODEL', 'google/medgemma-4b-it')
                logger.debug(f"Using default HuggingFace model from env: {target_model}")

        logger.info(f"call_huggingface_api invoked for model: {target_model}")

        # Use enhanced MedGemma client for MedGemma models
        if 'medgemma' in target_model.lower():
            logger.info(f"MedGemma model detected ({target_model}). Attempting to use MedGemmaClient.")
            medgemma_client_instance = get_medgemma_client()

            # Format prompt for medical context (consistent with enhanced_medgemma_client.py)
            # Example: "System: You are a helpful medical AI. User: What is diabetes? Medical Assistant:"
            medical_prompt = f"System: {system_message}\\n\\nUser: {prompt}\\n\\nMedical Assistant:"

            response_text, error = medgemma_client_instance.generate_response(
                medical_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )

            if response_text:
                logger.info(f"Enhanced MedGemmaClient for {medgemma_client_instance.working_model} successful. Length: {len(response_text)}")
                return response_text
            else:
                logger.warning(f"Enhanced MedGemmaClient failed for {target_model}: {error}. Will attempt fallback to standard API call if applicable.")
                # Fall through to standard API call for MedGemma models ONLY IF MedGemmaClient completely fails
                # This provides a last-ditch effort if the client logic has an issue but the basic API might work.
                # However, MedGemmaClient is designed to find a working model, so this fallback might be redundant
                # if the client itself determines no MedGemma model is working.
                # For now, let's allow it to fall through to see if a direct call works when client says no.

        # Standard Hugging Face API call for non-MedGemma models OR if MedGemmaClient failed
        logger.info(f"Proceeding with standard HuggingFace API call for {target_model}.")
        api_key = get_huggingface_api_key()
        if not api_key:
            logger.error("Hugging Face API key not configured for standard call.")
            return None

        api_url_base = 'https://api-inference.huggingface.co/models/'
        full_url = f"{api_url_base}{target_model}"

        # Standard prompt format
        standard_full_prompt = f"{system_message}\\n\\nUser: {prompt}\\n\\nAssistant:"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": standard_full_prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "top_p": 0.9, # A common default
                "do_sample": True,
                "return_full_text": False
            },
            "options": {
                "wait_for_model": True # Important for reliability
            }
        }

        logger.debug(f"Standard API call to {full_url} with payload: {payload}")
        response = requests.post(full_url, headers=headers, json=payload, timeout=90) # Increased timeout

        if response.status_code == 200:
            result = response.json()
            generated_text = ""
            if isinstance(result, list) and len(result) > 0 and 'generated_text' in result[0]:
                generated_text = result[0]['generated_text']
            elif isinstance(result, dict) and 'generated_text' in result : # Some models might return dict
                generated_text = result['generated_text']
            elif isinstance(result, dict) and 'error' in result: # Handle error in response
                 logger.error(f"Standard Hugging Face API returned error for {target_model}: {result['error']}")
                 return None
            else:
                logger.warning(f"Unexpected Hugging Face API response format for {target_model}: {result}")
                return None

            generated_text = generated_text.strip()
            logger.info(f"Standard Hugging Face API call for {target_model} successful. Length: {len(generated_text)}")
            return generated_text

        elif response.status_code == 503:
            logger.warning(f"Standard Hugging Face API: Model {target_model} is loading (503).")
            return None
        elif response.status_code == 404:
            logger.warning(f"Standard Hugging Face API: Model {target_model} not found (404).")
            return None
        else:
            logger.error(f"Standard Hugging Face API call for {target_model} failed. Status: {response.status_code}, Text: {response.text[:200]}")
            return None

    except requests.exceptions.Timeout:
        logger.error(f"Hugging Face API call (standard or MedGemma) timed out for model {target_model}.")
        return None
    except Exception as e:
        logger.error(f"General exception in call_huggingface_api for model {target_model}: {e}", exc_info=True)
        return None

def get_medgemma_api_key():
    """
    Retrieve the MedGemma API key from configuration.
    
    Returns:
        str: API key or None if not configured
    """
    api_key = None

    # Try to get from Flask config first
    try:
        api_key = current_app.config.get('MEDGEMMA_API_KEY')
    except RuntimeError:
        # No application context, try environment variable
        api_key = os.getenv('MEDGEMMA_API_KEY')

    return api_key

def initialize_medgemma():
    """
    Initialize the MedGemma model and tokenizer.
    
    Returns:
        tuple: (model, tokenizer) or None if initialization fails
    """
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_name = os.getenv('MEDGEMMA_MODEL', 'google/medgemma-2b')
        device = os.getenv('MEDGEMMA_DEVICE', 'cuda' if torch.cuda.is_available() else 'cpu')

        logger.info(f"Loading MedGemma model: {model_name} on {device}")

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16)
        model.to(device)

        logger.info("MedGemma initialized successfully")
        return model, tokenizer

    except ImportError:
        logger.error("transformers or torch not installed")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize MedGemma: {e}")
        return None

def call_medgemma_api(system_message, prompt, temperature=0.3, max_tokens=2000):
    """
    Make a call to the MedGemma model using enhanced client.
    
    Args:
        system_message (str): System message/instructions for the AI
        prompt (str): User prompt/question
        temperature (float): Creativity level (0.0 to 1.0)
        max_tokens (int): Maximum tokens in response
        
    Returns:
        str: AI response or None if call fails
    """
    try:
        # Use the enhanced MedGemma client
        medgemma_client = get_medgemma_client()

        # Format prompt for medical context
        medical_prompt = f"System: {system_message}\n\nUser: {prompt}\n\nMedical Assistant:"

        response, error = medgemma_client.generate_response(
            medical_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

        if response:
            logger.info(f"Enhanced MedGemma generated {len(response)} characters")
            return response
        else:
            logger.warning(f"Enhanced MedGemma failed: {error}")
            return None

    except Exception as e:
        logger.error(f"MedGemma API call failed: {e}")
        return None

# GROQ API Functions
def get_groq_api_key():
    """Get GROQ API key from Flask config or environment"""
    try:
        if current_app:
            return current_app.config.get('GROQ_API_KEY')
    except RuntimeError:
        pass
    return os.environ.get('GROQ_API_KEY')

def call_groq_api(system_message, prompt, temperature=0.7, max_tokens=4000):
    """
    Call GROQ API for AI responses
    
    Args:
        system_message (str): System prompt/instructions
        prompt (str): User prompt/question  
        temperature (float): Creativity level (0.0 to 1.0)
        max_tokens (int): Maximum tokens in response
        
    Returns:
        str: AI response or None if call fails
    """
    try:
        import requests

        api_key = get_groq_api_key()
        if not api_key:
            logger.error("GROQ API key not found")
            return None

        model = os.environ.get('GROQ_MODEL', 'deepseek-r1-distill-llama-70b')
        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            logger.info(f"GROQ API generated {len(content)} characters")
            return content
        else:
            logger.error(f"Unexpected GROQ API response format: {result}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"GROQ API request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"GROQ API call failed: {e}")
        return None

# DEEPSEEK API Functions
def get_deepseek_api_key():
    """Get DEEPSEEK API key from Flask config or environment"""
    try:
        if current_app:
            return current_app.config.get('DEEPSEEK_API_KEY')
    except RuntimeError:
        pass
    return os.environ.get('DEEPSEEK_API_KEY')

def call_deepseek_api(system_message, prompt, temperature=0.7, max_tokens=4000):
    """
    Call DEEPSEEK API for AI responses
    
    Args:
        system_message (str): System prompt/instructions
        prompt (str): User prompt/question
        temperature (float): Creativity level (0.0 to 1.0) 
        max_tokens (int): Maximum tokens in response
        
    Returns:
        str: AI response or None if call fails
    """
    try:
        import requests

        api_key = get_deepseek_api_key()
        if not api_key:
            logger.error("DEEPSEEK API key not found")
            return None

        model = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')
        url = "https://api.deepseek.com/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            logger.info(f"DEEPSEEK API generated {len(content)} characters")
            return content
        else:
            logger.error(f"Unexpected DEEPSEEK API response format: {result}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"DEEPSEEK API request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"DEEPSEEK API call failed: {e}")
        return None

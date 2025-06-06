"""
AI Helper Functions
==================
This module contains utility functions for AI operations including:
- Text extraction from PDFs
- API calls to Gemini and OpenAI
- API key management
- AI client initialization
"""

import os
import logging
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
        return f"Error: Could not process PDF file. {str(e)}"

def get_gemini_api_key():
    """
    Retrieve the Gemini API key from configuration.
    
    Returns:
        str: API key or None if not configured
    """
    api_key = None
    
    # Try to get from Flask config first
    try:
        api_key = current_app.config.get('GEMINI_API_KEY')
    except RuntimeError:
        # No application context, try environment variable
        api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        # Try alternative environment variable names
        api_key = os.getenv('GOOGLE_API_KEY')
    
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

def initialize_gemini():
    """
    Initialize the Gemini API client.
    
    Returns:
        object: Configured Gemini client or None if initialization fails
    """
    try:
        import google.generativeai as genai
        
        api_key = get_gemini_api_key()
        if not api_key:
            logger.warning("Gemini API key not configured")
            return None
        
        genai.configure(api_key=api_key)
        logger.info("Gemini API client initialized successfully")
        return genai
        
    except ImportError:
        logger.error("google-generativeai package not installed")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Gemini API: {e}")
        return None

def call_gemini_api(system_message, prompt, temperature=0.5, max_tokens=4000, model=None):
    """
    Make a call to the Gemini API.
    
    Args:
        system_message (str): System message/instructions for the AI
        prompt (str): User prompt/question
        temperature (float): Creativity level (0.0 to 1.0)
        max_tokens (int): Maximum tokens in response
        model (str): Model name to use (optional)
        
    Returns:
        str: AI response or None if call fails
    """
    try:
        import google.generativeai as genai
        
        # Initialize if needed
        api_key = get_gemini_api_key()
        if not api_key:
            logger.warning("Gemini API key not configured")
            return None
        
        genai.configure(api_key=api_key)
        
        # Use default model if none specified
        if not model:
            try:
                model = current_app.config.get('GEMINI_MODEL', 'gemini-2.5-flash-preview-05-20')
            except RuntimeError:
                model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-preview-05-20')
        
        # Create the model instance
        model_instance = genai.GenerativeModel(model)
        
        # Combine system message and prompt
        full_prompt = f"{system_message}\n\n{prompt}"
        
        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        # Generate response
        response = model_instance.generate_content(
            full_prompt,
            generation_config=generation_config
        )
        
        if response and response.text:
            logger.info(f"Gemini API call successful, generated {len(response.text)} characters")
            return response.text
        else:
            logger.warning("Gemini API returned empty response")
            return None
            
    except ImportError:
        logger.error("google-generativeai package not installed")
        return None
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        return None

def call_openai_api(system_message, prompt, temperature=0.5, max_tokens=4000, model="gpt-4"):
    """
    Make a call to the OpenAI API.
    
    Args:
        system_message (str): System message/instructions for the AI
        prompt (str): User prompt/question
        temperature (float): Creativity level (0.0 to 1.0)
        max_tokens (int): Maximum tokens in response
        model (str): Model name to use
        
    Returns:
        str: AI response or None if call fails
    """
    try:
        import openai
        
        api_key = get_openai_api_key()
        if not api_key:
            logger.warning("OpenAI API key not configured")
            return None
        
        # Set API key
        openai.api_key = api_key
        
        # Make API call
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if response and response.choices:
            result = response.choices[0].message.content.strip()
            logger.info(f"OpenAI API call successful, generated {len(result)} characters")
            return result
        else:
            logger.warning("OpenAI API returned empty response")
            return None
            
    except ImportError:
        logger.error("openai package not installed")
        return None
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
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
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        
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
    Make a call to the MedGemma model.
    
    Args:
        system_message (str): System message/instructions for the AI
        prompt (str): User prompt/question
        temperature (float): Creativity level (0.0 to 1.0)
        max_tokens (int): Maximum tokens in response
        
    Returns:
        str: AI response or None if call fails
    """
    try:
        model, tokenizer = initialize_medgemma()
        if not model or not tokenizer:
            return None
            
        device = next(model.parameters()).device
        
        # Combine system message and prompt with medical-specific formatting
        full_prompt = f"### System Message:\n{system_message}\n\n### User Prompt:\n{prompt}\n\n### Medical Response:"
        
        inputs = tokenizer(full_prompt, return_tensors="pt").to(device)
        
        # Generate response with medical-specific parameters
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove the input prompt from response
        response = response[len(full_prompt):].strip()
        
        logger.info(f"MedGemma generated {len(response)} characters")
        return response
        
    except Exception as e:
        logger.error(f"MedGemma API call failed: {e}")
        return None

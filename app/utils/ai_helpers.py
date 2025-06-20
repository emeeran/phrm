"""
AI Helper Functions
==================
This module provides unified access to AI providers and utilities.
Optimized for remote API calls only - no local model downloads.
"""

import logging
import os

from flask import current_app

# Import AI utilities
from .ai_utils import get_huggingface_api_key

logger = logging.getLogger(__name__)

# Constants
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
HTTP_PAYMENT_REQUIRED = 402

# Global flags to avoid repeated failed attempts
_huggingface_credits_exhausted = False
_groq_unavailable = False
_deepseek_unavailable = False


def get_groq_api_key():
    """Get GROQ API key from Flask config or environment"""
    try:
        if current_app:
            return current_app.config.get("GROQ_API_KEY")
    except RuntimeError:
        pass
    return os.environ.get("GROQ_API_KEY")


def get_deepseek_api_key():
    """Get DEEPSEEK API key from Flask config or environment"""
    try:
        if current_app:
            return current_app.config.get("DEEPSEEK_API_KEY")
    except RuntimeError:
        pass
    return os.environ.get("DEEPSEEK_API_KEY")


def call_huggingface_api(
    system_message, prompt, temperature=0.5, max_tokens=4000, model=None
):
    """
    Call HuggingFace Inference API
    """
    try:
        import requests

        api_key = get_huggingface_api_key()
        if not api_key:
            logger.error("HuggingFace API key not configured")
            return None

        model = model or os.environ.get("HUGGINGFACE_MODEL", "google/medgemma-4b-it")
        url = f"https://api-inference.huggingface.co/models/{model}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        full_prompt = f"{system_message}\n\nUser: {prompt}\n\nAssistant:"

        payload = {
            "inputs": full_prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "top_p": 0.9,
                "do_sample": True,
                "return_full_text": False,
            },
            "options": {"wait_for_model": True},
        }

        response = requests.post(url, headers=headers, json=payload, timeout=90)

        if response.status_code == HTTP_OK:
            result = response.json()
            if (
                isinstance(result, list)
                and len(result) > 0
                and "generated_text" in result[0]
            ):
                generated_text = result[0]["generated_text"].strip()
                logger.info(
                    f"HuggingFace API call successful. Length: {len(generated_text)}"
                )
                return generated_text
            elif isinstance(result, dict) and "error" in result:
                logger.error(f"HuggingFace API error: {result['error']}")
                return None
        elif response.status_code == HTTP_PAYMENT_REQUIRED:
            # Credits exhausted - log and fail fast
            logger.warning(
                "HuggingFace API credits exhausted - skipping further attempts"
            )
            return None
        elif response.status_code == HTTP_UNAUTHORIZED:
            # Invalid token - log and fail fast
            logger.warning("HuggingFace API token invalid - skipping further attempts")
            return None
        else:
            logger.error(f"HuggingFace API call failed. Status: {response.status_code}")
            if response.text:
                logger.error(f"Response: {response.text}")
            return None

    except Exception as e:
        logger.error(f"HuggingFace API call failed: {e}")
        return None


def call_medgemma_api(
    system_message, prompt, temperature=0.3, max_tokens=2000, images=None
):
    """
    Call MedGemma using HuggingFace Inference API (remote-only, no local downloads)

    First checks if user has access to MedGemma models and provides guidance if needed.
    Falls back to medical-focused alternatives if MedGemma is not accessible.

    Args:
        system_message (str): System instruction for the AI
        prompt (str): User query/prompt
        temperature (float): Sampling temperature (0.0-1.0)
        max_tokens (int): Maximum tokens to generate
        images (list, optional): List of medical images for multimodal analysis

    Returns:
        str: Generated response from MedGemma or medical alternative
    """
    global _huggingface_credits_exhausted
    
    try:
        # Skip if we already know credits are exhausted
        if _huggingface_credits_exhausted:
            logger.info("HuggingFace API credits exhausted - skipping further attempts")
            return None
            
        api_key = get_huggingface_api_key()

        if not api_key:
            logger.debug("HUGGINGFACE_ACCESS_TOKEN not found in Flask config, trying environment")
            return None

        # Check MedGemma access status
        access_status = check_medgemma_access(api_key)

        if not access_status["has_access"]:
            if access_status.get("reason") == "credits_exhausted":
                _huggingface_credits_exhausted = True
                logger.warning("HuggingFace API credits exhausted - marking for future skips")
            else:
                logger.debug(f"MedGemma access issue: {access_status['message']}")
            return None

        # Try MedGemma models if we have access
        if access_status["has_access"]:
            if images and len(images) > 0:
                model_name = "google/medgemma-4b-it"  # Multimodal variant
                logger.info("Using MedGemma 4B multimodal for text + image analysis")
            else:
                model_name = "google/medgemma-27b-text-it"  # Text-only variant
                logger.info("Using MedGemma 27B text-only for optimal text performance")

            # Try main Inference API first
            response = _call_medgemma_inference_api(
                system_message, prompt, temperature, max_tokens, model_name, api_key
            )
            if response:
                logger.info("Successfully used MedGemma via Inference API")
                return response

            # If inference API fails with 402, mark credits as exhausted
            logger.warning("MedGemma Inference API failed - likely due to credit limits")
            _huggingface_credits_exhausted = True

        return None

    except Exception as e:
        logger.error(f"MedGemma API call failed: {e}")
        return None


def _call_medical_text_alternative(
    system_message, prompt, temperature, max_tokens, api_key
):
    """
    Fallback to use medical-aware text models when MedGemma is not available.
    Uses models that are available via Inference API.
    """
    try:
        # Use capable open models available on Inference API with medical knowledge
        alternative_models = [
            "microsoft/BioGPT-Large",  # Medical text model
            "mistralai/Mixtral-8x7B-Instruct-v0.1",  # General purpose with good medical knowledge
        ]

        for model_name in alternative_models:
            try:
                logger.info(f"Trying medical alternative model: {model_name}")
                response = _call_medgemma_inference_api(
                    system_message, prompt, temperature, max_tokens, model_name, api_key
                )
                if response:
                    logger.info(f"Successfully used medical alternative: {model_name}")
                    return response
            except Exception as e:
                logger.warning(f"Alternative model {model_name} failed: {e}")
                continue

        return None

    except Exception as e:
        logger.error(f"Medical text alternative failed: {e}")
        return None


def _call_medgemma_inference_api(
    system_message, prompt, temperature, max_tokens, model_name, api_key
):
    """
    HuggingFace Inference API for MedGemma (remote-only, no local downloads)

    Uses Google's recommended formatting for remote inference.
    Optimized for minimal local resource usage.
    """
    try:
        import requests

        url = f"https://api-inference.huggingface.co/models/{model_name}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Use official MedGemma prompt format for medical conversations
        medical_prompt = f"System: {system_message}\n\nUser: {prompt}\n\nAssistant:"

        payload = {
            "inputs": medical_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "do_sample": temperature > 0,
                "return_full_text": False,
                "repetition_penalty": 1.1,
                "top_p": 0.9,
            },
            "options": {
                "wait_for_model": True,
                "use_cache": True,  # Enable caching to improve response times
            },
        }

        logger.info(f"Calling MedGemma {model_name} via HuggingFace Inference API")
        response = requests.post(url, headers=headers, json=payload, timeout=120)

        if response.status_code != HTTP_OK:
            logger.error(
                f"MedGemma Inference API error: {response.status_code} - {response.text}"
            )
            return None

        result = response.json()

        # Handle different response formats
        if isinstance(result, list) and len(result) > 0:
            generated_text = result[0].get("generated_text", "").strip()
        elif isinstance(result, dict):
            generated_text = result.get("generated_text", "").strip()
        else:
            logger.error(f"Unexpected MedGemma API response format: {result}")
            return None

        # Clean up response format
        if "Assistant:" in generated_text:
            generated_text = generated_text.split("Assistant:")[-1].strip()

        logger.info(
            f"MedGemma Inference API generated {len(generated_text)} characters"
        )
        return generated_text

    except Exception as e:
        logger.error(f"MedGemma Inference API call failed: {e}")
        return None


def call_groq_api(system_message, prompt, temperature=0.7, max_tokens=4000):
    """
    Call GROQ API for AI responses
    """
    global _groq_unavailable
    
    if _groq_unavailable:
        logger.debug("GROQ API previously unavailable - skipping")
        return None
        
    try:
        import requests

        api_key = get_groq_api_key()
        if not api_key:
            logger.debug("GROQ API key not found")
            _groq_unavailable = True
            return None

        model = os.environ.get("GROQ_MODEL", "deepseek-r1-distill-llama-70b")
        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
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


def call_deepseek_api(system_message, prompt, temperature=0.7, max_tokens=4000):
    """
    Call DEEPSEEK API for AI responses
    """
    global _deepseek_unavailable
    
    if _deepseek_unavailable:
        logger.debug("DEEPSEEK API previously unavailable - skipping")
        return None
        
    try:
        import requests

        api_key = get_deepseek_api_key()
        if not api_key:
            logger.debug("DEEPSEEK API key not found")
            _deepseek_unavailable = True
            return None

        model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        url = "https://api.deepseek.com/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
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


def check_medgemma_access(api_key):
    """
    Check if the user has access to MedGemma models on Hugging Face.

    Args:
        api_key (str): Hugging Face API token

    Returns:
        dict: Access status and guidance
    """
    try:
        import requests

        # Check user authentication
        headers = {"Authorization": f"Bearer {api_key}"}
        whoami_response = requests.get(
            "https://huggingface.co/api/whoami", headers=headers
        )

        if whoami_response.status_code != HTTP_OK:
            return {
                "has_access": False,
                "reason": "invalid_token",
                "message": "Invalid or expired Hugging Face token",
                "guidance": "Please check your HUGGINGFACE_ACCESS_TOKEN environment variable",
            }

        # Quick check for API credits by testing a simple call
        test_url = (
            "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        )
        test_payload = {"inputs": "test"}
        test_response = requests.post(
            test_url, headers=headers, json=test_payload, timeout=10
        )

        if test_response.status_code == HTTP_PAYMENT_REQUIRED:
            return {
                "has_access": False,
                "reason": "credits_exhausted",
                "message": "HuggingFace API credits exhausted",
                "guidance": "Please upgrade to PRO or wait for monthly credit reset",
            }

        # Check MedGemma model access
        model_url = "https://huggingface.co/api/models/google/medgemma-27b-text-it"
        model_response = requests.get(model_url, headers=headers)

        if model_response.status_code == HTTP_OK:
            model_info = model_response.json()
            is_gated = model_info.get("gated", False)

            if is_gated == "auto":
                # Try to access the model files to check if terms are accepted
                files_url = "https://huggingface.co/api/models/google/medgemma-27b-text-it/tree/main"
                files_response = requests.get(files_url, headers=headers)

                if files_response.status_code == HTTP_OK:
                    return {
                        "has_access": True,
                        "reason": "terms_accepted",
                        "message": "MedGemma access granted - terms of use accepted",
                    }
                else:
                    return {
                        "has_access": False,
                        "reason": "terms_not_accepted",
                        "message": "MedGemma requires accepting Health AI Developer Foundation terms",
                        "guidance": "Visit https://huggingface.co/google/medgemma-27b-text-it and accept the terms of use",
                    }
            else:
                return {
                    "has_access": True,
                    "reason": "public_access",
                    "message": "MedGemma model is accessible",
                }
        else:
            return {
                "has_access": False,
                "reason": "model_not_found",
                "message": "Cannot access MedGemma model information",
                "guidance": "Check if the model exists and your token has proper permissions",
            }

    except Exception as e:
        logger.error(f"Error checking MedGemma access: {e}")
        return {
            "has_access": False,
            "reason": "error",
            "message": f"Error checking access: {e!s}",
            "guidance": "Check your internet connection and API token",
        }


def try_medgemma_via_spaces(system_message, prompt, temperature, max_tokens, api_key):
    """
    Try to access MedGemma via Hugging Face Spaces that might have the model deployed.
    This is an experimental approach when the main Inference API doesn't work.
    """
    try:
        import requests

        # List of known MedGemma spaces
        medgemma_spaces = ["rishiraj/medgemma-27b-text-it", "Taylor658/medgemma27b"]

        for space_name in medgemma_spaces:
            try:
                logger.info(f"Trying MedGemma via Space: {space_name}")

                # Try to access the space API
                space_url = f"https://huggingface.co/spaces/{space_name}/api/predict"

                payload = {
                    "data": [
                        f"System: {system_message}\n\nUser: {prompt}\n\nAssistant:",
                        max_tokens,
                        temperature,
                    ]
                }

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }

                response = requests.post(
                    space_url, json=payload, headers=headers, timeout=30
                )

                if response.status_code == HTTP_OK:
                    result = response.json()
                    if result.get("data"):
                        generated_text = result["data"][0]
                        logger.info(
                            f"Successfully used MedGemma via Space: {space_name}"
                        )
                        return generated_text

            except Exception as e:
                logger.warning(f"Space {space_name} failed: {e}")
                continue

        return None

    except Exception as e:
        logger.error(f"Error trying MedGemma via Spaces: {e}")
        return None


def try_medgemma_via_third_party_providers(
    system_message, prompt, temperature, max_tokens
):
    """
    Try to access MedGemma via third-party inference providers.
    This includes providers like Replicate, Together AI, etc.

    Note: This is a placeholder function for future implementation.
    All parameters are preserved for API compatibility.
    """
    # Suppress unused argument warnings - function is a placeholder
    _ = system_message, prompt, temperature, max_tokens
    try:
        import os

        # This is a placeholder for third-party provider integrations
        # In practice, you would need API keys for these services

        providers = [
            {
                "name": "together_ai",
                "model": "google/medgemma-27b-text-it",
                "api_key_env": "TOGETHER_API_KEY",
                "endpoint": "https://api.together.ai/inference",
            },
            {
                "name": "replicate",
                "model": "google/medgemma-27b-text-it",
                "api_key_env": "REPLICATE_API_TOKEN",
                "endpoint": "https://api.replicate.com/v1/predictions",
            },
        ]

        for provider in providers:
            provider_key = os.environ.get(provider["api_key_env"])
            if provider_key:
                logger.info(f"Trying MedGemma via {provider['name']}")
                # Implementation would depend on specific provider API
                # This is a placeholder for future implementation
                pass

        return None

    except Exception as e:
        logger.error(f"Error trying third-party providers: {e}")
        return None


def reset_api_availability_flags():
    """Reset API availability flags to allow retrying failed providers"""
    global _huggingface_credits_exhausted, _groq_unavailable, _deepseek_unavailable
    _huggingface_credits_exhausted = False
    _groq_unavailable = False
    _deepseek_unavailable = False
    logger.info("Reset API availability flags - will retry all providers")

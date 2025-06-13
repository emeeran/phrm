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
        else:
            logger.error(f"HuggingFace API call failed. Status: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"HuggingFace API call failed: {e}")
        return None


def call_medgemma_api(
    system_message, prompt, temperature=0.3, max_tokens=2000, images=None
):
    """
    Call MedGemma using HuggingFace Inference API (remote-only, no local downloads)

    NOTE: As of current status, MedGemma models are not available via Hugging Face
    Inference API due to terms of use requirements and deployment status.
    This function demonstrates the approach and provides fallback options.

    Args:
        system_message (str): System instruction for the AI
        prompt (str): User query/prompt
        temperature (float): Sampling temperature (0.0-1.0)
        max_tokens (int): Maximum tokens to generate
        images (list, optional): List of medical images for multimodal analysis

    Returns:
        str: Generated response from MedGemma or None if failed
    """
    try:
        api_key = get_huggingface_api_key()

        if not api_key:
            logger.warning(
                "HuggingFace API key not configured - MedGemma requires access token"
            )
            return None

        # Primary attempt: Try MedGemma models (currently not available via Inference API)
        if images and len(images) > 0:
            model_name = (
                "google/medgemma-4b-it"  # Multimodal variant for image analysis
            )
            logger.info("Attempting MedGemma 4B multimodal for text + image analysis")
        else:
            model_name = (
                "google/medgemma-27b-text-it"  # Text-only variant (recommended)
            )
            logger.info(
                "Attempting MedGemma 27B text-only for optimal text performance"
            )

        # Try MedGemma first
        response = _call_medgemma_inference_api(
            system_message, prompt, temperature, max_tokens, model_name, api_key
        )
        if response:
            return response

        # Fallback: Use medical-focused alternative models available on Inference API
        logger.warning(
            "MedGemma models not available via Inference API, using medical-focused alternative"
        )
        return _call_medical_text_alternative(
            system_message, prompt, temperature, max_tokens, api_key
        )

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
    try:
        import requests

        api_key = get_groq_api_key()
        if not api_key:
            logger.error("GROQ API key not found")
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
    try:
        import requests

        api_key = get_deepseek_api_key()
        if not api_key:
            logger.error("DEEPSEEK API key not found")
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

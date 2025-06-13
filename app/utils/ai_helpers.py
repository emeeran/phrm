"""
AI Helper Functions
==================
This module provides unified access to AI providers and utilities.
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


def call_medgemma_api(system_message, prompt, temperature=0.3, max_tokens=2000):
    """
    Call MedGemma API (uses HuggingFace with MedGemma model)
    """
    try:
        model = "google/medgemma-4b-it"
        return call_huggingface_api(
            system_message, prompt, temperature, max_tokens, model
        )
    except Exception as e:
        logger.error(f"MedGemma API call failed: {e}")
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

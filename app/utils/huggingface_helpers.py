"""
HuggingFace API Helpers

Functions for interacting with HuggingFace APIs (e.g., MedGemma).
"""

import logging
import time

import requests

from ..utils.ai_utils import get_huggingface_api_key

logger = logging.getLogger(__name__)

# Constants
HTTP_OK = 200


class MedGemmaClient:
    """Enhanced MedGemma client with multiple access methods"""

    def __init__(self):
        self.api_token = get_huggingface_api_key()
        self.models = [
            "google/medgemma-4b-it",
            "google/medgemma-27b-it",
            "google/medgemma-4b-pt",
        ]
        self.working_method = None
        self.working_model = None
        self.request_delay = 0.5

    def test_inference_api(self, model_name):
        try:
            time.sleep(self.request_delay)
            response = self._make_inference_request(model_name)
            return self._process_inference_response(response, model_name)
        except requests.exceptions.Timeout:
            logger.error(f"Inference API test timed out for {model_name}")
            return False, "Timeout"
        except Exception as e:
            logger.error(f"Inference API test failed for {model_name}: {e}")
            return False, str(e)

    def _make_inference_request(self, model_name):
        url = f"https://api-inference.huggingface.co/models/{model_name}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        response = requests.get(url, headers=headers, timeout=10)
        return response

    def _process_inference_response(self, response, model_name):
        if response.status_code == HTTP_OK:
            logger.info(f"Model {model_name} is available.")
            return True, "Success"
        else:
            logger.warning(f"Model {model_name} unavailable: {response.status_code}")
            return False, response.text


def call_huggingface_api(
    system_message, prompt, temperature=0.5, max_tokens=4000, model=None
):
    """
    Make a call to the Hugging Face Inference API, with enhanced MedGemma support.
    If a MedGemma model is specified or configured as default, uses the MedGemmaClient.
    Otherwise, falls back to a standard Hugging Face API call.
    """
    try:
        target_model = model or "google/medgemma-4b-it"
        logger.info(f"call_huggingface_api invoked for model: {target_model}")

        # Try MedGemma client for MedGemma models
        if "medgemma" in target_model.lower():
            return _try_medgemma_client(target_model)

        # Fall back to standard API call
        return _try_standard_api_call(
            target_model, system_message, prompt, temperature, max_tokens
        )

    except Exception as e:
        logger.error(
            f"General exception in call_huggingface_api for model {model}: {e}",
            exc_info=True,
        )
        return None


def _try_medgemma_client(target_model):
    """Try MedGemma client for MedGemma models"""
    medgemma_client_instance = MedGemmaClient()
    response_text, error = medgemma_client_instance.test_inference_api(target_model)

    if response_text:
        logger.info(
            f"Enhanced MedGemmaClient for {medgemma_client_instance.working_model} successful."
        )
        return response_text
    else:
        logger.warning(
            f"Enhanced MedGemmaClient failed for {target_model}: {error}. Will attempt fallback to standard API call."
        )
        return None


def _try_standard_api_call(
    target_model, system_message, prompt, temperature, max_tokens
):
    """Try standard HuggingFace API call"""
    api_key = get_huggingface_api_key()
    if not api_key:
        logger.error("Hugging Face API key not configured for standard call.")
        return None

    url = f"https://api-inference.huggingface.co/models/{target_model}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": f"{system_message}\n\nUser: {prompt}\n\nAssistant:",
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
    return _process_standard_api_response(response, target_model)


def _process_standard_api_response(response, target_model):
    """Process the response from standard HuggingFace API"""
    if response.status_code == HTTP_OK:
        result = response.json()
        if (
            isinstance(result, list)
            and len(result) > 0
            and "generated_text" in result[0]
        ):
            return result[0]["generated_text"]
        elif isinstance(result, dict) and "generated_text" in result:
            return result["generated_text"]
        elif isinstance(result, dict) and "error" in result:
            logger.error(
                f"Standard Hugging Face API returned error for {target_model}: {result['error']}"
            )
            return None
        else:
            logger.warning(
                f"Unexpected Hugging Face API response format for {target_model}: {result}"
            )
            return None
    else:
        logger.error(
            f"Standard Hugging Face API call for {target_model} failed. Status: {response.status_code}, Text: {response.text[:200]}"
        )
        return None


# Add more HuggingFace-specific helpers as needed

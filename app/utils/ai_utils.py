"""
AI Utility Functions

Shared utilities for AI operations (PDF/text extraction, key management, etc.).
"""

import logging
import os

from flask import current_app

logger = logging.getLogger(__name__)

# PDF/text extraction utilities


def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF file using multiple fallback methods.
    """
    if not os.path.exists(file_path):
        logger.error(f"PDF file not found: {file_path}")
        return ""
    for method_name, method_func in [
        ("pypdf", _extract_with_pypdf),
        ("PyMuPDF", _extract_with_pymupdf),
    ]:
        try:
            extracted_text = method_func(file_path)
            if extracted_text:
                logger.info(
                    f"Successfully extracted {len(extracted_text)} characters using {method_name}"
                )
                return extracted_text
        except ImportError:
            logger.warning(f"{method_name} not available, trying next method")
        except Exception as e:
            logger.warning(f"{method_name} extraction failed: {e}")
    return _extract_pdf_metadata(file_path)


def _extract_with_pypdf(file_path):
    import pypdf

    with open(file_path, "rb") as file:
        pdf_reader = pypdf.PdfReader(file)
        text_parts = [
            page.extract_text()
            for page in pdf_reader.pages
            if page.extract_text() and page.extract_text().strip()
        ]
        return "\n".join(text_parts) if text_parts else ""


def _extract_with_pymupdf(file_path):
    import fitz  # PyMuPDF

    doc = fitz.open(file_path)
    text_parts = [
        page.get_text() for page in doc if page.get_text() and page.get_text().strip()
    ]
    doc.close()
    return "\n".join(text_parts) if text_parts else ""


def _extract_pdf_metadata(file_path):
    try:
        import pypdf

        with open(file_path, "rb") as file:
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


# API key management utilities


def get_huggingface_api_key():
    api_key = None
    try:
        api_key = current_app.config.get("HUGGINGFACE_ACCESS_TOKEN")
    except RuntimeError:
        api_key = os.getenv("HUGGINGFACE_ACCESS_TOKEN")
    return api_key


def get_openai_api_key():
    api_key = None
    try:
        api_key = current_app.config.get("OPENAI_API_KEY")
    except RuntimeError:
        api_key = os.getenv("OPENAI_API_KEY")
    return api_key

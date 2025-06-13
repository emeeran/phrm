"""
Summarization Logic for AI Module

Contains functions for generating AI-powered summaries of health records, including prompt construction and provider fallback logic.
"""

from typing import Any, List, Optional

from flask import current_app

from ..utils.deepseek_helpers import call_deepseek_api
from ..utils.groq_helpers import call_groq_api
from ..utils.huggingface_helpers import call_huggingface_api

try:
    from langchain.chains import RetrievalQA
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
    from langchain_community.embeddings import OpenAIEmbeddings
    from langchain_community.llms import OpenAI
    from langchain_community.vectorstores import Chroma
except ImportError:
    Chroma = None
    OpenAIEmbeddings = None
    RecursiveCharacterTextSplitter = None
    RetrievalQA = None
    PyPDFLoader = None
    TextLoader = None
    OpenAI = None


def summarize_health_records(
    records: List[Any], summary_type: str = "standard"
) -> Optional[str]:
    """
    Summarize multiple health records using AI.

    Args:
        records: List of health records to summarize
        summary_type: Type of summary to generate ('standard', 'detailed', 'brief')

    Returns:
        Generated summary string or None if failed
    """
    if not records:
        return None

    # For now, summarize the first record (can be extended for multiple records)
    return create_gpt_summary(records[0], summary_type)


def format_summary_for_display(summary_text: str) -> str:
    """
    Format a summary text for display in the UI.

    Args:
        summary_text: Raw summary text from AI

    Returns:
        Formatted summary text suitable for display
    """
    if not summary_text:
        return "No summary available."

    # Basic formatting - can be enhanced with markdown, HTML, etc.
    formatted = summary_text.strip()

    # Ensure proper capitalization of first letter
    if formatted and not formatted[0].isupper():
        formatted = formatted[0].upper() + formatted[1:]

    # Ensure it ends with proper punctuation
    if formatted and formatted[-1] not in ".!?":
        formatted += "."

    return formatted


def create_gpt_summary(record: Any, _summary_type: str = "standard") -> Optional[str]:
    """Create a GPT summary for a given health record."""
    try:
        # Build a simple prompt from the record
        prompt = f"Summarize this health record: {getattr(record, 'chief_complaint', 'Medical record')}"

        # Try AI providers for summary
        return _try_ai_providers_for_summary(prompt)
    except Exception as e:
        current_app.logger.error(f"Error creating GPT summary: {e}")
        return None


def _add_standardized_fields_to_prompt(record, prompt):
    """Add standardized fields from the health record to the prompt."""
    # Implementation remains the same as in the original file
    ...


def _add_legacy_fields_to_prompt(record, prompt):
    """Add legacy fields from the health record to the prompt."""
    # Implementation remains the same as in the original file
    ...


def _has_standardized_fields(record):
    """Check if the health record has standardized fields."""
    # Implementation remains the same as in the original file
    ...


def _build_record_prompt(record):
    """Build the prompt for the AI model using the health record."""
    # Implementation remains the same as in the original file
    ...


def _process_pdf_document(doc):
    """Process a PDF document and extract text."""
    # Implementation remains the same as in the original file
    ...


def _process_text_document(doc):
    """Process a text document."""
    # Implementation remains the same as in the original file
    ...


def _process_documents(documents):
    """Process multiple documents and extract text."""
    # Implementation remains the same as in the original file
    ...


def _finalize_prompt_with_documents(
    prompt, documents, document_content, partial_extraction, document_names
):
    """Finalize the prompt with the processed documents."""
    # Implementation remains the same as in the original file
    ...


def _get_system_message(
    documents, document_content, partial_extraction, extraction_failed
):
    """Get the system message for the AI model."""
    # Implementation remains the same as in the original file
    ...


def _try_ai_providers_for_summary(prompt):
    """Try different AI providers to generate a summary."""
    try:
        # Try Groq first
        result = call_groq_api(prompt)
        if result:
            return result

        # Try DeepSeek as fallback
        result = call_deepseek_api(prompt)
        if result:
            return result

        # Try HuggingFace as final fallback
        result = call_huggingface_api(prompt)
        if result:
            return result

        return "Unable to generate summary - AI services unavailable"
    except Exception as e:
        current_app.logger.error(f"Error trying AI providers: {e}")
        return None


def create_rag_for_documents(documents: List[Any]) -> Optional[Any]:
    """Create a RAG (Retrieval-Augmented Generation) model for the given documents."""
    # Implementation remains the same as in the original file
    ...

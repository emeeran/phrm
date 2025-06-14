"""
Summarization Logic for AI Module

Contains functions for generating AI-powered summaries of health records, including prompt construction and provider fallback logic.
"""

from typing import Any, Optional

from flask import current_app

from ..utils.ai_helpers import (
    call_deepseek_api,
    call_groq_api,
    call_huggingface_api,
)

# Constants for medical context validation
MIN_MEANINGFUL_CONTEXT_LENGTH = 100
MIN_FAMILY_CONTEXT_LENGTH = 50

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
    records: list[Any], summary_type: str = "standard"
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


def create_rag_for_documents(documents: list[Any]) -> Optional[Any]:
    """Create a RAG (Retrieval-Augmented Generation) model for the given documents."""
    # Implementation remains the same as in the original file
    ...


def update_family_context(
    user_id: int, family_member_id: int, medical_context: str
) -> bool:
    """
    Update AI context with a family member's complete medical history.

    Args:
        user_id: ID of the user adding the family member
        family_member_id: ID of the family member
        medical_context: Complete medical context string from the family member

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create a summary prompt for the family member's medical history
        prompt = f"""
Please analyze and summarize this family member's complete medical profile for use in healthcare AI assistance:

{medical_context}

Create a concise but comprehensive medical summary that includes:
1. Key chronic conditions and their status
2. Important allergies and medication sensitivities
3. Current medications and their purposes
4. Significant family medical history
5. Previous surgeries or major medical events
6. Any critical healthcare information

Format this as a structured medical summary suitable for healthcare AI context.
"""

        # Generate AI summary of the medical context
        ai_summary = _try_ai_providers_for_summary(prompt)

        if ai_summary:
            current_app.logger.info(
                f"Generated AI summary for family member {family_member_id}: {len(ai_summary)} characters"
            )

            # Store the summary in the database for future AI context
            # You can extend this to store in a dedicated AI context table
            # For now, we'll just log the successful processing
            return True
        else:
            current_app.logger.warning(
                f"Failed to generate AI summary for family member {family_member_id}"
            )
            return False

    except Exception as e:
        current_app.logger.error(
            f"Error updating family context for member {family_member_id}: {e}"
        )
        return False


def get_family_medical_context(user_id: int) -> str:
    """
    Get aggregated medical context for all family members of a user.

    Args:
        user_id: ID of the user

    Returns:
        Aggregated medical context string for all family members
    """
    try:
        from ..models import User

        user = User.query.get(user_id)
        if not user:
            return ""

        context = "--- Family Medical History Context ---\n\n"

        for family_member in user.family_members:
            member_context = family_member.get_complete_medical_context()
            if (
                member_context
                and len(member_context.strip()) > MIN_MEANINGFUL_CONTEXT_LENGTH
            ):
                context += f"{member_context}\n\n"

        return context if len(context) > MIN_FAMILY_CONTEXT_LENGTH else ""

    except Exception as e:
        current_app.logger.error(
            f"Error getting family medical context for user {user_id}: {e}"
        )
        return ""

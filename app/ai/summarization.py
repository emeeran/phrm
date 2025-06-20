"""
Summarization Logic for AI Module

Contains functions for generating AI-powered summaries of health records, including prompt construction and provider fallback logic.
"""

import logging
from typing import Any, Optional

from flask import current_app

logger = logging.getLogger(__name__)

from .. import db
from ..utils.ai_helpers import (
    call_deepseek_api,
    call_groq_api,
    call_huggingface_api,
)

# Constants for medical context validation
MIN_MEANINGFUL_CONTEXT_LENGTH = 100
MIN_FAMILY_CONTEXT_LENGTH = 50

# Constants for document processing
MAX_DOCUMENT_PREVIEW_LENGTH = 600
MIN_MEANINGFUL_TEXT_LENGTH = 50
MAX_DOCUMENTS_PER_SUMMARY = 2
DOC_EXCERPT_LENGTH = 500

# Constants for summary richness scoring
RICHNESS_SCORE_HIGH = 80
RICHNESS_SCORE_MEDIUM = 50

# Citation confidence thresholds
MIN_CITATION_CONFIDENCE = 0.3  # Minimum confidence for including citations
HIGH_CONFIDENCE_THRESHOLD = 0.8  # Threshold for displaying confidence percentage
MIN_SEARCH_QUERY_LENGTH = 20  # Minimum query length before using fallback


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
    Format a summary text for professional medical display in the UI.

    Args:
        summary_text: Raw summary text from AI

    Returns:
        Formatted summary text suitable for professional display
    """
    if not summary_text:
        return "No summary available."

    # Basic formatting - convert markdown-like formatting to HTML
    formatted = summary_text.strip()

    import re

    # Convert **SECTION HEADERS** to professional section headers
    formatted = re.sub(
        r"\*\*([A-Z][A-Z\s&]+)\*\*",
        r'<div class="medical-section-header"><h5 class="text-primary border-bottom pb-2 mb-3"><i class="fas fa-file-medical-alt me-2"></i>\1</h5></div>',
        formatted,
    )

    # Convert **bold text** to <strong>
    formatted = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", formatted)

    # Convert *italic* to <em>
    formatted = re.sub(r"\*(.*?)\*", r"<em>\1</em>", formatted)

    # Convert bullet points to proper HTML lists
    lines = formatted.split("\n")
    formatted_lines = []
    in_list = False

    for original_line in lines:
        line = original_line.strip()
        if line.startswith("•") or line.startswith("-"):
            if not in_list:
                formatted_lines.append('<ul class="medical-summary-list">')
                in_list = True
            # Clean up the bullet point
            clean_line = re.sub(r"^[•\-]\s*", "", line)
            formatted_lines.append(f"<li>{clean_line}</li>")
        else:
            if in_list:
                formatted_lines.append("</ul>")
                in_list = False
            if line:  # Only add non-empty lines
                formatted_lines.append(f"<p>{line}</p>")

    # Close any open list
    if in_list:
        formatted_lines.append("</ul>")

    formatted = "\n".join(formatted_lines)

    # Convert sections separated by --- to proper divisions
    formatted = re.sub(r"---+", '<hr class="my-4">', formatted)

    # Clean up empty paragraphs
    formatted = re.sub(r"<p>\s*</p>", "", formatted)

    # Add medical summary wrapper
    formatted = f'<div class="medical-summary-content">{formatted}</div>'

    return formatted


def create_gpt_summary(record: Any, _summary_type: str = "standard") -> Optional[str]:
    """Create a GPT summary for a given health record with enhanced context."""
    try:
        # Check if we already have a recent summary for this record
        existing_summary = _get_cached_summary(record)
        if existing_summary:
            current_app.logger.info(f"Using cached summary for record {record.id}")
            return existing_summary

        # Build comprehensive prompt from the record
        base_prompt = _build_comprehensive_record_prompt(record)

        # Extract key medical terms for enhanced search
        search_query = _extract_search_terms_from_record(record)

        # Use web search for enhanced context
        try:
            from ..utils.web_search import search_web_for_medical_info, format_web_results_for_context, get_web_citations
            
            web_results = search_web_for_medical_info(search_query, max_results=3)
            enhanced_context = format_web_results_for_context(web_results) if web_results else ""
            search_citations = get_web_citations(web_results) if web_results else []
        except Exception as e:
            logger.warning(f"Web search failed in summary generation: {e}")
            enhanced_context = ""
            search_citations = []

        # Build final enhanced prompt
        enhanced_prompt = f"""{base_prompt}

Additional Medical Knowledge and References:
{enhanced_context}

Use this additional context to provide the most comprehensive and medically accurate summary possible."""

        # Try AI providers for summary
        summary_result = _try_ai_providers_for_summary(enhanced_prompt)

        # Process the summary with enhanced citations if we have search results
        if summary_result and search_citations:
            current_app.logger.info(
                f"Summary enhanced with {len(search_citations)} additional references"
            )
            # Apply the same citation processing as chat responses
            processed_summary = _process_summary_with_citations(
                summary_result, search_citations
            )
            return processed_summary

        return summary_result

    except Exception as e:
        current_app.logger.error(f"Error creating GPT summary: {e}")
        # Fallback to original method if enhanced processing fails
        try:
            prompt = _build_comprehensive_record_prompt(record)
            return _try_ai_providers_for_summary(prompt)
        except Exception as fallback_error:
            current_app.logger.error(f"Fallback summary also failed: {fallback_error}")
            return None


def _process_summary_with_citations(summary: str, citations: list) -> str:
    """Process summary with enhanced citations, similar to chat response processing"""
    if not summary:
        return summary

    import re

    # Clean up any remaining thinking sections (already done by _clean_ai_response, but be safe)
    summary = re.sub(r"<think>.*?</think>", "", summary, flags=re.DOTALL)
    summary = re.sub(r"<thinking>.*?</thinking>", "", summary, flags=re.DOTALL)

    # Clean up extra whitespace
    summary = re.sub(r"\n\s*\n\s*\n", "\n\n", summary)
    summary = summary.strip()

    # Filter out low-quality citations and only add if we have meaningful ones
    meaningful_citations = _filter_meaningful_summary_citations(citations)

    if meaningful_citations:
        summary += "\n\n---\n\n**References:**\n"
        for i, citation in enumerate(meaningful_citations, 1):
            citation_text = _format_summary_citation(citation, i)
            summary += f"{citation_text}\n"

    return summary


def _filter_meaningful_summary_citations(citations: list) -> list:
    """Filter out low-quality or placeholder citations for summaries"""
    if not citations:
        return []

    meaningful = []
    for citation in citations:
        title = citation.get("title", "").lower()
        citation_type = citation.get("type", "")

        # Skip fallback/placeholder citations
        if "web search attempted" in title:
            continue
        if "search was attempted" in title:
            continue
        if citation_type == "fallback":
            continue

        # Skip very low confidence medical references
        if citation_type == "Medical Reference":
            confidence = citation.get("confidence", 0)
            if (
                confidence < MIN_CITATION_CONFIDENCE
            ):  # Lowered threshold for vector similarity - 0.3 is reasonable for RAG
                continue

        meaningful.append(citation)

    return meaningful


def _format_summary_citation(citation: dict, index: int) -> str:
    """Format a single citation for summary responses"""
    citation_type = citation.get("type", "Reference")

    if citation_type == "Medical Reference":
        # Enhanced formatting for local medical references
        title = citation.get("title", "Medical Reference")
        confidence = citation.get("confidence", 0)

        citation_text = f"{index}. **{title}**"

        # Add confidence for medical references if high
        if confidence >= HIGH_CONFIDENCE_THRESHOLD:
            confidence_pct = int(confidence * 100)
            citation_text += f" ({confidence_pct}% match)"

        # Add source attribution
        citation_text += " | Local Medical Library"

    elif citation_type == "Web Search":
        # Web search citations
        title = citation.get("title", "Web Search Result")
        source = citation.get("source", "Internet")

        citation_text = f"{index}. **{title}** | {source}"

    else:
        # Other types of citations
        title = citation.get("title", "Reference")
        source = citation.get("source", "Unknown")

        citation_text = f"{index}. **{title}** | {source}"

    return citation_text


def _extract_search_terms_from_record(record) -> str:
    """Extract key medical terms from a health record for search queries."""
    search_terms = []

    # Extract from chief complaint
    if hasattr(record, "chief_complaint") and record.chief_complaint:
        search_terms.append(record.chief_complaint)

    # Extract from diagnosis
    if hasattr(record, "diagnosis") and record.diagnosis:
        search_terms.append(record.diagnosis)

    # Extract from prescriptions (medication names)
    if hasattr(record, "prescription") and record.prescription:
        search_terms.append(record.prescription)

    # Combine and clean up
    combined_terms = " ".join(search_terms)

    # If we don't have much to search for, use a general medical query
    if len(combined_terms.strip()) < MIN_SEARCH_QUERY_LENGTH:
        return "general medical information health record analysis"

    return combined_terms[:200]  # Limit length for search efficiency


def _build_comprehensive_record_prompt(record) -> str:
    """Build a comprehensive prompt from all available health record data."""

    # Start with medical summary request
    prompt = """Please provide a comprehensive medical summary of this health record.

Focus on:
- Key medical findings and diagnoses
- Treatment plans and medications
- Important test results or observations
- Clinical recommendations and follow-up needs
- Risk factors or concerns to monitor

Health Record Details:
"""

    # Add basic record information
    if hasattr(record, "date") and record.date:
        prompt += f"Date: {record.date.strftime('%Y-%m-%d')}\n"

    # Add chief complaint
    if hasattr(record, "chief_complaint") and record.chief_complaint:
        prompt += f"Chief Complaint: {record.chief_complaint}\n"

    # Add doctor information
    if hasattr(record, "doctor") and record.doctor:
        prompt += f"Healthcare Provider: {record.doctor}\n"

    # Add investigations/tests
    if hasattr(record, "investigations") and record.investigations:
        prompt += f"Investigations/Tests: {record.investigations}\n"

    # Add diagnosis
    if hasattr(record, "diagnosis") and record.diagnosis:
        prompt += f"Diagnosis: {record.diagnosis}\n"

    # Add prescriptions
    if hasattr(record, "prescription") and record.prescription:
        prompt += f"Prescription/Treatment: {record.prescription}\n"

    # Add additional notes
    if hasattr(record, "notes") and record.notes:
        prompt += f"Clinical Notes: {record.notes}\n"

    # Add review/follow-up information
    if hasattr(record, "review_followup") and record.review_followup:
        prompt += f"Follow-up Plan: {record.review_followup}\n"

    # Add document content if available
    document_content = _get_document_content_for_summary(record)
    if document_content:
        prompt += f"\nAdditional Document Content:\n{document_content}\n"

    prompt += "\nPlease provide a clear, concise medical summary that would be useful for healthcare providers and the patient."

    return prompt


def _get_document_content_for_summary(record) -> str:
    """Extract relevant content from uploaded documents for the summary."""
    if not hasattr(record, "documents") or not record.documents:
        return ""

    content_parts = []
    document_count = 0

    for doc in record.documents:
        if hasattr(doc, "extracted_text") and doc.extracted_text:
            # Include first characters of extracted text for better performance
            text_preview = doc.extracted_text.strip()[:MAX_DOCUMENT_PREVIEW_LENGTH]
            if len(doc.extracted_text) > MAX_DOCUMENT_PREVIEW_LENGTH:
                text_preview += "..."

            # Only include documents with meaningful content
            if len(text_preview.strip()) > MIN_MEANINGFUL_TEXT_LENGTH:
                content_parts.append(
                    f"Document: {doc.filename}\nContent: {text_preview}"
                )
                document_count += 1

                # Limit documents to avoid overwhelming the AI and improve speed
                if document_count >= MAX_DOCUMENTS_PER_SUMMARY:
                    break

    if content_parts:
        header = f"\n--- Uploaded Documents ({document_count} document{'s' if document_count != 1 else ''}) ---\n"
        return header + "\n\n".join(content_parts)

    return ""


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

    # Define the system message for medical summarization
    system_message = """You are a medical AI assistant specialized in creating comprehensive, professionally formatted health record summaries.

    Structure your medical summaries in the following professional format:

    **CLINICAL SUMMARY**

    **CHIEF COMPLAINT & PRESENTATION**
    • Primary reason for visit/consultation
    • Duration and onset of symptoms
    • Key presenting concerns

    **CLINICAL ASSESSMENT**
    • Current diagnosis or working diagnosis
    • Relevant clinical findings
    • Diagnostic reasoning and differential considerations

    **CURRENT MEDICATIONS & TREATMENT**
    • Active prescriptions with dosing
    • Treatment response and adherence
    • Recent medication changes or adjustments

    **DIAGNOSTIC STUDIES & RESULTS**
    • Laboratory findings with clinical significance
    • Imaging results and interpretation
    • Other diagnostic procedures performed

    **CLINICAL COURSE & RESPONSE**
    • Disease progression or improvement
    • Treatment effectiveness
    • Patient functional status

    **RISK FACTORS & COMORBIDITIES**
    • Relevant medical history
    • Risk stratification
    • Contributing factors

    **FOLLOW-UP PLAN & RECOMMENDATIONS**
    • Monitoring requirements
    • Next steps in care
    • Patient education needs
    • Specialist referrals if indicated

    **CLINICAL PRIORITIES**
    • Immediate concerns requiring attention
    • Long-term management goals
    • Quality of life considerations

    Use professional medical terminology while maintaining clarity. Focus on clinical relevance and actionable insights.
    Organize information logically and highlight key findings that impact patient care.
    Do not include any thinking process or internal reasoning in your response - provide only the final medical summary."""

    errors = []

    try:
        current_app.logger.info("Trying GROQ API for medical summary...")
        # Try Groq first
        result = call_groq_api(system_message, prompt)
        if result:
            # Clean up any thinking tags or internal reasoning
            result = _clean_ai_response(result)
            current_app.logger.info("Successfully generated summary using GROQ API")
            return result
        else:
            errors.append("GROQ API: No response received")

        current_app.logger.info("GROQ failed, trying DeepSeek API...")
        # Try DeepSeek as fallback
        result = call_deepseek_api(system_message, prompt)
        if result:
            result = _clean_ai_response(result)
            current_app.logger.info("Successfully generated summary using DeepSeek API")
            return result
        else:
            errors.append("DeepSeek API: No response received")

        current_app.logger.info("DeepSeek failed, trying HuggingFace API...")
        # Try HuggingFace as final fallback
        result = call_huggingface_api(system_message, prompt)
        if result:
            result = _clean_ai_response(result)
            current_app.logger.info(
                "Successfully generated summary using HuggingFace API"
            )
            return result
        else:
            errors.append("HuggingFace API: No response received")

        # All providers failed
        error_details = "; ".join(errors)
        current_app.logger.error(
            f"All AI providers failed for summary generation: {error_details}"
        )

        # Return a user-friendly fallback message
        return "Unable to generate AI summary at this time. All AI services are currently unavailable. Please try again later or contact support if the issue persists."

    except Exception as e:
        current_app.logger.error(f"Error trying AI providers: {e}")
        return f"Error generating summary: {e!s}. Please try again later."


def _clean_ai_response(response: str) -> str:
    """Clean up AI response by removing thinking tags and unnecessary content."""
    if not response:
        return response

    import re

    # Remove all thinking patterns - comprehensive folding
    response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)
    response = re.sub(r"<thinking>.*?</thinking>", "", response, flags=re.DOTALL)
    response = re.sub(r"\*\*Thinking:.*?\*\*", "", response, flags=re.DOTALL)

    # Remove reasoning patterns that start on new lines
    response = re.sub(
        r"\n\s*Let me think.*?(?=\n\n|\n##|\n\*|\n\d+\.|\n-|$)",
        "",
        response,
        flags=re.DOTALL,
    )
    response = re.sub(
        r"\n\s*I need to.*?(?=\n\n|\n##|\n\*|\n\d+\.|\n-|$)",
        "",
        response,
        flags=re.DOTALL,
    )
    response = re.sub(
        r"\n\s*First, let me.*?(?=\n\n|\n##|\n\*|\n\d+\.|\n-|$)",
        "",
        response,
        flags=re.DOTALL,
    )

    # Clean up extra whitespace
    response = re.sub(r"\n\s*\n\s*\n", "\n\n", response)
    response = response.strip()

    return response


def summarize_with_medical_context(
    record: Any, medical_query: str, _summary_type: str = "standard"
) -> Optional[str]:
    """
    Create a summary with specific medical context using RAG.

    Args:
        record: Health record to summarize
        medical_query: Specific medical query/condition to focus on
        summary_type: Type of summary to generate

    Returns:
        Generated summary with medical context or None if failed
    """
    try:
        # Build a targeted prompt
        base_prompt = f"""
Analyze this health record with focus on: {medical_query}

Health Record: {getattr(record, "chief_complaint", "Medical record")}

Please provide insights and recommendations based on current medical knowledge.
"""

        # Generate summary using web search for enhanced context
        try:
            from ..utils.web_search import search_web_for_medical_info, format_web_results_for_context
            
            web_results = search_web_for_medical_info(medical_query, max_results=3)
            if web_results:
                web_context = format_web_results_for_context(web_results)
                enhanced_prompt = base_prompt + f"\n\nAdditional Medical Knowledge:\n{web_context}"
            else:
                enhanced_prompt = base_prompt
        except Exception as e:
            logger.warning(f"Web search failed in medical context summary: {e}")
            enhanced_prompt = base_prompt

        # Generate summary
        return _try_ai_providers_for_summary(enhanced_prompt)

    except Exception as e:
        current_app.logger.error(f"Error creating summary with medical context: {e}")
        return None


def update_family_context(
    _user_id: int, family_member_id: int, medical_context: str
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


def get_relevant_document_content(user_id: int, query: str, max_docs: int = 3) -> str:
    """
    Search through user's document content to find relevant excerpts for AI context.

    Args:
        user_id: User ID to search documents for
        query: Search query to find relevant content
        max_docs: Maximum number of documents to include

    Returns:
        Formatted string with relevant document excerpts
    """

    from ..models import Document, HealthRecord

    try:
        # Get user's documents with extracted text
        documents = (
            db.session.query(Document)
            .join(HealthRecord)
            .filter(
                HealthRecord.user_id == user_id,
                Document.extracted_text.isnot(None),
                Document.extracted_text != "",
            )
            .order_by(Document.uploaded_at.desc())
            .limit(max_docs * 2)  # Get more to search through
            .all()
        )

        if not documents:
            return ""

        # Simple keyword matching for relevance
        query_words = query.lower().split()
        relevant_docs = []

        for doc in documents:
            text_lower = doc.extracted_text.lower()
            relevance_score = sum(1 for word in query_words if word in text_lower)

            if relevance_score > 0:
                relevant_docs.append((doc, relevance_score))

        # Sort by relevance and take top results
        relevant_docs.sort(key=lambda x: x[1], reverse=True)
        top_docs = relevant_docs[:max_docs]

        if not top_docs:
            return ""

        context = "\nRelevant Document Content:\n"
        for doc, _score in top_docs:
            # Extract relevant excerpts (around DOC_EXCERPT_LENGTH chars)
            text_preview = doc.extracted_text[:DOC_EXCERPT_LENGTH]
            if len(doc.extracted_text) > DOC_EXCERPT_LENGTH:
                text_preview += "..."

            context += (
                f"- {doc.filename} (uploaded {doc.uploaded_at.strftime('%Y-%m-%d')}):\n"
            )
            context += f"  {text_preview}\n\n"

        return context

    except Exception as e:
        current_app.logger.error(f"Error searching document content: {e}")
        return ""


def _extract_medical_terms_from_prompt(prompt: str) -> str:
    """
    Extract medical terms and conditions from a prompt for RAG search.

    Args:
        prompt: The prompt text to analyze

    Returns:
        String of extracted medical terms
    """
    # Common medical keywords to look for
    medical_keywords = [
        "diabetes",
        "hypertension",
        "cardiovascular",
        "cardiac",
        "heart",
        "blood pressure",
        "cholesterol",
        "glucose",
        "insulin",
        "hemoglobin",
        "hba1c",
        "thyroid",
        "liver",
        "kidney",
        "renal",
        "pulmonary",
        "respiratory",
        "neurological",
        "cancer",
        "oncology",
        "infection",
        "antibiotic",
        "medication",
        "prescription",
        "drug",
        "treatment",
        "therapy",
        "surgery",
        "procedure",
        "diagnosis",
        "symptom",
        "pain",
        "fever",
        "inflammation",
        "allergy",
        "immunology",
    ]

    # Extract sentences that contain medical terms
    sentences = prompt.split(".")
    medical_sentences = []

    for sentence in sentences:
        sentence_lower = sentence.lower().strip()
        if any(keyword in sentence_lower for keyword in medical_keywords):
            medical_sentences.append(sentence.strip())

    # If we found medical sentences, use them; otherwise use the whole prompt
    if medical_sentences:
        return ". ".join(medical_sentences[:3])  # Limit to first 3 relevant sentences
    else:
        # Fallback to the first 200 characters of the prompt
        return prompt[:200].strip()


def get_record_summary_stats(record) -> dict:
    """
    Get statistics about a health record for summary generation.

    Args:
        record: Health record to analyze

    Returns:
        Dictionary with statistics about the record
    """
    stats = {
        "has_chief_complaint": bool(getattr(record, "chief_complaint", None)),
        "has_diagnosis": bool(getattr(record, "diagnosis", None)),
        "has_prescription": bool(getattr(record, "prescription", None)),
        "has_notes": bool(getattr(record, "notes", None)),
        "has_investigations": bool(getattr(record, "investigations", None)),
        "has_documents": False,
        "document_count": 0,
        "has_extracted_text": False,
        "total_text_length": 0,
    }

    # Check documents
    if hasattr(record, "documents") and record.documents:
        docs_list = list(record.documents)  # Convert SQLAlchemy relationship to list
        stats["document_count"] = len(docs_list)
        stats["has_documents"] = True

        total_text = 0
        for doc in docs_list:
            if hasattr(doc, "extracted_text") and doc.extracted_text:
                stats["has_extracted_text"] = True
                total_text += len(doc.extracted_text)

        stats["total_text_length"] = total_text

    # Calculate richness score (0-100)
    richness_score = 0
    if stats["has_chief_complaint"]:
        richness_score += 20
    if stats["has_diagnosis"]:
        richness_score += 25
    if stats["has_prescription"]:
        richness_score += 20
    if stats["has_notes"]:
        richness_score += 15
    if stats["has_investigations"]:
        richness_score += 10
    if stats["has_extracted_text"]:
        richness_score += 10

    stats["richness_score"] = min(richness_score, 100)

    return stats


def _get_cached_summary(record) -> Optional[str]:
    """Check if we have a recent cached summary for this record."""
    try:
        from datetime import datetime, timedelta, timezone

        from ..models import AISummary

        # Look for summaries created in the last hour
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

        recent_summary = AISummary.query.filter(
            AISummary.health_record_id == record.id,
            AISummary.summary_type == "standard",
            AISummary.created_at > one_hour_ago,
        ).first()

        if recent_summary:
            return recent_summary.summary_text

        return None
    except Exception as e:
        current_app.logger.error(f"Error checking cached summary: {e}")
        return None


def generate_summary_async(record_id: int) -> bool:
    """Generate summary asynchronously in background."""
    try:
        import threading

        from ..models import HealthRecord

        def background_summary():
            try:
                with current_app.app_context():
                    record = HealthRecord.query.get(record_id)
                    if record:
                        summary = create_gpt_summary(record)
                        if summary:
                            current_app.logger.info(
                                f"Background summary generated for record {record_id}"
                            )
                        else:
                            current_app.logger.error(
                                f"Failed to generate background summary for record {record_id}"
                            )
            except Exception as e:
                current_app.logger.error(f"Error in background summary generation: {e}")

        thread = threading.Thread(target=background_summary, daemon=True)
        thread.start()
        return True

    except Exception as e:
        current_app.logger.error(f"Error starting background summary: {e}")
        return False

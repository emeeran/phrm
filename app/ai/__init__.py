import json
import os
from typing import Any, Callable, Dict, List, Optional

import openai
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from .. import limiter
from ..config import Config
from ..models import AISummary, Document, FamilyMember, HealthRecord, db
from ..utils.ai_helpers import (
    call_deepseek_api,
    call_groq_api,
    call_huggingface_api,
    extract_text_from_pdf,
    get_deepseek_api_key,
    get_groq_api_key,
    get_huggingface_api_key,
    get_openai_api_key,
)
from ..utils.shared import (
    AISecurityManager,
    ai_audit_required,
    ai_security_required,
    detect_suspicious_patterns,
    log_security_event,
    monitor_performance,
    sanitize_html,
    secure_ai_response_headers,
    validate_medical_context_access,
)

try:
    from langchain.chains import RetrievalQA
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
    from langchain_community.embeddings import OpenAIEmbeddings
    from langchain_community.llms import OpenAI
    from langchain_community.vectorstores import Chroma
except ImportError:
    # Handle missing langchain dependencies gracefully
    Chroma = None
    OpenAIEmbeddings = None
    RecursiveCharacterTextSplitter = None
    RetrievalQA = None
    PyPDFLoader = None
    TextLoader = None
    OpenAI = None
import re
import time

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")

# Default AI model configuration
DEFAULT_MODEL = "google/gemma-3n-E4B-it-litert-preview"

# Comprehensive Medical AI System Message (Enhanced for MedGemma)
MEDICA_AI_SYSTEM_MESSAGE = """You are Medical AI, a comprehensive medical consultant AI assistant designed to provide evidence-based health information and support. Your expertise spans:

**Core Medical Domains:**
- General Medicine & Internal Medicine
- Emergency Medicine & Urgent Care
- Preventive Medicine & Public Health
- Surgery (General, Orthopedic, Cardiac, Neurosurgery)
- Psychology & Psychiatry
- Pediatrics & Geriatrics
- Women's Health & Men's Health
- Cardiology, Neurology, Endocrinology
- Dermatology, Ophthalmology, ENT
- Oncology & Hematology
- Infectious Diseases & Immunology
- Rehabilitation Medicine & Physical Therapy

**Your Capabilities:**
✓ Evidence-based medical information and guidance
✓ Symptom analysis and differential diagnosis considerations
✓ Health record interpretation and medical data analysis
✓ Treatment options and therapeutic recommendations
✓ Medication information, interactions, and side effects
✓ Preventive care and wellness strategies
✓ Mental health support and psychological insights
✓ Health risk assessment and lifestyle modifications
✓ Medical terminology explanation and patient education
✓ Emergency situations recognition and triage guidance

**Your Approach:**
- **Patient-Centric**: Always prioritize patient safety, dignity, and autonomy
- **Evidence-Based**: Ground recommendations in current medical literature and guidelines
- **Holistic**: Consider physical, mental, social, and environmental health factors
- **Collaborative**: Emphasize the importance of healthcare team coordination
- **Educational**: Empower patients with knowledge while maintaining appropriate boundaries
- **Culturally Sensitive**: Respect diverse backgrounds and health beliefs
- **Ethical**: Maintain confidentiality and professional medical ethics

**Communication Style:**
- Use clear, compassionate, and professional language
- Adapt complexity based on the user's medical literacy
- Provide structured, organized responses with clear sections
- Use bullet points, numbered lists, and headers for clarity
- Include relevant medical terminology with explanations
- Offer actionable next steps and follow-up recommendations

**Critical Safety Protocols:**
⚠️ **EMERGENCY RECOGNITION**: Immediately identify and clearly flag medical emergencies requiring urgent care
⚠️ **SCOPE LIMITATIONS**: Never provide definitive diagnoses - offer differential considerations instead
⚠️ **PROFESSIONAL CARE**: Always emphasize the need for proper medical evaluation and professional healthcare
⚠️ **MEDICATION SAFETY**: Stress the importance of healthcare provider oversight for any medication changes
⚠️ **RED FLAGS**: Highlight concerning symptoms that warrant immediate medical attention

**Response Format Requirements:**
- **ALWAYS use proper Markdown formatting** for all responses
- Structure responses with clear headers (##), subheaders (###)
- Use bullet points (*) and numbered lists (1.) appropriately
- Apply emphasis with **bold** for important information and *italics* for emphasis
- Include relevant medical disclaimers and safety warnings
- Provide organized, scannable information that's easy to follow

Remember: You are a supportive medical consultant AI, providing comprehensive health information and guidance."""


def create_gpt_summary(record: Any, _summary_type: str = "standard") -> Optional[str]:
    """
    Create an explanation of a health record's documents using AI models

    Args:
        record: The HealthRecord object to analyze
        summary_type: 'standard' or 'detailed'

    Returns:
        A string containing the document explanation or None if there was an error
    """
    # Build the initial prompt from record data
    prompt = _build_record_prompt(record)

    # Process documents
    documents = record.documents.all()
    document_content, document_names, extraction_failed, partial_extraction = (
        _process_documents(documents)
    )

    # Finalize prompt with document information
    prompt = _finalize_prompt_with_documents(
        prompt, documents, document_content, partial_extraction, document_names
    )

    # Get appropriate system message
    system_message = _get_system_message(
        documents, document_content, partial_extraction, extraction_failed
    )

    # Try AI providers for summary generation
    current_app.logger.info(
        f"Attempting to generate medical summary for record {record.id}"
    )
    explanation = _try_ai_providers_for_summary(system_message, prompt, record)

    return explanation


def _add_standardized_fields_to_prompt(record, prompt):
    """Add standardized medical record fields to prompt"""
    if record.date:
        prompt += f"Date: {record.date.strftime('%Y-%m-%d')}\n"
    if record.chief_complaint:
        prompt += f"Chief Complaint: {record.chief_complaint}\n"
    if record.doctor:
        prompt += f"Doctor: {record.doctor}\n"
    if record.investigations:
        prompt += f"Investigations: {record.investigations}\n"
    if record.diagnosis:
        prompt += f"Diagnosis: {record.diagnosis}\n"
    if record.prescription:
        prompt += f"Prescription: {record.prescription}\n"
    if record.notes:
        prompt += f"Notes: {record.notes}\n"
    if record.review_followup:
        prompt += f"Review/Follow up: {record.review_followup}\n"
    return prompt


def _add_legacy_fields_to_prompt(record, prompt):
    """Add legacy fields for backward compatibility"""
    if record.record_type:
        prompt += f"Record Type: {record.record_type}\n"
    if record.title:
        prompt += f"Title: {record.title}\n"
    if record.description:
        prompt += f"Description: {record.description}\n"
    return prompt


def _has_standardized_fields(record):
    """Check if record has any standardized fields"""
    return any([record.chief_complaint, record.doctor, record.diagnosis])


def _build_record_prompt(record):
    """Build the initial prompt from record data"""
    prompt = (
        "You are analyzing a medical health record with the following information:\n\n"
    )

    # Use new standardized medical record fields
    prompt = _add_standardized_fields_to_prompt(record, prompt)

    # Fallback to legacy fields for backward compatibility
    if not _has_standardized_fields(record):
        prompt = _add_legacy_fields_to_prompt(record, prompt)

    return prompt


def _process_pdf_document(doc):
    """Process a PDF document and return content and status"""
    current_app.logger.info(f"Attempting to extract text from PDF: {doc.filename}")
    text = extract_text_from_pdf(doc.file_path)

    if text.strip():
        document_content = f"\n--- Document: {doc.filename} ---\n"
        document_content += text

        # Check if we got metadata only
        partial_extraction = (
            "PDF METADATA:" in text and "Full text extraction was not possible" in text
        )
        if partial_extraction:
            current_app.logger.warning(f"Only metadata extracted from {doc.filename}")

        return document_content, partial_extraction, False
    else:
        current_app.logger.warning(f"No text extracted from PDF {doc.filename}")
        return "", False, True


def _process_text_document(doc):
    """Process a text document and return content and status"""
    try:
        with open(doc.file_path) as text_file:
            text = text_file.read()
            if text.strip():
                document_content = f"\n--- Document: {doc.filename} ---\n"
                document_content += text
                return document_content, False, False
            else:
                return "", False, True
    except UnicodeDecodeError:
        current_app.logger.warning(f"Could not read {doc.filename} as text")
        return "", False, True


def _process_documents(documents):
    """Process all documents and return aggregated content and status"""
    document_content = ""
    document_names = []
    extraction_failed = False
    partial_extraction = False

    for doc in documents:
        document_names.append(doc.filename)
        try:
            if doc.file_type.lower() == "pdf":
                content, is_partial, is_failed = _process_pdf_document(doc)
                document_content += content
                if is_partial:
                    partial_extraction = True
                if is_failed:
                    extraction_failed = True
            else:
                content, is_partial, is_failed = _process_text_document(doc)
                document_content += content
                if is_failed:
                    extraction_failed = True
        except Exception as e:
            current_app.logger.error(f"Error processing document {doc.filename}: {e}")
            extraction_failed = True
            continue

    return document_content, document_names, extraction_failed, partial_extraction


def _finalize_prompt_with_documents(
    prompt, documents, document_content, partial_extraction, document_names
):
    """Finalize the prompt by adding document information"""
    if documents:
        if document_content:
            prompt += f"\nThe record includes {len(documents)} attached document(s) with the following content:\n"
            prompt += document_content

            if partial_extraction:
                prompt += "\n\nNote: Some documents could only be partially extracted. The summary may be limited by the available text content."
        else:
            prompt += f"\nThe record includes {len(documents)} attached document(s) with the following names: {', '.join(document_names)}"
            prompt += "\nHowever, the content could not be extracted for analysis."
    else:
        prompt += "\nThis record does not have any attached documents to analyze."

    return prompt


def _get_system_message(
    documents, document_content, partial_extraction, extraction_failed
):
    """Get appropriate system message based on document processing status"""
    if document_content and not partial_extraction:
        return "You are a medical assistant helping patients understand their health documents. Provide a clear explanation of medical terminology, test results, diagnoses, and treatment plans in plain language. Format your response with appropriate HTML paragraph and list tags for readability. Organize the explanation by sections like 'Summary', 'Key Findings', 'Recommendations', etc."
    elif document_content and partial_extraction:
        return "You are a medical assistant helping patients understand their health records. Some documents could only be partially extracted or only metadata was available. Explain this limitation to the user while still providing the best possible summary based on the available content. Format your response with appropriate HTML paragraph and list tags."
    elif documents and extraction_failed:
        return "You are a medical assistant helping patients understand their health records. The record has attached documents, but their content could not be extracted for analysis. Explain this limitation to the user and provide a summary based on the available record metadata. Suggest what the documents might contain based on the record type and title. Format your response with appropriate HTML paragraph tags."
    else:
        return "You are a medical assistant helping patients understand their health records. This record does not have attached documents, so provide a summary based on the available metadata. Format your response with appropriate HTML paragraph tags."


def _try_ai_providers_for_summary(system_message, prompt, record):
    """Try different AI providers for summary generation"""
    explanation = None

    # First try HuggingFace API with MedGemma
    try:
        explanation = call_huggingface_api(
            system_message, prompt, temperature=0.3, max_tokens=1500
        )
        if explanation:
            current_app.logger.info(
                f"HuggingFace/MedGemma API successful for record {record.id}"
            )
            return explanation
    except Exception as e:
        current_app.logger.warning(
            f"HuggingFace/MedGemma API failed for record {record.id}: {e}"
        )

    # If HuggingFace fails, try GROQ API
    current_app.logger.info(f"Falling back to GROQ API for record {record.id}")
    try:
        explanation = call_groq_api(
            system_message, prompt, temperature=0.3, max_tokens=1500
        )
        if explanation:
            current_app.logger.info(f"GROQ API successful for record {record.id}")
            return explanation
    except Exception as e:
        current_app.logger.warning(f"GROQ API failed for record {record.id}: {e}")

    # If GROQ fails, try DEEPSEEK API
    current_app.logger.info(f"Falling back to DEEPSEEK API for record {record.id}")
    try:
        explanation = call_deepseek_api(
            system_message, prompt, temperature=0.3, max_tokens=1500
        )
        if explanation:
            current_app.logger.info(f"DEEPSEEK API successful for record {record.id}")
            return explanation
    except Exception as e:
        current_app.logger.warning(f"DEEPSEEK API failed for record {record.id}: {e}")

    return None


def create_rag_for_documents(documents: List[Any]) -> Optional[Any]:
    """
    Create a RAG system for a list of documents

    Args:
        documents: List of Document objects

    Returns:
        A RetrievalQA chain or None if there was an error
    """
    # Continue using OpenAI embeddings for now as Llama embeddings would require additional setup
    api_key = get_openai_api_key()
    if not api_key:
        return None

    # Process documents and setup embedding as before
    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    docs = []

    for doc in documents:
        try:
            if doc.file_type == "pdf":
                loader = PyPDFLoader(doc.file_path)
                file_docs = loader.load()
                docs.extend(file_docs)
        except Exception as e:
            current_app.logger.error(f"Error loading document {doc.filename}: {e}")
            continue

    if not docs:
        return None

    # Split documents and create vector store as before
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = text_splitter.split_documents(docs)

    db_directory = os.path.join(current_app.config["UPLOAD_FOLDER"], "vector_db")
    os.makedirs(db_directory, exist_ok=True)

    vectordb = Chroma.from_documents(
        documents=split_docs, embedding=embeddings, persist_directory=db_directory
    )

    # Create retriever
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})

    # For now, maintain OpenAI as the RAG chain provider
    # TODO: Update this to use Llama when LangChain integration is available
    llm = OpenAI(openai_api_key=api_key, temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff", retriever=retriever
    )

    return qa_chain


# Routes
@ai_bp.route("/summarize/<int:record_id>", methods=["GET", "POST"])
@login_required
@limiter.limit("5 per minute")  # Rate limit AI summary generation
@monitor_performance
@ai_security_required("summarize")
@ai_audit_required(operation_type="summarize", data_classification="PHI")
@secure_ai_response_headers()
def summarize_record(record_id: int) -> Any:
    """Create an AI summary of a health record"""
    try:
        record = HealthRecord.query.get_or_404(record_id)

        # Check if user has permission to view this record
        has_permission = False
        if record.user_id == current_user.id:
            # This is the user's own record
            has_permission = True
        elif (
            record.family_member_id
            and record.family_member in current_user.family_members
        ):
            # This is a record for a family member of the user
            has_permission = True

        if not has_permission:
            log_security_event(
                "unauthorized_ai_summary_attempt",
                {
                    "user_id": current_user.id,
                    "record_id": record_id,
                    "record_owner_id": record.user_id,
                    "record_family_member_id": record.family_member_id,
                },
            )
            flash("You do not have permission to view this record", "danger")
            return redirect(url_for("records.dashboard"))

        # Check if a summary already exists
        existing_summary = AISummary.query.filter_by(
            health_record_id=record.id,
            summary_type="standard",  # Default to standard summary type
        ).first()

        if request.method == "POST":
            try:
                # Create a new summary or regenerate an existing one
                summary_text = create_gpt_summary(record)

                if not summary_text:
                    log_security_event(
                        "ai_summary_generation_failed",
                        {"user_id": current_user.id, "record_id": record_id},
                    )
                    flash("Error generating summary. Please try again later.", "danger")
                    return redirect(url_for("records.view_record", record_id=record.id))

                # Sanitize the generated summary
                summary_text = sanitize_html(summary_text)

                if existing_summary:
                    # Update existing summary
                    existing_summary.summary_text = summary_text
                    db.session.commit()
                else:
                    # Create new summary
                    summary = AISummary(
                        health_record_id=record.id,
                        summary_text=summary_text,
                        summary_type="standard",
                    )
                    db.session.add(summary)
                    db.session.commit()

                # Log successful summary generation
                log_security_event(
                    "ai_summary_generated",
                    {
                        "user_id": current_user.id,
                        "record_id": record_id,
                        "summary_length": len(summary_text),
                    },
                )

                flash("Summary generated successfully!", "success")
                return redirect(url_for("ai.view_summary", record_id=record.id))

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(
                    f"Error generating summary for record {record_id}: {e}"
                )
                flash(
                    "An error occurred while generating the summary. Please try again.",
                    "danger",
                )

        return render_template(
            "ai/summarize.html",
            title="Summarize Record",
            record=record,
            existing_summary=existing_summary,
        )

    except Exception as e:
        current_app.logger.error(f"Error in summarize_record: {e}")
        flash("An error occurred while accessing the record", "danger")
        return redirect(url_for("records.dashboard"))


@ai_bp.route("/summary/<int:record_id>")
@login_required
@monitor_performance
@ai_security_required("view_summary")
@ai_audit_required(operation_type="view_summary", data_classification="PHI")
@secure_ai_response_headers()
def view_summary(record_id: int) -> Any:
    """View an AI-generated summary"""
    try:
        record = HealthRecord.query.get_or_404(record_id)

        # Check if user has permission to view this record
        has_permission = False
        if record.user_id == current_user.id:
            # This is the user's own record
            has_permission = True
        elif (
            record.family_member_id
            and record.family_member in current_user.family_members
        ):
            # This is a record for a family member of the user
            has_permission = True

        if not has_permission:
            log_security_event(
                "unauthorized_ai_summary_view_attempt",
                {
                    "user_id": current_user.id,
                    "record_id": record_id,
                    "record_owner_id": record.user_id,
                    "record_family_member_id": record.family_member_id,
                },
            )
            flash("You do not have permission to view this record", "danger")
            return redirect(url_for("records.dashboard"))

        summary = AISummary.query.filter_by(health_record_id=record.id).first()

        if not summary:
            flash("No summary available. Please generate one first.", "info")
            return redirect(url_for("ai.summarize_record", record_id=record.id))

        # Log successful summary access
        log_security_event(
            "ai_summary_viewed",
            {
                "user_id": current_user.id,
                "record_id": record_id,
                "summary_id": summary.id,
            },
        )

        return render_template(
            "ai/view_summary.html", title="Summary", record=record, summary=summary
        )

    except Exception as e:
        current_app.logger.error(f"Error viewing summary for record {record_id}: {e}")
        flash("An error occurred while loading the summary", "danger")
        return redirect(url_for("records.dashboard"))


@ai_bp.route("/chatbot")
@login_required
@limiter.limit("20 per minute")  # Rate limit chatbot interface access
@monitor_performance
@ai_security_required("chatbot")
@ai_audit_required(operation_type="chatbot_access", data_classification="PHI")
def chatbot() -> Any:
    """Interactive health chatbot interface"""
    try:
        # Get family members for the patient selector
        family_members = current_user.family_members

        # Log chatbot access
        log_security_event(
            "chatbot_accessed",
            {"user_id": current_user.id, "family_members_count": len(family_members)},
        )

        return render_template(
            "ai/chatbot.html", title="Health Assistant", family_members=family_members
        )

    except Exception as e:
        current_app.logger.error(f"Error accessing chatbot: {e}")
        flash("An error occurred while loading the chatbot", "danger")
        return redirect(url_for("records.dashboard"))


@ai_bp.route("/chat", methods=["POST"])
@login_required
@limiter.limit("15 per minute")  # Rate limit chat API calls
@monitor_performance
@ai_security_required("chat")
@ai_audit_required(operation_type="chat", data_classification="PHI")
@secure_ai_response_headers()
def chat() -> Any:
    """API endpoint for the chatbot"""
    try:
        data = request.get_json()

        user_message, mode, patient, error_response, status_code = (
            _validate_chat_request(data)
        )
        if error_response:
            return error_response

        error_response = _validate_chat_input(user_message, mode, patient)
        if error_response:
            return error_response

        # Log chat interaction
        log_security_event(
            "chat_message_sent",
            {
                "user_id": current_user.id,
                "mode": mode,
                "patient": patient,
                "message_length": len(user_message),
            },
        )

        # Determine context and target records based on mode and patient
        (
            context,
            system_message,
            target_records,
            patient_name,
            family_member_name,
            error_response,
        ) = _determine_context_and_records(mode, patient)
        if error_response:
            return error_response

        # Enhance context with medical records information
        context = _enhance_context_with_records(context, target_records, patient_name)

        # Add context for records most relevant to the user's question
        context = _add_relevant_records_context(context, target_records, user_message)

        # Combine context and user message
        prompt = f"Context:\n{context}\n\nUser question: {user_message}\n\nImportant: Format your response using proper Markdown syntax for headings, lists, emphasis, etc. Do not use HTML tags."

        # Try AI providers for chat response generation
        assistant_message, used_model = _try_ai_providers_for_chat(
            system_message, prompt, mode
        )
        if not assistant_message:
            log_security_event(
                "chat_response_generation_failed",
                {"user_id": current_user.id, "mode": mode, "patient": patient},
            )
        # Sanitize the AI response
        assistant_message = sanitize_html(assistant_message)

        # Log successful chat response
        log_security_event(
            "chat_response_generated",
            {
                "user_id": current_user.id,
                "mode": mode,
                "patient": patient,
                "response_length": len(assistant_message),
            },
        )

        # Return AI response with model information
        return jsonify(
            {
                "response": assistant_message,
                "model": used_model
                or "Unknown",  # Use actual model name instead of hardcoded
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error in chat endpoint: {e}")
        log_security_event("chat_error", {"user_id": current_user.id, "error": str(e)})
        return jsonify({"error": "An error occurred processing your request"}), 500


@ai_bp.route("/symptom-checker")
@login_required
@limiter.limit("20 per minute")  # Rate limit symptom checker access
@monitor_performance
@ai_security_required("symptom_checker")
@ai_audit_required(operation_type="symptom_checker_access", data_classification="PHI")
def symptom_checker():
    """Symptom checker interface"""
    try:
        # Log symptom checker access
        log_security_event("symptom_checker_accessed", {"user_id": current_user.id})

        return render_template("ai/symptom_checker.html", title="Symptom Checker")

    except Exception as e:
        current_app.logger.error(f"Error accessing symptom checker: {e}")
        flash("An error occurred while loading the symptom checker", "danger")
        return redirect(url_for("records.dashboard"))


@ai_bp.route("/check-symptoms", methods=["POST"])
@login_required
@limiter.limit("10 per minute")  # Rate limit symptom checking API calls
@monitor_performance
@ai_security_required("check_symptoms")
@ai_audit_required(operation_type="symptom_analysis", data_classification="PHI")
@secure_ai_response_headers()
def check_symptoms():
    """API endpoint for symptom checking"""
    try:
        data = request.get_json()

        symptoms, error_response = _validate_symptoms_request(data)
        if error_response:
            return error_response

        # Validate and sanitize symptoms input
        symptoms, error_response = _validate_symptoms_input(symptoms)
        if error_response:
            return error_response

        # Log symptom check request
        log_security_event(
            "symptom_check_requested",
            {"user_id": current_user.id, "symptoms_length": len(symptoms)},
        )

        # Build user context for symptom analysis
        context = _build_user_context()

        # System message for symptom checker - Updated to use comprehensive Medica AI system message
        system_message = (
            MEDICA_AI_SYSTEM_MESSAGE
            + "\n\n**SYMPTOM ANALYSIS MODE**: You are operating in symptom analysis mode. Analyze the provided symptoms using your comprehensive medical knowledge, consider differential diagnoses, assess urgency levels, and provide evidence-based guidance. Include clear red flags for emergency situations, suggested timeframes for seeking care, and actionable next steps. Always emphasize when professional medical evaluation is needed."
        )

        # User prompt
        prompt = f"Context:\n{context}\n\nThe user has the following symptoms: {symptoms}\n\nProvide information about these symptoms, potential causes, and suggest whether the user should see a doctor. Include a clear disclaimer. Format your response using proper Markdown syntax for headings, lists, emphasis, etc. Do not use HTML tags."

        # Try AI providers in order: HuggingFace (MedGemma) -> GROQ -> DEEPSEEK
        current_app.logger.info("Attempting to analyze symptoms")
        assistant_message = _try_ai_providers_for_symptoms(system_message, prompt)

        if not assistant_message:
            log_security_event(
                "symptom_analysis_failed",
                {"user_id": current_user.id, "symptoms_length": len(symptoms)},
            )
            return jsonify({"error": "Failed to analyze symptoms"}), 500

        # Sanitize the AI response
        assistant_message = sanitize_html(assistant_message)

        # Log successful symptom analysis
        log_security_event(
            "symptom_analysis_completed",
            {
                "user_id": current_user.id,
                "symptoms_length": len(symptoms),
                "analysis_length": len(assistant_message),
            },
        )

        # Return only the AI response without the standard message
        return jsonify({"analysis": assistant_message})

    except Exception as e:
        current_app.logger.error(f"Error in symptom checker: {e}")
        log_security_event(
            "symptom_check_error", {"user_id": current_user.id, "error": str(e)}
        )
        return jsonify({"error": "An error occurred processing your request"}), 500


def _validate_symptoms_request(data):
    """Validate symptoms request data"""
    if not data or "symptoms" not in data:
        log_security_event(
            "invalid_symptom_check_request",
            {
                "user_id": current_user.id,
                "data_provided": bool(data),
                "symptoms_provided": bool(data and "symptoms" in data),
            },
        )
        return None, (jsonify({"error": "Invalid request"}), 400)
    return data["symptoms"], None


def _validate_symptoms_input(symptoms):
    """Validate and sanitize symptoms input"""
    if not symptoms or not isinstance(symptoms, str):
        log_security_event(
            "invalid_symptoms_input",
            {"user_id": current_user.id, "symptoms_type": type(symptoms).__name__},
        )
        return None, (
            jsonify({"error": "Symptoms description is required and must be text"}),
            400,
        )

    if detect_suspicious_patterns(symptoms):
        log_security_event(
            "suspicious_symptoms_input",
            {"user_id": current_user.id, "symptoms_length": len(symptoms)},
        )
        return None, (jsonify({"error": "Invalid input detected"}), 400)

    return sanitize_html(symptoms.strip()), None


def _build_user_context():
    """Build user context for symptom analysis"""
    user_records = HealthRecord.query.filter_by(user_id=current_user.id).all()

    context = f"The user is {current_user.first_name} {current_user.last_name}.\n"

    # Add age information if available
    if current_user.date_of_birth:
        from datetime import datetime, timezone

        today = datetime.now(timezone.utc)
        age = (
            today.year
            - current_user.date_of_birth.year
            - (
                (today.month, today.day)
                < (current_user.date_of_birth.month, current_user.date_of_birth.day)
            )
        )
        context += f"The user is {age} years old.\n"

    # Add past health records
    if user_records:
        context += "Here are some relevant past health records:\n"
        for record in user_records:
            if record.record_type in ["complaint", "doctor_visit", "lab_report"]:
                context += f"- {record.record_type.capitalize()}: {record.title} ({record.date.strftime('%Y-%m-%d')})\n"

    return context


def _try_ai_providers_for_symptoms(system_message, prompt):
    """Try different AI providers for symptom analysis"""
    assistant_message = None

    # First try HuggingFace API with MedGemma
    try:
        assistant_message = call_huggingface_api(
            system_message, prompt, temperature=0.5
        )
        if assistant_message:
            current_app.logger.info(
                "HuggingFace/MedGemma API successful for symptom analysis"
            )
            return assistant_message
    except Exception as e:
        current_app.logger.warning(
            f"HuggingFace/MedGemma API failed for symptom analysis: {e}"
        )

    # If HuggingFace fails, try GROQ API
    current_app.logger.info("Falling back to GROQ API for symptom analysis")
    try:
        assistant_message = call_groq_api(system_message, prompt, temperature=0.5)
        if assistant_message:
            current_app.logger.info("GROQ API successful for symptom analysis")
            return assistant_message
    except Exception as e:
        current_app.logger.warning(f"GROQ API failed for symptom analysis: {e}")

    # If GROQ fails, try DEEPSEEK API
    current_app.logger.info("Falling back to DEEPSEEK API for symptom analysis")
    try:
        assistant_message = call_deepseek_api(system_message, prompt, temperature=0.5)
        if assistant_message:
            current_app.logger.info("DEEPSEEK API successful for symptom analysis")
            return assistant_message
    except Exception as e:
        current_app.logger.warning(f"DEEPSEEK API failed for symptom analysis: {e}")

    return None


def _validate_chat_request(data):
    """Validate chat request data"""
    if not data or "message" not in data:
        log_security_event(
            "invalid_chat_request",
            {
                "user_id": current_user.id,
                "data_provided": bool(data),
                "message_provided": bool(data and "message" in data),
            },
        )
        return None, None, None, jsonify({"error": "Invalid request"}), 400

    user_message = data["message"]
    mode = data.get("mode", "public")  # 'private' or 'public' - default to public
    patient = data.get("patient", "self")  # 'self' or family member ID

    return user_message, mode, patient, None, None


def _validate_chat_input(user_message, mode, patient):
    """Validate chat input parameters"""
    # Input validation and sanitization
    if not user_message or not isinstance(user_message, str):
        log_security_event(
            "invalid_chat_message",
            {
                "user_id": current_user.id,
                "message_type": type(user_message).__name__,
            },
        )
        return None, jsonify({"error": "Message is required and must be text"}), 400

    # Check for suspicious patterns in user input
    if detect_suspicious_patterns(user_message):
        log_security_event(
            "suspicious_chat_input",
            {
                "user_id": current_user.id,
                "message_length": len(user_message),
                "mode": mode,
                "patient": patient,
            },
        )
        return None, jsonify({"error": "Invalid input detected"}), 400

    # Sanitize user message
    user_message = sanitize_html(user_message.strip())

    # Validate mode parameter
    if mode not in ["public", "private"]:
        log_security_event(
            "invalid_chat_mode", {"user_id": current_user.id, "mode": mode}
        )
        return None, jsonify({"error": "Invalid mode"}), 400

    return user_message, None, None


def _determine_context_and_records(mode, patient):
    """Determine context and target records based on mode and patient"""
    if mode == "public":
        # Public mode - no access to personal records
        context = "You are operating in public mode with no access to personal medical records. Provide general health information only."
        system_message = (
            MEDICA_AI_SYSTEM_MESSAGE
            + "\n\n**PUBLIC MODE RESTRICTIONS**: You are currently in public mode and do not have access to any personal medical records. Provide only general health information and educational content. Do not reference any personal medical history or specific patient data."
        )
        target_records = []  # Initialize empty list for public mode
        patient_name = None
        return context, system_message, target_records, patient_name, None, None

    # Private mode - access to records based on patient selection
    elif patient == "self":
        # User's own records
        user_records = HealthRecord.query.filter_by(user_id=current_user.id).all()
        context = f"The user is {current_user.first_name} {current_user.last_name}.\n"
        context += f"They have {len(user_records)} personal health records.\n"
        target_records = user_records
        patient_name = "your"
        system_message = (
            MEDICA_AI_SYSTEM_MESSAGE
            + "\n\n**PRIVATE MODE - PERSONAL RECORDS ACCESS**: You have full access to the user's complete medical history and health records. Use this information to provide personalized health insights, interpret medical data, reference specific records with dates and details when relevant, and offer contextual health guidance. Always maintain patient confidentiality and provide evidence-based recommendations while emphasizing the importance of professional medical care."
        )
        return context, system_message, target_records, patient_name, None, None

    else:
        # Family member's records
        try:
            family_member_id = int(patient)
            family_member = FamilyMember.query.get(family_member_id)

            # Verify the family member belongs to the current user
            if not family_member or family_member not in current_user.family_members:
                log_security_event(
                    "unauthorized_family_member_access",
                    {
                        "user_id": current_user.id,
                        "attempted_family_member_id": family_member_id,
                        "valid_family_member": bool(family_member),
                    },
                )
                return (
                    None,
                    None,
                    None,
                    None,
                    jsonify({"error": "Family member not found"}),
                    404,
                )

            # Use the enhanced medical context method
            context = family_member.get_complete_medical_context()
            family_records = family_member.records.all()
            target_records = family_records
            patient_name = f"{family_member.first_name}'s"
            family_member_name = family_member.first_name
            system_message = (
                MEDICA_AI_SYSTEM_MESSAGE
                + f"\n\n**PRIVATE MODE - FAMILY MEMBER RECORDS ACCESS**: You have full access to {family_member_name}'s complete medical history and health records. Use this information to provide personalized health insights about {family_member_name}, interpret their medical data, reference specific records with dates and details when relevant, and offer contextual health guidance for {family_member_name}'s care. Always maintain patient confidentiality and provide evidence-based recommendations while emphasizing the importance of professional medical care."
            )
            return context, system_message, target_records, patient_name, None, None
        except (ValueError, TypeError):
            log_security_event(
                "invalid_patient_id",
                {"user_id": current_user.id, "patient_value": str(patient)},
            )
            return None, None, None, None, jsonify({"error": "Invalid patient ID"}), 400


def _enhance_context_with_records(context, target_records, patient_name):
    """Enhance context with medical records information"""
    if not target_records:
        return context

    patient_display_name = (
        patient_name.replace("your", "the user").replace("'s", "")
        if patient_name
        else "the patient"
    )
    context += f"\n--- Complete Medical History for {patient_display_name} ---\n"

    # Group records by type for better organization
    records_by_type: Dict[str, List[Any]] = {}
    for record in target_records:
        record_type = record.record_type
        if record_type not in records_by_type:
            records_by_type[record_type] = []
        records_by_type[record_type].append(record)

    # Add summary of record types
    context += f"Total records: {len(target_records)}\n"
    for record_type, records in records_by_type.items():
        context += (
            f"- {record_type.replace('_', ' ').title()}: {len(records)} records\n"
        )

    context += "\n--- Recent Medical Records (Most Recent First) ---\n"
    # Sort records by date (most recent first) and include details
    sorted_records = sorted(target_records, key=lambda x: x.date, reverse=True)
    # Limit to most recent records to prevent context overflow
    max_records = 15  # Increased from 10 but still reasonable
    for idx, record in enumerate(sorted_records[:max_records]):
        context += f"\n{idx + 1}. {record.title}\n"
        context += f"   Type: {record.record_type.replace('_', ' ').title()}\n"
        context += f"   Date: {record.date.strftime('%Y-%m-%d')}\n"
        if record.description:
            # Optimize description length for context efficiency
            MAX_DESCRIPTION_LENGTH = 500
            description = (
                record.description[:MAX_DESCRIPTION_LENGTH] + "..."
                if len(record.description) > MAX_DESCRIPTION_LENGTH
                else record.description
            )
            context += f"   Description: {description}\n"

        # Include document information if available
        if record.documents.count() > 0:
            doc_count = record.documents.count()
            context += f"   Documents: {doc_count} attached file(s)\n"

    # Add note if there are more records
    if len(target_records) > max_records:
        context += f"\n... and {len(target_records) - max_records} additional older records not shown here but available for reference.\n"

    return context


def _add_relevant_records_context(context, target_records, user_message):
    """Add context for records most relevant to the user's question"""
    # Check if user is asking about specific record types
    record_type_keywords = {
        "prescription": ["prescription", "medicine", "drug", "medication"],
        "lab_report": ["lab", "test", "blood", "result"],
        "doctor_visit": ["visit", "appointment", "doctor", "consultation"],
        "complaint": ["symptom", "pain", "feeling", "complaint"],
    }

    # Simple record matching logic for highlighting relevant records
    matching_records = []
    for record_type, keywords in record_type_keywords.items():
        if any(keyword in user_message.lower() for keyword in keywords):
            # Find records of this type
            matches = [r for r in target_records if r.record_type == record_type]
            if matches:
                matching_records.extend(matches)

    if matching_records:
        context += "\n--- Records Most Relevant to Your Question ---\n"
        for idx, record in enumerate(
            matching_records[:3]
        ):  # Limit to 3 most relevant records
            context += f"\nHighlighted Record {idx + 1}: {record.title}\n"
            context += f"Date: {record.date.strftime('%Y-%m-%d')}\n"
            context += f"Type: {record.record_type.replace('_', ' ').title()}\n"
            if record.description:
                context += f"Details: {record.description}\n"

    return context


def _try_ai_providers_for_chat(system_message, prompt, mode):
    """Try different AI providers for chat response generation"""
    # Use higher token limits for private mode due to comprehensive system message and medical context
    max_tokens = 8000 if mode == "private" else 4000
    temperature = 0.5
    assistant_message = None
    used_model = None

    # Try AI providers in order: HuggingFace (MedGemma) -> GROQ -> DEEPSEEK
    current_app.logger.info(
        f"Attempting to generate chat response (mode: {mode}, max_tokens: {max_tokens})"
    )

    # First try HuggingFace API with MedGemma
    current_app.logger.info("Attempting HuggingFace API with MedGemma")
    try:
        assistant_message = call_huggingface_api(
            system_message, prompt, temperature=temperature, max_tokens=max_tokens
        )
        if assistant_message:
            used_model = current_app.config.get(
                "HUGGINGFACE_MODEL", "google/medgemma-4b-it"
            )
            current_app.logger.info("HuggingFace/MedGemma API successful")
            return assistant_message, used_model
    except Exception as e:
        current_app.logger.warning(f"HuggingFace/MedGemma API failed: {e}")

    # If HuggingFace fails, try GROQ API
    current_app.logger.info("Falling back to GROQ API")
    try:
        assistant_message = call_groq_api(
            system_message,
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if assistant_message:
            used_model = current_app.config.get(
                "GROQ_MODEL", "deepseek-r1-distill-llama-70b"
            )
            current_app.logger.info("GROQ API successful")
            return assistant_message, used_model
    except Exception as e:
        current_app.logger.warning(f"GROQ API failed: {e}")

    # If GROQ fails, try DEEPSEEK API
    current_app.logger.info("Falling back to DEEPSEEK API")
    try:
        assistant_message = call_deepseek_api(
            system_message,
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if assistant_message:
            used_model = current_app.config.get("DEEPSEEK_MODEL", "deepseek-chat")
            current_app.logger.info("DEEPSEEK API successful")
            return assistant_message, used_model
    except Exception as e:
        current_app.logger.warning(f"DEEPSEEK API failed: {e}")

    return None, None

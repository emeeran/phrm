from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import current_user, login_required
import os
import openai
import json
from ..models import db, HealthRecord, Document, AISummary, FamilyMember
from ..utils.ai_helpers import extract_text_from_pdf, call_gemini_api, call_openai_api, get_gemini_api_key, initialize_gemini, get_openai_api_key
from ..utils.security import (
    log_security_event, detect_suspicious_patterns, 
    sanitize_html
)
from ..utils.ai_security import (
    AISecurityManager, ai_security_required, 
    secure_ai_response_headers, validate_medical_context_access
)
from ..utils.ai_audit import ai_audit_required
from ..utils.performance import monitor_performance
from .. import limiter, cache
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader, PyPDFLoader
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
import re
import time

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

# Default AI model configuration
DEFAULT_MODEL = "gemini-2.5-flash-preview-05-20"
# Whether to use OpenAI as fallback if Gemini fails
USE_OPENAI_FALLBACK = True

# Comprehensive Medica AI System Message
MEDICA_AI_SYSTEM_MESSAGE = """You are Medica AI, a comprehensive medical consultant AI assistant designed to provide evidence-based health information and support. Your expertise spans:

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

def create_gpt_summary(record, summary_type='standard'):
    """
    Create an explanation of a health record's documents using AI models

    Args:
        record: The HealthRecord object to analyze
        summary_type: 'standard' or 'detailed'

    Returns:
        A string containing the document explanation or None if there was an error
    """
    # Build the context from record data
    prompt = f"You are analyzing a medical health record with the following information:\n\n"
    
    # Use new standardized medical record fields
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
    
    # Fallback to legacy fields for backward compatibility
    if not any([record.chief_complaint, record.doctor, record.diagnosis]):
        if record.record_type:
            prompt += f"Record Type: {record.record_type}\n"
        if record.title:
            prompt += f"Title: {record.title}\n"
        if record.description:
            prompt += f"Description: {record.description}\n"

    # Add document contents if available
    documents = record.documents.all()
    document_content = ""
    document_names = []
    extraction_failed = False
    partial_extraction = False

    if documents:
        for doc in documents:
            document_names.append(doc.filename)
            try:
                if (doc.file_type.lower() == 'pdf'):
                    current_app.logger.info(f"Attempting to extract text from PDF: {doc.filename}")
                    # Use enhanced extraction function
                    text = extract_text_from_pdf(doc.file_path)

                    if text.strip():
                        document_content += f"\n--- Document: {doc.filename} ---\n"
                        document_content += text

                        # Check if we got metadata only, which indicates partial extraction
                        if "PDF METADATA:" in text and "Full text extraction was not possible" in text:
                            partial_extraction = True
                            current_app.logger.warning(f"Only metadata extracted from {doc.filename}")
                    else:
                        current_app.logger.warning(f"No text extracted from PDF {doc.filename}")
                        extraction_failed = True
                else:
                    # For non-PDF files, read as text if possible
                    try:
                        with open(doc.file_path, 'r') as text_file:
                            text = text_file.read()
                            if text.strip():
                                document_content += f"\n--- Document: {doc.filename} ---\n"
                                document_content += text
                            else:
                                extraction_failed = True
                    except UnicodeDecodeError:
                        current_app.logger.warning(f"Could not read {doc.filename} as text")
                        extraction_failed = True
            except Exception as e:
                current_app.logger.error(f"Error processing document {doc.filename}: {e}")
                extraction_failed = True
                continue

    # Build the final prompt
    if documents:
        if document_content:
            prompt += f"\nThe record includes {len(documents)} attached document(s) with the following content:\n"
            prompt += document_content

            if partial_extraction:
                prompt += "\n\nNote: Some documents could only be partially extracted. The summary may be limited by the available text content."
        else:
            extraction_failed = True
            prompt += f"\nThe record includes {len(documents)} attached document(s) with the following names: {', '.join(document_names)}"
            prompt += "\nHowever, the content could not be extracted for analysis."
    else:
        prompt += "\nThis record does not have any attached documents to analyze."

    # Give specific instructions to the AI based on the available content
    if document_content and not partial_extraction:
        system_message = "You are a medical assistant helping patients understand their health documents. Provide a clear explanation of medical terminology, test results, diagnoses, and treatment plans in plain language. Format your response with appropriate HTML paragraph and list tags for readability. Organize the explanation by sections like 'Summary', 'Key Findings', 'Recommendations', etc."
    elif document_content and partial_extraction:
        system_message = "You are a medical assistant helping patients understand their health records. Some documents could only be partially extracted or only metadata was available. Explain this limitation to the user while still providing the best possible summary based on the available content. Format your response with appropriate HTML paragraph and list tags."
    elif documents and extraction_failed:
        system_message = "You are a medical assistant helping patients understand their health records. The record has attached documents, but their content could not be extracted for analysis. Explain this limitation to the user and provide a summary based on the available record metadata. Suggest what the documents might contain based on the record type and title. Format your response with appropriate HTML paragraph tags."
    else:
        system_message = "You are a medical assistant helping patients understand their health records. This record does not have attached documents, so provide a summary based on the available metadata. Format your response with appropriate HTML paragraph tags."

    # First try using Gemini API
    current_app.logger.info(f"Attempting to generate summary for record {record.id} using Gemini API")
    explanation = call_gemini_api(system_message, prompt)

    # If Gemini API fails and fallback is enabled, try OpenAI
    if explanation is None and USE_OPENAI_FALLBACK:
        current_app.logger.warning(f"Gemini API failed, falling back to OpenAI for record {record.id}")
        api_key = get_openai_api_key()

        if api_key:
            try:
                openai.api_key = api_key
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.3
                )
                explanation = response.choices[0].message.content.strip()
            except Exception as e:
                current_app.logger.error(f"Error creating OpenAI fallback explanation: {e}")
                return None

    return explanation

def create_rag_for_documents(documents):
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
            if (doc.file_type == 'pdf'):
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

    db_directory = os.path.join(current_app.config['UPLOAD_FOLDER'], "vector_db")
    os.makedirs(db_directory, exist_ok=True)

    vectordb = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        persist_directory=db_directory
    )

    # Create retriever
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})

    # For now, maintain OpenAI as the RAG chain provider
    # TODO: Update this to use Llama when LangChain integration is available
    llm = OpenAI(openai_api_key=api_key, temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever
    )

    return qa_chain

# Routes
@ai_bp.route('/summarize/<int:record_id>', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per minute")  # Rate limit AI summary generation
@monitor_performance
@ai_security_required('summarize')
@ai_audit_required(operation_type='summarize', data_classification='PHI')
@secure_ai_response_headers()
def summarize_record(record_id):
    """Create an AI summary of a health record"""
    try:
        record = HealthRecord.query.get_or_404(record_id)

        # Check if user has permission to view this record
        has_permission = False
        if record.user_id == current_user.id:
            # This is the user's own record
            has_permission = True
        elif record.family_member_id and record.family_member in current_user.family_members:
            # This is a record for a family member of the user
            has_permission = True
        
        if not has_permission:
            log_security_event('unauthorized_ai_summary_attempt', {
                'user_id': current_user.id,
                'record_id': record_id,
                'record_owner_id': record.user_id,
                'record_family_member_id': record.family_member_id
            })
            flash('You do not have permission to view this record', 'danger')
            return redirect(url_for('records.dashboard'))

        # Check if a summary already exists
        existing_summary = AISummary.query.filter_by(
            health_record_id=record.id,
            summary_type='standard'  # Default to standard summary type
        ).first()

        if request.method == 'POST':
            try:
                # Create a new summary or regenerate an existing one
                summary_text = create_gpt_summary(record)

                if not summary_text:
                    log_security_event('ai_summary_generation_failed', {
                        'user_id': current_user.id,
                        'record_id': record_id
                    })
                    flash('Error generating summary. Please try again later.', 'danger')
                    return redirect(url_for('records.view_record', record_id=record.id))

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
                        summary_type='standard'
                    )
                    db.session.add(summary)
                    db.session.commit()

                # Log successful summary generation
                log_security_event('ai_summary_generated', {
                    'user_id': current_user.id,
                    'record_id': record_id,
                    'summary_length': len(summary_text)
                })

                flash('Summary generated successfully!', 'success')
                return redirect(url_for('ai.view_summary', record_id=record.id))
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error generating summary for record {record_id}: {e}")
                flash('An error occurred while generating the summary. Please try again.', 'danger')

        return render_template('ai/summarize.html',
                              title='Summarize Record',
                              record=record,
                              existing_summary=existing_summary)
                              
    except Exception as e:
        current_app.logger.error(f"Error in summarize_record: {e}")
        flash('An error occurred while accessing the record', 'danger')
        return redirect(url_for('records.dashboard'))

@ai_bp.route('/summary/<int:record_id>')
@login_required
@monitor_performance
@cache.cached(timeout=300)  # Cache summaries for 5 minutes
@ai_security_required('view_summary')
@ai_audit_required(operation_type='view_summary', data_classification='PHI')
@secure_ai_response_headers()
def view_summary(record_id):
    """View an AI-generated summary"""
    try:
        record = HealthRecord.query.get_or_404(record_id)

        # Check if user has permission to view this record
        has_permission = False
        if record.user_id == current_user.id:
            # This is the user's own record
            has_permission = True
        elif record.family_member_id and record.family_member in current_user.family_members:
            # This is a record for a family member of the user
            has_permission = True
        
        if not has_permission:
            log_security_event('unauthorized_ai_summary_view_attempt', {
                'user_id': current_user.id,
                'record_id': record_id,
                'record_owner_id': record.user_id,
                'record_family_member_id': record.family_member_id
            })
            flash('You do not have permission to view this record', 'danger')
            return redirect(url_for('records.dashboard'))

        summary = AISummary.query.filter_by(health_record_id=record.id).first()

        if not summary:
            flash('No summary available. Please generate one first.', 'info')
            return redirect(url_for('ai.summarize_record', record_id=record.id))

        # Log successful summary access
        log_security_event('ai_summary_viewed', {
            'user_id': current_user.id,
            'record_id': record_id,
            'summary_id': summary.id
        })

        return render_template('ai/view_summary.html',
                              title='Summary',
                              record=record,
                              summary=summary)
                              
    except Exception as e:
        current_app.logger.error(f"Error viewing summary for record {record_id}: {e}")
        flash('An error occurred while loading the summary', 'danger')
        return redirect(url_for('records.dashboard'))

@ai_bp.route('/chatbot')
@login_required
@limiter.limit("20 per minute")  # Rate limit chatbot interface access
@monitor_performance
@ai_security_required('chatbot')
@ai_audit_required(operation_type='chatbot_access', data_classification='PHI')
def chatbot():
    """Interactive health chatbot interface"""
    try:
        # Get family members for the patient selector
        family_members = current_user.family_members
        
        # Log chatbot access
        log_security_event('chatbot_accessed', {
            'user_id': current_user.id,
            'family_members_count': len(family_members)
        })
        
        return render_template('ai/chatbot.html', title='Health Assistant', family_members=family_members)
        
    except Exception as e:
        current_app.logger.error(f"Error accessing chatbot: {e}")
        flash('An error occurred while loading the chatbot', 'danger')
        return redirect(url_for('records.dashboard'))

@ai_bp.route('/chat', methods=['POST'])
@login_required
@limiter.limit("15 per minute")  # Rate limit chat API calls
@monitor_performance
@ai_security_required('chat')
@ai_audit_required(operation_type='chat', data_classification='PHI')
@secure_ai_response_headers()
def chat():
    """API endpoint for the chatbot"""
    try:
        data = request.get_json()

        if not data or 'message' not in data:
            log_security_event('invalid_chat_request', {
                'user_id': current_user.id,
                'data_provided': bool(data),
                'message_provided': bool(data and 'message' in data)
            })
            return jsonify({'error': 'Invalid request'}), 400

        user_message = data['message']
        mode = data.get('mode', 'public')  # 'private' or 'public' - default to public
        patient = data.get('patient', 'self')  # 'self' or family member ID

        # Input validation and sanitization
        if not user_message or not isinstance(user_message, str):
            log_security_event('invalid_chat_message', {
                'user_id': current_user.id,
                'message_type': type(user_message).__name__
            })
            return jsonify({'error': 'Message is required and must be text'}), 400
        
        # Check for suspicious patterns in user input
        if detect_suspicious_patterns(user_message):
            log_security_event('suspicious_chat_input', {
                'user_id': current_user.id,
                'message_length': len(user_message),
                'mode': mode,
                'patient': patient
            })
            return jsonify({'error': 'Invalid input detected'}), 400

        # Sanitize user message
        user_message = sanitize_html(user_message.strip())
        
        # Validate mode parameter
        if mode not in ['public', 'private']:
            log_security_event('invalid_chat_mode', {
                'user_id': current_user.id,
                'mode': mode
            })
            return jsonify({'error': 'Invalid mode'}), 400

        # Log chat interaction
        log_security_event('chat_message_sent', {
            'user_id': current_user.id,
            'mode': mode,
            'patient': patient,
            'message_length': len(user_message)
        })

        # Handle different modes and patient contexts
        if mode == 'public':
            # Public mode - no access to personal records
            context = "You are operating in public mode with no access to personal medical records. Provide general health information only."
            system_message = MEDICA_AI_SYSTEM_MESSAGE + "\n\n**PUBLIC MODE RESTRICTIONS**: You are currently in public mode and do not have access to any personal medical records. Provide only general health information and educational content. Do not reference any personal medical history or specific patient data."
        else:
            # Private mode - access to records based on patient selection
            if patient == 'self':
                # User's own records
                user_records = HealthRecord.query.filter_by(user_id=current_user.id).all()
                context = f"The user is {current_user.first_name} {current_user.last_name}.\n"
                context += f"They have {len(user_records)} personal health records.\n"
                target_records = user_records
                patient_name = "your"
            else:
                # Family member's records
                try:
                    family_member_id = int(patient)
                    family_member = FamilyMember.query.get(family_member_id)
                    
                    # Verify the family member belongs to the current user
                    if not family_member or family_member not in current_user.family_members:
                        log_security_event('unauthorized_family_member_access', {
                            'user_id': current_user.id,
                            'attempted_family_member_id': family_member_id,
                            'valid_family_member': bool(family_member)
                        })
                        return jsonify({'error': 'Family member not found'}), 404
                    
                    # Use the enhanced medical context method
                    context = family_member.get_complete_medical_context()
                    family_records = family_member.records.all()
                    target_records = family_records
                    patient_name = f"{family_member.first_name}'s"
                except (ValueError, TypeError):
                    log_security_event('invalid_patient_id', {
                        'user_id': current_user.id,
                        'patient_value': str(patient)
                    })
                    return jsonify({'error': 'Invalid patient ID'}), 400

        # Check if user is asking about specific record types
        record_type_keywords = {
            'prescription': ['prescription', 'medicine', 'drug', 'medication'],
            'lab_report': ['lab', 'test', 'blood', 'result'],
            'doctor_visit': ['visit', 'appointment', 'doctor', 'consultation'],
            'complaint': ['symptom', 'pain', 'feeling', 'complaint']
        }

        # Always include all medical records for the selected patient in context
        if target_records:
            patient_display_name = patient_name.replace('your', 'the user').replace("'s", '')
            context += f"\n--- Complete Medical History for {patient_display_name} ---\n"
            
            # Group records by type for better organization
            records_by_type = {}
            for record in target_records:
                record_type = record.record_type
                if record_type not in records_by_type:
                    records_by_type[record_type] = []
                records_by_type[record_type].append(record)
            
            # Add summary of record types
            context += f"Total records: {len(target_records)}\n"
            for record_type, records in records_by_type.items():
                context += f"- {record_type.replace('_', ' ').title()}: {len(records)} records\n"
            
            context += "\n--- Recent Medical Records (Most Recent First) ---\n"
            # Sort records by date (most recent first) and include details
            sorted_records = sorted(target_records, key=lambda x: x.date, reverse=True)
            # Limit to most recent records to prevent context overflow
            max_records = 15  # Increased from 10 but still reasonable
            for idx, record in enumerate(sorted_records[:max_records]):
                context += f"\n{idx+1}. {record.title}\n"
                context += f"   Type: {record.record_type.replace('_', ' ').title()}\n"
                context += f"   Date: {record.date.strftime('%Y-%m-%d')}\n"
                if record.description:
                    # Optimize description length for context efficiency
                    description = record.description[:500] + "..." if len(record.description) > 500 else record.description
                    context += f"   Description: {description}\n"
                
                # Include document information if available
                if record.documents.count() > 0:
                    doc_count = record.documents.count()
                    context += f"   Documents: {doc_count} attached file(s)\n"
            
            # Add note if there are more records
            if len(target_records) > max_records:
                context += f"\n... and {len(target_records) - max_records} additional older records not shown here but available for reference.\n"

        # Simple record matching logic for highlighting relevant records
        matching_records = []
        for record_type, keywords in record_type_keywords.items():
            if any(keyword in user_message.lower() for keyword in keywords):
                # Find records of this type
                matches = [r for r in target_records if r.record_type == record_type]
                if matches:
                    matching_records.extend(matches)

        if matching_records:
            context += f"\n--- Records Most Relevant to Your Question ---\n"
            for idx, record in enumerate(matching_records[:3]):  # Limit to 3 most relevant records
                context += f"\nHighlighted Record {idx+1}: {record.title}\n"
                context += f"Date: {record.date.strftime('%Y-%m-%d')}\n"
                context += f"Type: {record.record_type.replace('_', ' ').title()}\n"
                if record.description:
                    context += f"Details: {record.description}\n"

        # System message for the chatbot - Updated to use comprehensive Medica AI system message
        if patient == 'self':
            system_message = MEDICA_AI_SYSTEM_MESSAGE + f"\n\n**PRIVATE MODE - PERSONAL RECORDS ACCESS**: You have full access to the user's complete medical history and health records. Use this information to provide personalized health insights, interpret medical data, reference specific records with dates and details when relevant, and offer contextual health guidance. Always maintain patient confidentiality and provide evidence-based recommendations while emphasizing the importance of professional medical care."
        else:
            family_member_name = family_member.first_name if 'family_member' in locals() else "the family member"
            system_message = MEDICA_AI_SYSTEM_MESSAGE + f"\n\n**PRIVATE MODE - FAMILY MEMBER RECORDS ACCESS**: You have full access to {family_member_name}'s complete medical history and health records. Use this information to provide personalized health insights about {family_member_name}, interpret their medical data, reference specific records with dates and details when relevant, and offer contextual health guidance for {family_member_name}'s care. Always maintain patient confidentiality and provide evidence-based recommendations while emphasizing the importance of professional medical care."

        # Combine context and user message
        prompt = f"Context:\n{context}\n\nUser question: {user_message}\n\nImportant: Format your response using proper Markdown syntax for headings, lists, emphasis, etc. Do not use HTML tags."

        # Log prompt and system message lengths for debugging
        current_app.logger.info(f"System message length: {len(system_message)} characters")
        current_app.logger.info(f"Context length: {len(context)} characters") 
        current_app.logger.info(f"Full prompt length: {len(prompt)} characters")

        # Use higher token limits for private mode due to comprehensive system message and medical context
        max_tokens = 8000 if mode == 'private' else 4000
        temperature = 0.5

        # First try using Gemini API
        current_app.logger.info(f"Attempting to generate chat response using Gemini API (mode: {mode}, max_tokens: {max_tokens})")
        assistant_message = call_gemini_api(system_message, prompt, temperature=temperature, max_tokens=max_tokens)

        # If Gemini API fails and fallback is enabled, try OpenAI
        if assistant_message is None and USE_OPENAI_FALLBACK:
            current_app.logger.warning(f"Gemini API failed for chat, falling back to OpenAI")
            try:
                api_key = get_openai_api_key()
                if not api_key:
                    return jsonify({'error': 'API key not configured'}), 500

                openai.api_key = api_key
                # Use higher token limits for private mode
                openai_max_tokens = 4000 if mode == 'private' else 2000
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=openai_max_tokens
                )
                assistant_message = response.choices[0].message.content.strip()
            except Exception as e:
                current_app.logger.error(f"Error in chatbot fallback: {e}")
                return jsonify({'error': 'An error occurred processing your request'}), 500

        if not assistant_message:
            log_security_event('chat_response_generation_failed', {
                'user_id': current_user.id,
                'mode': mode,
                'patient': patient
            })
            return jsonify({'error': 'Failed to generate response'}), 500

        # Sanitize the AI response
        assistant_message = sanitize_html(assistant_message)

        # Log successful chat response
        log_security_event('chat_response_generated', {
            'user_id': current_user.id,
            'mode': mode,
            'patient': patient,
            'response_length': len(assistant_message)
        })

        # Return only the AI response without the standard message
        return jsonify({
            'response': assistant_message
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in chat endpoint: {e}")
        log_security_event('chat_error', {
            'user_id': current_user.id,
            'error': str(e)
        })
        return jsonify({'error': 'An error occurred processing your request'}), 500

@ai_bp.route('/symptom-checker')
@login_required
@limiter.limit("20 per minute")  # Rate limit symptom checker access
@monitor_performance
@ai_security_required('symptom_checker')
@ai_audit_required(operation_type='symptom_checker_access', data_classification='PHI')
def symptom_checker():
    """Symptom checker interface"""
    try:
        # Log symptom checker access
        log_security_event('symptom_checker_accessed', {
            'user_id': current_user.id
        })
        
        return render_template('ai/symptom_checker.html', title='Symptom Checker')
        
    except Exception as e:
        current_app.logger.error(f"Error accessing symptom checker: {e}")
        flash('An error occurred while loading the symptom checker', 'danger')
        return redirect(url_for('records.dashboard'))

@ai_bp.route('/check-symptoms', methods=['POST'])
@login_required
@limiter.limit("10 per minute")  # Rate limit symptom checking API calls
@monitor_performance
@ai_security_required('check_symptoms')
@ai_audit_required(operation_type='symptom_analysis', data_classification='PHI')
@secure_ai_response_headers()
def check_symptoms():
    """API endpoint for symptom checking"""
    try:
        data = request.get_json()

        if not data or 'symptoms' not in data:
            log_security_event('invalid_symptom_check_request', {
                'user_id': current_user.id,
                'data_provided': bool(data),
                'symptoms_provided': bool(data and 'symptoms' in data)
            })
            return jsonify({'error': 'Invalid request'}), 400

        symptoms = data['symptoms']

        # Input validation and sanitization
        if not symptoms or not isinstance(symptoms, str):
            log_security_event('invalid_symptoms_input', {
                'user_id': current_user.id,
                'symptoms_type': type(symptoms).__name__
            })
            return jsonify({'error': 'Symptoms description is required and must be text'}), 400
        
        # Check for suspicious patterns in user input
        if detect_suspicious_patterns(symptoms):
            log_security_event('suspicious_symptoms_input', {
                'user_id': current_user.id,
                'symptoms_length': len(symptoms)
            })
            return jsonify({'error': 'Invalid input detected'}), 400

        # Sanitize symptoms input
        symptoms = sanitize_html(symptoms.strip())
        
        # Log symptom check request
        log_security_event('symptom_check_requested', {
            'user_id': current_user.id,
            'symptoms_length': len(symptoms)
        })

        # Get user records for context
        user_records = HealthRecord.query.filter_by(user_id=current_user.id).all()

        # Create context from records
        context = f"The user is {current_user.first_name} {current_user.last_name}.\n"

        # Add age information if available
        if current_user.date_of_birth:
            from datetime import datetime
            today = datetime.today()
            age = today.year - current_user.date_of_birth.year - ((today.month, today.day) < (current_user.date_of_birth.month, current_user.date_of_birth.day))
            context += f"The user is {age} years old.\n"

        # Add past health records
        if user_records:
            context += "Here are some relevant past health records:\n"
            for record in user_records:
                if record.record_type in ['complaint', 'doctor_visit', 'lab_report']:
                    context += f"- {record.record_type.capitalize()}: {record.title} ({record.date.strftime('%Y-%m-%d')})\n"

        # System message for symptom checker - Updated to use comprehensive Medica AI system message
        system_message = MEDICA_AI_SYSTEM_MESSAGE + "\n\n**SYMPTOM ANALYSIS MODE**: You are operating in symptom analysis mode. Analyze the provided symptoms using your comprehensive medical knowledge, consider differential diagnoses, assess urgency levels, and provide evidence-based guidance. Include clear red flags for emergency situations, suggested timeframes for seeking care, and actionable next steps. Always emphasize when professional medical evaluation is needed."

        # User prompt
        prompt = f"Context:\n{context}\n\nThe user has the following symptoms: {symptoms}\n\nProvide information about these symptoms, potential causes, and suggest whether the user should see a doctor. Include a clear disclaimer. Format your response using proper Markdown syntax for headings, lists, emphasis, etc. Do not use HTML tags."

        # First try using Gemini API
        current_app.logger.info(f"Attempting to analyze symptoms using Gemini API")
        assistant_message = call_gemini_api(system_message, prompt, temperature=0.5)

        # If Gemini API fails and fallback is enabled, try OpenAI
        if assistant_message is None and USE_OPENAI_FALLBACK:
            current_app.logger.warning(f"Gemini API failed for symptom checking, falling back to OpenAI")
            try:
                api_key = get_openai_api_key()
                if not api_key:
                    return jsonify({'error': 'API key not configured'}), 500

                openai.api_key = api_key
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5
                )
                assistant_message = response.choices[0].message.content.strip()
            except Exception as e:
                current_app.logger.error(f"Error in symptom checker fallback: {e}")
                return jsonify({'error': 'An error occurred processing your request'}), 500

        if not assistant_message:
            log_security_event('symptom_analysis_failed', {
                'user_id': current_user.id,
                'symptoms_length': len(symptoms)
            })
            return jsonify({'error': 'Failed to analyze symptoms'}), 500

        # Sanitize the AI response
        assistant_message = sanitize_html(assistant_message)

        # Log successful symptom analysis
        log_security_event('symptom_analysis_completed', {
            'user_id': current_user.id,
            'symptoms_length': len(symptoms),
            'analysis_length': len(assistant_message)
        })

        # Return only the AI response without the standard message
        return jsonify({
            'analysis': assistant_message
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in symptom checker: {e}")
        log_security_event('symptom_check_error', {
            'user_id': current_user.id,
            'error': str(e)
        })
        return jsonify({'error': 'An error occurred processing your request'}), 500
from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import current_user, login_required
import os
import openai
import json
import requests
from ..models import db, HealthRecord, Document, AISummary, FamilyMember
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader, PyPDFLoader
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
# Import pypdf directly
import pypdf
import io
import logging
import subprocess
import tempfile
# Import Google Generative AI
import google.generativeai as genai

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

# Helper functions
def get_openai_api_key():
    """Get OpenAI API key from Doppler via app config"""
    api_key = current_app.config.get('OPENAI_API_KEY')
    if not api_key:
        current_app.logger.error("OpenAI API key not configured in Doppler")
        return None
    return api_key

def get_gemini_api_key():
    """Get Gemini API key from app config"""
    api_key = current_app.config.get('GEMINI_API_KEY')
    if not api_key:
        current_app.logger.error("Gemini API key not configured")
        return None
    return api_key

def initialize_gemini():
    """Initialize the Gemini API"""
    api_key = get_gemini_api_key()
    if not api_key:
        return False
    
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to initialize Gemini API: {e}")
        return False

# Default AI model configuration
DEFAULT_MODEL = "gemini-1.5-pro"
# Whether to use OpenAI as fallback if Gemini fails
USE_OPENAI_FALLBACK = True

def extract_text_from_pdf(file_path):
    """
    Enhanced PDF text extraction with multiple fallback methods

    Args:
        file_path: Path to the PDF file

    Returns:
        Extracted text or empty string if extraction fails
    """
    # First attempt using pypdf's standard extraction
    try:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = pypdf.PdfReader(pdf_file)
            text = ""

            # Try page by page extraction
            for page_num in range(len(pdf_reader.pages)):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num + 1} ---\n"
                        text += page_text + "\n"
                except Exception as e:
                    current_app.logger.warning(f"Error extracting text from page {page_num}: {e}")
                    continue

            if text.strip():
                current_app.logger.info(f"Successfully extracted text using pypdf standard method")
                return text

            current_app.logger.warning("Standard pypdf extraction returned empty text")
    except Exception as e:
        current_app.logger.error(f"Error in primary PDF extraction method: {e}")

    # Fallback 1: Try with different encoding/parameters
    try:
        text = ""
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = pypdf.PdfReader(pdf_file)
            for page_num in range(len(pdf_reader.pages)):
                try:
                    page = pdf_reader.pages[page_num]
                    # Extract raw content which might contain more information
                    content = page.extract_text(extraction_mode="rawtext", encoding="Latin1")
                    if content:
                        text += content + "\n"
                except:
                    continue

        if text.strip():
            current_app.logger.info(f"Successfully extracted text using fallback method 1")
            return text

        current_app.logger.warning("Fallback method 1 returned empty text")
    except Exception as e:
        current_app.logger.error(f"Error in fallback method 1: {e}")

    # Fallback 2: Try deep extraction mode with different parameters
    try:
        text = ""
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = pypdf.PdfReader(pdf_file)
            for page_num in range(len(pdf_reader.pages)):
                try:
                    page = pdf_reader.pages[page_num]
                    # Try with extraction_mode="layout" which can work better for complex documents
                    content = page.extract_text(extraction_mode="layout")
                    if content:
                        text += f"\n--- Page {page_num + 1} ---\n"
                        text += content + "\n"
                except Exception as e:
                    current_app.logger.warning(f"Layout extraction failed for page {page_num}: {e}")
                    continue

        if text.strip():
            current_app.logger.info(f"Successfully extracted text using fallback method 2")
            return text

        current_app.logger.warning("Fallback method 2 returned empty text")
    except Exception as e:
        current_app.logger.error(f"Error in fallback method 2: {e}")

    # Fallback 3: Try using PyPDFLoader from LangChain which might handle some PDFs better
    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        text = ""
        for doc in docs:
            text += doc.page_content + "\n"

        if text.strip():
            current_app.logger.info(f"Successfully extracted text using LangChain PyPDFLoader")
            return text

        current_app.logger.warning("LangChain PyPDFLoader returned empty text")
    except Exception as e:
        current_app.logger.error(f"Error using LangChain PyPDFLoader: {e}")

    # Fallback 4: Try using pdftotext CLI tool if available (from poppler-utils package)
    try:
        if subprocess.run(['which', 'pdftotext'], capture_output=True).returncode == 0:
            with tempfile.NamedTemporaryFile(suffix='.txt') as temp_txt:
                # Run pdftotext with various options for better extraction
                subprocess.run(['pdftotext', '-layout', file_path, temp_txt.name], check=True)
                with open(temp_txt.name, 'r') as f:
                    text = f.read()

                if text.strip():
                    current_app.logger.info(f"Successfully extracted text using pdftotext CLI tool")
                    return text

                # Try again with different options
                subprocess.run(['pdftotext', '-raw', file_path, temp_txt.name], check=True)
                with open(temp_txt.name, 'r') as f:
                    text = f.read()

                if text.strip():
                    current_app.logger.info(f"Successfully extracted text using pdftotext CLI tool with -raw option")
                    return text

                current_app.logger.warning("pdftotext CLI extraction returned empty text")
        else:
            current_app.logger.warning("pdftotext CLI tool not available")
    except Exception as e:
        current_app.logger.error(f"Error using pdftotext CLI tool: {e}")

    # Fallback 5: Try reading the PDF metadata if text extraction failed
    try:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = pypdf.PdfReader(pdf_file)
            metadata = pdf_reader.metadata
            if metadata:
                meta_text = "PDF METADATA:\n"
                for key, value in metadata.items():
                    if value:
                        meta_text += f"{key}: {value}\n"

                # Add file info
                meta_text += f"\nFile Information:\n"
                meta_text += f"Filename: {os.path.basename(file_path)}\n"
                meta_text += f"Pages: {len(pdf_reader.pages)}\n"
                meta_text += f"Size: {os.path.getsize(file_path)} bytes\n"

                current_app.logger.info(f"Extracted metadata from PDF")
                return meta_text + "\n(Note: This PDF appears to contain only metadata or images. Full text extraction was not possible.)"
    except Exception as e:
        current_app.logger.error(f"Error extracting metadata: {e}")

    # All extraction methods failed
    current_app.logger.error(f"All PDF extraction methods failed for {file_path}")
    return f"ERROR: Unable to extract text from this PDF file ({os.path.basename(file_path)}). The document may be encrypted, password-protected, or contain only scanned images without OCR text. Please contact support for assistance with this document."

def call_gemini_api(system_message, prompt, temperature=0.3, max_tokens=1500):
    """
    Call the Gemini API with the given prompt

    Args:
        system_message: The system message for the model
        prompt: The user prompt
        temperature: Temperature parameter for randomness
        max_tokens: Maximum tokens in the response

    Returns:
        The model's response text or None if there was an error
    """
    api_key = get_gemini_api_key()
    if not api_key:
        current_app.logger.error("Gemini API key not configured")
        return None

    try:
        # Initialize Gemini API
        if not initialize_gemini():
            return None
        
        # Get the model
        model_name = current_app.config.get('GEMINI_MODEL', DEFAULT_MODEL)
        
        try:
            # Create a generative model instance
            model = genai.GenerativeModel(model_name=model_name)
            
            # Combine system message and prompt
            full_prompt = f"{system_message}\n\n{prompt}"
            
            # Generate content
            current_app.logger.info(f"Sending request to Gemini API using model: {model_name}")
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=0.95,
                )
            )
            
            if response.text:
                return response.text.strip()
            else:
                current_app.logger.error("Gemini API returned empty response")
                return None
                
        except genai.types.BlockedPromptException as e:
            current_app.logger.error(f"Gemini API blocked the prompt: {e}")
            return "I'm unable to respond to this request as it may violate content safety policies."
        except ValueError as e:
            current_app.logger.error(f"Gemini API value error: {e}")
            return None

    except Exception as e:
        current_app.logger.error(f"Error calling Gemini API: {e}")
        return None

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
    prompt = f"You are analyzing a health record with the following information:\n\n"
    prompt += f"Record Type: {record.record_type}\n"
    prompt += f"Title: {record.title}\n"
    prompt += f"Date: {record.date.strftime('%Y-%m-%d')}\n"
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
def summarize_record(record_id):
    """Create an AI summary of a health record"""
    record = HealthRecord.query.get_or_404(record_id)

    # Check if user has permission to view this record
    if record.user_id == current_user.id:
        # This is the user's own record
        pass
    elif record.family_member_id and record.family_member in current_user.family_members:
        # This is a record for a family member of the user
        pass
    else:
        flash('You do not have permission to view this record', 'danger')
        return redirect(url_for('records.dashboard'))

    # Check if a summary already exists
    existing_summary = AISummary.query.filter_by(
        health_record_id=record.id,
        summary_type='standard'  # Default to standard summary type
    ).first()

    if request.method == 'POST':
        # Create a new summary or regenerate an existing one
        summary_text = create_gpt_summary(record)

        if not summary_text:
            flash('Error generating summary. Please try again later.', 'danger')
            return redirect(url_for('records.view_record', record_id=record.id))

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

        flash('Summary generated successfully!', 'success')
        return redirect(url_for('ai.view_summary', record_id=record.id))

    return render_template('ai/summarize.html',
                          title='Summarize Record',
                          record=record,
                          existing_summary=existing_summary)

@ai_bp.route('/summary/<int:record_id>')
@login_required
def view_summary(record_id):
    """View an AI-generated summary"""
    record = HealthRecord.query.get_or_404(record_id)

    # Check if user has permission to view this record
    if record.user_id == current_user.id:
        # This is the user's own record
        pass
    elif record.family_member_id and record.family_member in current_user.family_members:
        # This is a record for a family member of the user
        pass
    else:
        flash('You do not have permission to view this record', 'danger')
        return redirect(url_for('records.dashboard'))

    summary = AISummary.query.filter_by(health_record_id=record.id).first()

    if not summary:
        flash('No summary available. Please generate one first.', 'info')
        return redirect(url_for('ai.summarize_record', record_id=record.id))

    return render_template('ai/view_summary.html',
                          title='Summary',
                          record=record,
                          summary=summary)

@ai_bp.route('/chatbot')
@login_required
def chatbot():
    """Interactive health chatbot interface"""
    # Get family members for the patient selector
    family_members = current_user.family_members
    return render_template('ai/chatbot.html', title='Health Assistant', family_members=family_members)

@ai_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """API endpoint for the chatbot"""
    data = request.get_json()

    if not data or 'message' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    user_message = data['message']
    mode = data.get('mode', 'private')  # 'private' or 'public'
    patient = data.get('patient', 'self')  # 'self' or family member ID

    # Handle different modes and patient contexts
    if mode == 'public':
        # Public mode - no access to personal records
        context = "You are a general health assistant. Provide general health information only. Do not reference any personal medical records."
        system_message = "You are a helpful general health assistant. Provide general health information and advice, but always remind users to consult healthcare professionals for medical advice. Do not reference any personal medical records. FORMAT YOUR RESPONSE IN MARKDOWN: Use markdown formatting for all responses, including headers (##), lists (*), emphasis (**bold**, *italic*), and other markdown formatting as needed for clear and organized information."
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
                    return jsonify({'error': 'Family member not found'}), 404
                
                family_records = family_member.records.all()
                context = f"The user is asking about {family_member.first_name} {family_member.last_name}.\n"
                context += f"{family_member.first_name} has {len(family_records)} health records.\n"
                target_records = family_records
                patient_name = f"{family_member.first_name}'s"
            except (ValueError, TypeError):
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
            for idx, record in enumerate(sorted_records[:10]):  # Limit to 10 most recent records
                context += f"\n{idx+1}. {record.title}\n"
                context += f"   Type: {record.record_type.replace('_', ' ').title()}\n"
                context += f"   Date: {record.date.strftime('%Y-%m-%d')}\n"
                if record.description:
                    # Include more of the description for better context
                    description = record.description[:300] + "..." if len(record.description) > 300 else record.description
                    context += f"   Description: {description}\n"
                
                # Include document information if available
                if record.documents.count() > 0:
                    doc_count = record.documents.count()
                    context += f"   Documents: {doc_count} attached file(s)\n"

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

        # System message for the chatbot - Updated to request Markdown formatting
        if patient == 'self':
            system_message = f"You are a helpful health assistant with access to the user's complete medical history. You can provide health information and help interpret their health records. Reference specific records, dates, and medical details when relevant to answer their questions. Always remind users to consult healthcare professionals for medical advice. FORMAT YOUR RESPONSE IN MARKDOWN: Use markdown formatting for all responses, including headers (##), lists (*), emphasis (**bold**, *italic*), and other markdown formatting as needed for clear and organized information."
        else:
            family_member_name = family_member.first_name if 'family_member' in locals() else "the family member"
            system_message = f"You are a helpful health assistant with access to {family_member_name}'s complete medical history. You can provide health information and help interpret {family_member_name}'s health records. Reference specific records, dates, and medical details when relevant to answer questions about {family_member_name}'s health. Always remind users to consult healthcare professionals for medical advice. FORMAT YOUR RESPONSE IN MARKDOWN: Use markdown formatting for all responses, including headers (##), lists (*), emphasis (**bold**, *italic*), and other markdown formatting as needed for clear and organized information."

    # Combine context and user message
    prompt = f"Context:\n{context}\n\nUser question: {user_message}\n\nImportant: Format your response using proper Markdown syntax for headings, lists, emphasis, etc. Do not use HTML tags."

    # First try using Gemini API
    current_app.logger.info(f"Attempting to generate chat response using Gemini API")
    assistant_message = call_gemini_api(system_message, prompt, temperature=0.5)

    # If Gemini API fails and fallback is enabled, try OpenAI
    if assistant_message is None and USE_OPENAI_FALLBACK:
        current_app.logger.warning(f"Gemini API failed for chat, falling back to OpenAI")
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
            current_app.logger.error(f"Error in chatbot fallback: {e}")
            return jsonify({'error': 'An error occurred processing your request'}), 500

    if not assistant_message:
        return jsonify({'error': 'Failed to generate response'}), 500

    # Return only the AI response without the standard message
    return jsonify({
        'response': assistant_message
    })

@ai_bp.route('/symptom-checker')
@login_required
def symptom_checker():
    """Symptom checker interface"""
    return render_template('ai/symptom_checker.html', title='Symptom Checker')

@ai_bp.route('/check-symptoms', methods=['POST'])
@login_required
def check_symptoms():
    """API endpoint for symptom checking"""
    data = request.get_json()

    if not data or 'symptoms' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    symptoms = data['symptoms']

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

    # System message for symptom checker - Updated to request Markdown formatting
    system_message = "You are a helpful health assistant that can provide information about symptoms. You should never diagnose, but you can suggest when users should seek medical attention. Always include a disclaimer that this is not medical advice and recommend consulting a healthcare professional. FORMAT YOUR RESPONSE IN MARKDOWN: Use markdown formatting for all responses, including headers (##), lists (*), emphasis (**bold**, *italic*), and other markdown formatting as needed for clear and organized information."

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
        return jsonify({'error': 'Failed to analyze symptoms'}), 500

    # Return only the AI response without the standard message
    return jsonify({
        'analysis': assistant_message
    })
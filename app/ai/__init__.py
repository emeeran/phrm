from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import current_user, login_required
import os
import openai
import json
import requests
from ..models import db, HealthRecord, Document, AISummary
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

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

# Helper functions
def get_openai_api_key():
    """Get OpenAI API key from app config"""
    api_key = current_app.config.get('OPENAI_API_KEY')
    if not api_key:
        current_app.logger.error("OpenAI API key not configured")
        return None
    return api_key

def get_llama_api_key():
    """Get Meta Llama API key from app config"""
    return current_app.config.get('META_LLAMA_API_KEY') or os.environ.get('META_LLAMA_API_KEY')

# Default AI model configuration
DEFAULT_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
# Whether to use OpenAI as fallback if Llama fails
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

def call_llama_api(system_message, prompt, temperature=0.3, max_tokens=1500):
    """
    Call the Meta Llama API with the given prompt

    Args:
        system_message: The system message for the model
        prompt: The user prompt
        temperature: Temperature parameter for randomness
        max_tokens: Maximum tokens in the response

    Returns:
        The model's response text or None if there was an error
    """
    api_key = get_llama_api_key()
    if not api_key:
        current_app.logger.error("Meta Llama API key not configured")
        return None

    try:
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        current_app.logger.info(f"Sending request to Llama API using model: {DEFAULT_MODEL}")
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content.strip()
        else:
            current_app.logger.error(f"Llama API error: Status {response.status_code}, Response: {response.text}")
            return None

    except Exception as e:
        current_app.logger.error(f"Error calling Llama API: {e}")
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
                if doc.file_type.lower() == 'pdf':
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
                        # Try binary mode for non-text files
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

    # First try using Llama API
    current_app.logger.info(f"Attempting to generate summary for record {record.id} using Llama API")
    explanation = call_llama_api(system_message, prompt)

    # If Llama API fails and fallback is enabled, try OpenAI
    if explanation is None and USE_OPENAI_FALLBACK:
        current_app.logger.warning(f"Llama API failed, falling back to OpenAI for record {record.id}")
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
    return render_template('ai/chatbot.html', title='Health Assistant')

@ai_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """API endpoint for the chatbot"""
    data = request.get_json()

    if not data or 'message' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    user_message = data['message']

    # Get user records for context
    user_records = HealthRecord.query.filter_by(user_id=current_user.id).all()

    # Get family records
    family_records = []
    for family_member in current_user.family_members:
        family_records.extend(family_member.records.all())

    # Create context from records (simplified, a real implementation would be more sophisticated)
    context = f"The user is {current_user.first_name} {current_user.last_name}.\n"
    context += f"They have {len(user_records)} personal health records and {len(family_records)} family health records.\n"

    # Check if user is asking about specific record types
    record_type_keywords = {
        'prescription': ['prescription', 'medicine', 'drug', 'medication'],
        'lab_report': ['lab', 'test', 'blood', 'result'],
        'doctor_visit': ['visit', 'appointment', 'doctor', 'consultation'],
        'complaint': ['symptom', 'pain', 'feeling', 'complaint']
    }

    # Simple record matching logic (a real implementation would use RAG)
    matching_records = []
    for record_type, keywords in record_type_keywords.items():
        if any(keyword in user_message.lower() for keyword in keywords):
            # Find records of this type
            matches = [r for r in user_records if r.record_type == record_type]
            if matches:
                matching_records.extend(matches)

    if matching_records:
        context += "Here are some relevant records that might help answer your query:\n"
        for idx, record in enumerate(matching_records[:3]):  # Limit to 3 records
            context += f"Record {idx+1}: {record.title} ({record.date.strftime('%Y-%m-%d')})\n"
            if record.description:
                context += f"Description: {record.description[:100]}...\n"

    # System message for the chatbot
    system_message = "You are a helpful health assistant. You can provide general health information and help users interpret their health records. Always remind users to consult healthcare professionals for medical advice."

    # Combine context and user message
    prompt = f"Context:\n{context}\n\nUser question: {user_message}"

    # First try using Llama API
    current_app.logger.info(f"Attempting to generate chat response using Llama API")
    assistant_message = call_llama_api(system_message, prompt, temperature=0.5)

    # If Llama API fails and fallback is enabled, try OpenAI
    if assistant_message is None and USE_OPENAI_FALLBACK:
        current_app.logger.warning(f"Llama API failed for chat, falling back to OpenAI")
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

    # System message for symptom checker
    system_message = "You are a helpful health assistant that can provide information about symptoms. You should never diagnose, but you can suggest when users should seek medical attention. Always include a disclaimer that this is not medical advice and recommend consulting a healthcare professional."

    # User prompt
    prompt = f"Context:\n{context}\n\nThe user has the following symptoms: {symptoms}\n\nProvide information about these symptoms, potential causes, and suggest whether the user should see a doctor. Include a clear disclaimer."

    # First try using Llama API
    current_app.logger.info(f"Attempting to analyze symptoms using Llama API")
    assistant_message = call_llama_api(system_message, prompt, temperature=0.5)

    # If Llama API fails and fallback is enabled, try OpenAI
    if assistant_message is None and USE_OPENAI_FALLBACK:
        current_app.logger.warning(f"Llama API failed for symptom checking, falling back to OpenAI")
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

    return jsonify({
        'analysis': assistant_message
    })
import logging
import re

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user, login_required

from ...models import HealthRecord
from ...utils.ai_helpers import (
    call_deepseek_api,
    call_groq_api,
    call_huggingface_api,
    call_medgemma_api,
)

logger = logging.getLogger(__name__)

# Constants
CHAT_CONTEXT_PREVIEW_LENGTH = 200

# Citation confidence thresholds
MIN_CITATION_CONFIDENCE = 0.3  # Minimum confidence for including citations
HIGH_CONFIDENCE_THRESHOLD = 0.8  # Threshold for displaying confidence percentage

ai_chat_bp = Blueprint("ai_chat", __name__)


def _process_chat_response(response: str, citations: list) -> str:
    """Process AI chat response by folding thinking and formatting citations"""
    if not response:
        return response

    # Remove thinking tags and their content
    response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)
    response = re.sub(r"<thinking>.*?</thinking>", "", response, flags=re.DOTALL)
    response = re.sub(r"\*\*Thinking:.*?\*\*", "", response, flags=re.DOTALL)

    # Remove reasoning patterns that start on new lines - more precise matching
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

    # Filter out low-quality citations and only add if we have meaningful ones
    meaningful_citations = _filter_meaningful_citations(citations)

    if meaningful_citations:
        response += "\n\n---\n\n**Sources:**\n"
        for i, citation in enumerate(meaningful_citations, 1):
            citation_text = _format_citation(citation, i)
            response += f"{citation_text}\n"

    return response


def _filter_meaningful_citations(citations: list) -> list:
    """Filter out low-quality or placeholder citations"""
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


def _format_citation(citation: dict, index: int) -> str:
    """Format a single citation with enhanced medical reference information"""
    citation_type = citation.get("type", "Reference")

    if citation_type == "Medical Reference":
        # Enhanced formatting for local medical references
        title = citation.get("title", "Medical Reference")
        confidence = citation.get("confidence", 0)

        # Format: "1. Current Medical Diagnosis & Treatment p-543 (95% match)"
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
        url = citation.get("url", "")
        source = citation.get("source", "Internet")

        citation_text = f"{index}. **{title}**"
        if url and url.startswith("http"):
            citation_text += f" | {source}"
        else:
            citation_text += f" | {source}"

    else:
        # Standard medical record citations
        title = citation.get("title", "Medical Record")
        date = citation.get("date")
        record_type = citation.get("type", "Medical Record")
        owner = citation.get("owner", "")

        citation_text = f"{index}. **{title}**"
        if date:
            citation_text += f" ({date})"
        citation_text += f" - {record_type}"
        if owner:
            citation_text += f" | {owner}"

    return citation_text


def get_user_context(mode, patient_id=None):
    """Get user health context based on mode and patient selection"""
    if mode == "public":
        return "", []

    try:
        if patient_id == "self" or not patient_id:
            return _get_user_records_context()
        else:
            return _get_family_member_records_context(patient_id)
    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        return "", []


def _get_user_records_context():
    """Get current user's health records context"""
    from ..summarization import search_document_content

    records = (
        HealthRecord.query.filter_by(user_id=current_user.id)
        .order_by(HealthRecord.date.desc())
        .limit(10)
        .all()
    )

    context = "User's recent health records:\n"
    citations = []

    if records:
        for record in records[:5]:  # Limit to avoid token overflow
            context += _format_record_context(record)
            citations.append(
                {
                    "id": record.id,
                    "date": record.date.strftime("%Y-%m-%d"),
                    "title": record.title
                    or record.chief_complaint
                    or f"Health Record #{record.id}",
                    "type": record.record_type or "Medical Record",
                    "owner": "You",
                }
            )

    # Add document content search - this will search through all user's document content
    # and find relevant excerpts based on recent health patterns
    try:
        # Use recent health complaints/symptoms for document search
        search_terms = []
        for record in records[:3]:  # Use top 3 recent records for search terms
            if record.chief_complaint:
                search_terms.extend(record.chief_complaint.lower().split())
            if record.diagnosis:
                search_terms.extend(record.diagnosis.lower().split())

        if search_terms:
            # Create search query from most recent health terms
            search_query = " ".join(
                list(set(search_terms))[:10]
            )  # Unique terms, max 10
            document_context = search_document_content(
                current_user.id, search_query, max_docs=3
            )
            if document_context:
                context += f"\n{document_context}"
    except Exception as e:
        logger.warning(f"Could not include document context: {e}")

    return context, citations


def _get_family_member_records_context(patient_id):
    """Get family member's health records context"""
    # Get family member through the many-to-many relationship
    family_member = None
    for fm in current_user.family_members:
        if str(fm.id) == str(patient_id):
            family_member = fm
            break

    if not family_member:
        return "", []

    records = (
        HealthRecord.query.filter_by(family_member_id=family_member.id)
        .order_by(HealthRecord.date.desc())
        .limit(10)
        .all()
    )

    if not records:
        return "", []

    context = f"{family_member.first_name}'s recent health records:\n"
    citations = []
    for record in records[:5]:
        context += _format_record_context(record)
        citations.append(
            {
                "id": record.id,
                "date": record.date.strftime("%Y-%m-%d"),
                "title": record.title
                or record.chief_complaint
                or f"Health Record #{record.id}",
                "type": record.record_type or "Medical Record",
                "owner": f"{family_member.first_name} {family_member.last_name}",
            }
        )
    return context, citations


def _format_record_context(record):
    """Format a single health record for context including document content"""
    context = f"- {record.date}: {record.chief_complaint}"
    if record.diagnosis:
        context += f" | Diagnosis: {record.diagnosis}"
    if record.prescription:
        context += f" | Prescription: {record.prescription}"

    # Include document content if available
    if record.documents:
        docs_with_text = [doc for doc in record.documents if doc.extracted_text]
        if docs_with_text:
            context += " | Documents: "
            for i, doc in enumerate(docs_with_text):
                if i > 0:
                    context += "; "
                # Include first chars for chat context (more concise than user profile)
                text_preview = (
                    doc.extracted_text[:CHAT_CONTEXT_PREVIEW_LENGTH]
                    .replace("\n", " ")
                    .strip()
                )
                if len(doc.extracted_text) > CHAT_CONTEXT_PREVIEW_LENGTH:
                    text_preview += "..."
                context += f"{doc.filename}({text_preview})"

    context += "\n"
    return context


def call_ai_with_fallback(
    system_message, user_message, temperature=0.3, max_tokens=2000
):
    """Call AI providers with fallback logic - prioritizing MedGemma for medical queries"""
    
    # Reset API availability flags occasionally to allow retrying
    import random
    if random.random() < 0.1:  # 10% chance to reset flags
        from ...utils.ai_helpers import reset_api_availability_flags
        reset_api_availability_flags()

    # Try MedGemma first (Google's specialized medical AI)
    try:
        logger.info("Attempting MedGemma API call...")
        response = call_medgemma_api(
            system_message, user_message, temperature, max_tokens
        )
        if response:
            logger.info("MedGemma API call successful")
            return response, "MedGemma"
        else:
            logger.info("MedGemma API returned None - trying next provider")
    except Exception as e:
        logger.warning(f"MedGemma API failed: {e}")

    # Try GROQ second (reliable for general queries)
    try:
        logger.info("Attempting GROQ API call...")
        response = call_groq_api(system_message, user_message, temperature, max_tokens)
        if response:
            logger.info("GROQ API call successful")
            return response, "GROQ"
        else:
            logger.info("GROQ API returned None - trying next provider")
    except Exception as e:
        logger.warning(f"GROQ API failed: {e}")

    # Try HuggingFace general API
    try:
        logger.info("Attempting HuggingFace API call...")
        response = call_huggingface_api(
            system_message, user_message, temperature, max_tokens
        )
        if response:
            logger.info("HuggingFace API call successful")
            return response, "HuggingFace"
        else:
            logger.info("HuggingFace API returned None - trying next provider")
    except Exception as e:
        logger.warning(f"HuggingFace API failed: {e}")

    # Try DeepSeek as final fallback
    try:
        logger.info("Attempting DeepSeek API call...")
        response = call_deepseek_api(
            system_message, user_message, temperature, max_tokens
        )
        if response:
            logger.info("DeepSeek API call successful")
            return response, "DeepSeek"
        else:
            logger.info("DeepSeek API returned None - using demo response")
    except Exception as e:
        logger.warning(f"DeepSeek API failed: {e}")

    # If all AI providers fail, generate a demo response
    logger.warning("All AI providers failed or returned None, using demo response")
    demo_response = generate_demo_medical_response(user_message)
    return demo_response, "Demo Mode"


def generate_demo_medical_response(user_message):
    """Generate a demo medical response when all AI providers are unavailable"""
    
    # Common medical keywords and their responses
    demo_responses = {
        "headache": """**HEADACHE - Demo Response**

**ESSENTIALS OF DIAGNOSIS**
• Recurrent or persistent head pain
• May be accompanied by nausea, sensitivity to light
• Can range from mild tension-type to severe migraine

**GENERAL CONSIDERATIONS**
Headaches are among the most common medical complaints. Most are benign but proper evaluation is important to rule out serious underlying conditions.

**CLINICAL FINDINGS**
A. Symptoms and Signs
• Location, quality, and duration of pain
• Associated symptoms (nausea, visual changes)
• Triggers and relieving factors

**DIFFERENTIAL DIAGNOSIS**
• Tension headache
• Migraine
• Cluster headache
• Secondary headaches (infection, medication overuse)

**Note**: This is a demo response. Please consult with a healthcare provider for proper medical evaluation.""",

        "fever": """**FEVER - Demo Response**

**ESSENTIALS OF DIAGNOSIS**
• Body temperature >100.4°F (38°C)
• May be accompanied by chills, sweating
• Often indicates infection or inflammatory process

**GENERAL CONSIDERATIONS**
Fever is a common symptom representing the body's response to infection or other stimuli. Most fevers are self-limiting but warrant evaluation.

**CLINICAL FINDINGS**
A. Symptoms and Signs
• Elevated temperature
• Associated symptoms vary by cause
• May include fatigue, body aches

**DIFFERENTIAL DIAGNOSIS**
• Viral infections
• Bacterial infections
• Inflammatory conditions
• Medication reactions

**Note**: This is a demo response. Please consult with a healthcare provider for proper medical evaluation.""",

        "cough": """**COUGH - Demo Response**

**ESSENTIALS OF DIAGNOSIS**
• Acute or chronic respiratory symptom
• May be dry or productive
• Can indicate various respiratory conditions

**GENERAL CONSIDERATIONS**
Cough is a protective reflex that helps clear airways. Acute cough is often due to viral infections, while chronic cough may indicate underlying conditions.

**CLINICAL FINDINGS**
A. Symptoms and Signs
• Duration and characteristics of cough
• Presence of sputum production
• Associated respiratory symptoms

**DIFFERENTIAL DIAGNOSIS**
• Upper respiratory infection
• Bronchitis
• Pneumonia
• Asthma
• Gastroesophageal reflux

**Note**: This is a demo response. Please consult with a healthcare provider for proper medical evaluation.""",
        
        "chest pain": """**CHEST PAIN - Demo Response**

**ESSENTIALS OF DIAGNOSIS**
• Discomfort or pain in the chest region
• May radiate to arms, neck, jaw, or back
• Can range from mild to severe

**GENERAL CONSIDERATIONS**
Chest pain requires careful evaluation to distinguish between cardiac, pulmonary, gastrointestinal, and musculoskeletal causes.

**CLINICAL FINDINGS**
A. Symptoms and Signs
• Character, location, and radiation of pain
• Relationship to exertion or rest
• Associated symptoms (shortness of breath, sweating)

**DIFFERENTIAL DIAGNOSIS**
• Cardiac: MI, angina, pericarditis
• Pulmonary: PE, pneumonia, pneumothorax
• GI: GERD, esophageal spasm
• Musculoskeletal: costochondritis

**Note**: This is a demo response. Chest pain requires immediate medical evaluation.""",

        "diabetes": """**DIABETES MELLITUS - Demo Response**

**ESSENTIALS OF DIAGNOSIS**
• Fasting glucose ≥126 mg/dL or HbA1c ≥6.5%
• Classic symptoms: polyuria, polydipsia, weight loss
• Random glucose ≥200 mg/dL with symptoms

**GENERAL CONSIDERATIONS**
Diabetes is a chronic metabolic disorder requiring ongoing management to prevent complications.

**CLINICAL FINDINGS**
A. Symptoms and Signs
• Increased urination and thirst
• Unexplained weight loss
• Fatigue and blurred vision

**TREATMENT**
• Lifestyle modifications (diet, exercise)
• Glucose monitoring
• Medications as appropriate
• Regular follow-up

**Note**: This is a demo response. Please consult with a healthcare provider for proper diabetes management.""",

        "hypertension": """**HYPERTENSION - Demo Response**

**ESSENTIALS OF DIAGNOSIS**
• Blood pressure ≥130/80 mmHg on repeated measurements
• Often asymptomatic ("silent killer")
• May present with headache or visual changes

**GENERAL CONSIDERATIONS**
Hypertension is a major risk factor for cardiovascular disease and stroke. Early detection and management are crucial.

**CLINICAL FINDINGS**
A. Symptoms and Signs
• Usually asymptomatic
• May have headaches or dizziness
• End-organ damage in severe cases

**TREATMENT**
• Lifestyle modifications
• Antihypertensive medications
• Regular monitoring
• Cardiovascular risk assessment

**Note**: This is a demo response. Please consult with a healthcare provider for proper hypertension management."""
    }
    
    # Check for keywords in the user message
    message_lower = user_message.lower()
    
    for keyword, response in demo_responses.items():
        if keyword in message_lower:
            return response
    
    # Generic response if no specific keyword matches
    return """**MEDICAL INFORMATION - Demo Response**

I understand you're seeking medical information. This system is currently operating in demo mode as external AI services are temporarily unavailable.

**IMPORTANT NOTICE**
• This is a demonstration response only
• For actual medical concerns, please consult with a qualified healthcare provider
• Emergency situations require immediate medical attention (call 911)

**GENERAL HEALTH GUIDANCE**
• Maintain regular check-ups with your healthcare provider
• Follow prescribed medications as directed
• Maintain healthy lifestyle habits
• Seek professional medical advice for health concerns

**AVAILABLE FEATURES**
• Document storage and organization
• Appointment scheduling
• Medication tracking
• Health record management

**Note**: This system will return to full functionality once AI provider access is restored. For urgent medical questions, please contact your healthcare provider directly."""


@ai_chat_bp.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    if request.method == "GET":
        return _handle_chat_get_request()

    if request.is_json:
        return _handle_chat_json_request()

    # Handle legacy form-based requests
    return _handle_chat_form_request()


def _handle_chat_get_request():
    """Handle GET request for chat interface"""
    family_members = current_user.family_members
    return render_template("ai/chatbot.html", family_members=family_members)


def _handle_chat_json_request():
    """Handle JSON request for chat API with comprehensive query processing"""
    data = request.get_json()
    user_message = data.get("message", "").strip()
    mode = data.get("mode", "private")  # public or private
    patient_id = data.get("patient", "self")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    try:
        # Stage 1: Build base system message and get user context
        system_message, base_citations = _build_system_message(mode, patient_id)

        # Stage 2: Process query through local RAG and web search
        logger.info(f"Processing comprehensive query for user {current_user.id}")

        # Extract user context from system message for query processing
        user_context = ""
        if "Medical History Context:" in system_message:
            context_start = system_message.find("Medical History Context:")
            user_context = system_message[context_start:]

        # Get enhanced context and additional citations from web search only
        from ...utils.web_search import search_web_for_medical_info, format_web_results_for_context, get_web_citations
        
        web_results = search_web_for_medical_info(user_message, max_results=3)
        enhanced_context = format_web_results_for_context(web_results) if web_results else ""
        search_citations = get_web_citations(web_results) if web_results else []

        # Stage 3: Build final system message with all context
        final_system_message = _build_enhanced_system_message(
            mode, system_message, enhanced_context
        )

        # Combine all citations
        all_citations = base_citations + search_citations

        # Stage 4: Generate AI response (now always returns a response due to demo fallback)
        ai_response, model_used = _get_ai_response(final_system_message, user_message)

        # Process the AI response to fold thinking and format citations
        processed_response = _process_chat_response(ai_response, all_citations)

        response_data = {
            "response": processed_response,
            "mode": mode,
            "patient": patient_id,
            "model": model_used or "Demo Mode",
            "search_info": {
                "local_results": len(
                    [
                        c
                        for c in search_citations
                        if c.get("type") == "Medical Reference"
                    ]
                ),
                "web_results": len(
                    [c for c in search_citations if c.get("type") == "Web Search"]
                ),
                "total_citations": len(all_citations),
            },
        }
        return jsonify(response_data)

    except Exception as e:
        current_app.logger.error(f"Chat error: {e}")
        return jsonify({"error": "Chat service error"}), 500


def _handle_chat_form_request():
    """Handle legacy form-based chat request"""
    # ...existing code...
    pass


def _build_system_message(mode, patient_id):
    """Build comprehensive system message based on chat mode and patient selection"""
    if mode == "public":
        return (
            """You are an advanced medical AI assistant providing comprehensive health information based on current medical evidence and clinical guidelines.

        RESPONSE STRUCTURE: For medical topics, organize your response as follows:

        **OVERVIEW**
        • Brief, clear explanation of the condition/topic
        • Why this information is relevant to the user

        **KEY INFORMATION**
        • Essential facts the user should know
        • Clinical significance and implications
        • Prevalence and demographics when relevant

        **DETAILED EXPLANATION**
        • Pathophysiology or mechanism (when appropriate)
        • Signs and symptoms (organized by frequency/importance)
        • Risk factors and prevention strategies
        • Diagnostic approaches and criteria

        **TREATMENT OPTIONS**
        • First-line and evidence-based treatments
        • Lifestyle modifications and self-care measures
        • When to seek professional care
        • Prognosis and expected outcomes

        **IMPORTANT CONSIDERATIONS**
        • Red flags or warning signs
        • Contraindications or special populations
        • Drug interactions or side effects (when relevant)
        • Follow-up recommendations

        **ADDITIONAL RESOURCES**
        • When to consult healthcare providers
        • Specialist referrals when appropriate
        • Patient education resources

        GUIDELINES:
        - Provide comprehensive, evidence-based information
        - Use clear, accessible language while maintaining medical accuracy
        - Include practical, actionable advice when appropriate
        - Always emphasize the importance of professional medical consultation
        - Address common concerns and misconceptions
        - Provide context for why information is important

        DISCLAIMERS:
        - This is educational information only, not personalized medical advice
        - Individual cases may vary significantly
        - Professional medical evaluation is essential for diagnosis and treatment
        - Emergency symptoms require immediate medical attention""",
            [],
        )
    else:
        # Private mode - include user context
        user_context, citations = get_user_context(mode, patient_id)
        if user_context:
            return (
                f"""You are an advanced medical AI assistant with access to this user's personal health records and medical history. Provide comprehensive, personalized health insights and recommendations.

            RESPONSE STRUCTURE: For medical topics, organize your response as follows:

            **PERSONALIZED OVERVIEW**
            • Brief explanation relevant to this specific user
            • Connection to their medical history when applicable
            • Why this information is particularly important for them

            **ANALYSIS OF USER'S SITUATION**
            • Review relevant information from their medical records
            • Identify patterns, trends, or connections in their health data
            • Highlight any risk factors or protective factors specific to them

            **COMPREHENSIVE INFORMATION**
            • Detailed medical information about the topic/condition
            • Clinical significance and implications for this user
            • How their medical history affects prognosis or treatment options

            **PERSONALIZED RECOMMENDATIONS**
            • Specific recommendations based on their health profile
            • Medication considerations (interactions with current medications)
            • Lifestyle modifications tailored to their situation
            • Prevention strategies relevant to their risk factors

            **CLINICAL INSIGHTS**
            • Patterns in their health records that warrant attention
            • Correlations between different health conditions or medications
            • Timeline analysis of their health progression
            • Red flags or concerning trends that need professional evaluation

            **NEXT STEPS**
            • Specific actions recommended for this user
            • Questions to discuss with their healthcare provider
            • Follow-up recommendations based on their history
            • When to seek immediate medical attention

            PERSONALIZATION GUIDELINES:
            - Always reference relevant information from their medical records
            - Consider their complete medication list for interaction warnings
            - Account for their medical history when making recommendations
            - Highlight patterns or trends in their health data
            - Provide context for how their situation differs from general cases
            - Be specific about timing and urgency based on their health status

            Medical History Context:
            {user_context}

            Use this context to provide medically sound, personalized responses. Always cite relevant information from the medical records when applicable, and highlight any patterns or concerns that warrant professional attention.""",
                citations,
            )
        else:
            return (
                """You are MedGemma, a specialized medical AI assistant for personal health management.

            When responding to queries about diseases, conditions, or medical topics, structure your responses in Current Medical Diagnosis & Treatment (CMDT) format:

            **DISEASE/CONDITION NAME**

            **ESSENTIALS OF DIAGNOSIS**
            • Key clinical features and diagnostic criteria
            • Most important signs and symptoms
            • Laboratory or imaging findings when relevant

            **GENERAL CONSIDERATIONS**
            • Epidemiology and risk factors
            • Pathophysiology overview
            • Classification or staging if applicable

            **CLINICAL FINDINGS**
            A. Symptoms and Signs
            • Present symptoms in order of frequency
            • Physical examination findings

            B. Laboratory Findings
            • Relevant laboratory tests
            • Typical values or ranges

            C. Imaging
            • Useful imaging modalities
            • Expected findings

            **DIFFERENTIAL DIAGNOSIS**
            • Other conditions to consider
            • How to distinguish between them

            **TREATMENT**
            A. General Measures
            • Lifestyle modifications
            • Supportive care

            B. Medications
            • First-line treatments
            • Alternative options
            • Dosing considerations

            **PROGNOSIS**
            • Expected outcomes
            • Factors affecting prognosis

            **WHEN TO REFER**
            • Indications for specialist consultation
            • Emergency situations requiring immediate care

            For general health queries, provide personalized health guidance and insights based on medical best practices.

            Focus on:
            - Preventive health measures
            - Health monitoring and tracking guidance
            - General wellness recommendations
            - When to seek professional medical care

            Always remind users to consult with healthcare professionals for specific medical decisions and diagnoses.""",
                [],
            )


def _build_enhanced_system_message(
    mode: str, base_message: str, enhanced_context: str
) -> str:
    """Build enhanced system message with local RAG and web search context"""
    if mode == "public":
        if enhanced_context:
            return f"""{base_message}

Additional Context from Medical References and Current Information:
{enhanced_context}

Use this additional context to provide more comprehensive and up-to-date information while maintaining your role as a general medical information assistant."""
        return base_message
    else:
        # Private mode - add enhanced context to existing medical history
        if enhanced_context:
            return f"""{base_message}

Additional Medical Knowledge and Current Information:
{enhanced_context}

Integrate this additional context with the user's medical history to provide the most comprehensive and personalized response possible."""
        return base_message


def _get_ai_response(system_message, user_message):
    """Get AI response with fallback logic"""
    ai_response, model_used = call_ai_with_fallback(system_message, user_message)
    return ai_response, model_used


def _handle_chat_form_request():
    """Handle legacy form-based chat request"""
    user_message = request.form.get("message")
    if user_message:
        try:
            system_message = """You are MedGemma, a specialized medical AI assistant developed by Google for healthcare applications.
        You have been trained on extensive medical literature and datasets to provide accurate health information.

        When responding to queries about diseases, conditions, or medical topics, structure your responses in Current Medical Diagnosis & Treatment (CMDT) format:

        **DISEASE/CONDITION NAME**

        **ESSENTIALS OF DIAGNOSIS**
        • Key clinical features and diagnostic criteria
        • Most important signs and symptoms
        • Laboratory or imaging findings when relevant

        **GENERAL CONSIDERATIONS**
        • Epidemiology and risk factors
        • Pathophysiology overview
        • Classification or staging if applicable

        **CLINICAL FINDINGS**
        A. Symptoms and Signs
        • Present symptoms in order of frequency
        • Physical examination findings

        B. Laboratory Findings
        • Relevant laboratory tests
        • Typical values or ranges

        C. Imaging
        • Useful imaging modalities
        • Expected findings

        **DIFFERENTIAL DIAGNOSIS**
        • Other conditions to consider
        • How to distinguish between them

        **TREATMENT**
        A. General Measures
        • Lifestyle modifications
        • Supportive care

        B. Medications
        • First-line treatments
        • Alternative options
        • Dosing considerations

        **PROGNOSIS**
        • Expected outcomes
        • Factors affecting prognosis

        **WHEN TO REFER**
        • Indications for specialist consultation
        • Emergency situations requiring immediate care

        For non-medical queries, respond normally with evidence-based information. Always remind users to consult with healthcare professionals for personalized medical advice and specific diagnoses."""

            ai_response, model_used = call_ai_with_fallback(
                system_message, user_message
            )
            if ai_response:
                # Process the response to clean up thinking and add formatting
                ai_response = _process_chat_response(ai_response, [])
            else:
                ai_response = "I'm sorry, I'm experiencing technical difficulties. Please try again later."
                model_used = None
        except Exception as e:
            logger.error(f"Form chat error: {e}")
            ai_response = (
                "I encountered an error processing your request. Please try again."
            )
            model_used = None
    else:
        ai_response = None
        model_used = None

    family_members = current_user.family_members
    
    # Add timestamp for display
    from datetime import datetime
    current_time = datetime.now().strftime('%B %d, %Y at %I:%M:%S %p')
    
    return render_template(
        "ai/chat.html",
        user_message=user_message,
        ai_response=ai_response,
        model_used=model_used,
        response_time=current_time if ai_response else None,
        family_members=family_members,
    )

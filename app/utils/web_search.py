"""
Web Search Utilities for PHRM

Provides functionality to search the web for medical information using Google Search via Serper API.
"""

import logging
import os
from typing import Any

import requests
from flask import current_app

logger = logging.getLogger(__name__)

# Constants
MAX_WEB_RESULTS = 5
MAX_SNIPPET_LENGTH = 200  # Maximum length for web search snippets
WEB_SEARCH_TIMEOUT = 10
MEDICAL_DOMAINS = [
    "pubmed.ncbi.nlm.nih.gov",
    "mayoclinic.org",
    "webmd.com",
    "medlineplus.gov",
    "who.int",
    "cdc.gov",
    "nih.gov",
    "healthline.com",
    "medicalnewstoday.com",
    "patient.info",
]


def get_serper_api_key():
    """Get Serper API key from Flask config or environment"""
    try:
        if current_app:
            key = current_app.config.get("SERPER_API_KEY")
            if key:
                return key
    except RuntimeError:
        pass
    return os.environ.get("SERPER_API_KEY")


def search_web_for_medical_info(
    query: str, max_results: int = MAX_WEB_RESULTS
) -> list[dict[str, Any]]:
    """
    Search the web for medical information using Google Search via Serper API.

    Args:
        query: Medical query to search for
        max_results: Maximum number of results to return

    Returns:
        List of search results with title, url, snippet, and source info
    """
    try:
        # Try Google Search via Serper API first
        results = _search_google_serper(query, max_results)
        if results:
            return results

        # Fallback to other search methods if needed
        logger.warning("Google/Serper search failed, trying alternative methods")
        return _search_fallback(query, max_results)

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return []


def _search_google_serper(query: str, max_results: int) -> list[dict[str, Any]]:
    """
    Search using Google Search via Serper API
    """
    try:
        api_key = get_serper_api_key()
        if not api_key:
            logger.warning("Serper API key not configured")
            return []

        # Add medical terms to improve relevance
        medical_query = f"{query} medical health information"

        # Use Serper API for Google Search
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": medical_query,
            "num": max_results * 2,  # Get extra results to filter better
            "gl": "us",  # Geographic location
            "hl": "en"   # Language
        }

        response = requests.post(url, headers=headers, json=payload, timeout=WEB_SEARCH_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        results = []

        # Process organic results
        for result in data.get("organic", [])[:max_results]:
            snippet = result.get("snippet", "")
            if len(snippet) > MAX_SNIPPET_LENGTH:
                snippet = snippet[:MAX_SNIPPET_LENGTH] + "..."
                
            results.append({
                "title": result.get("title", ""),
                "url": result.get("link", ""),
                "snippet": snippet,
                "source": "Google Search",
                "type": "organic",
                "relevance_score": _calculate_medical_relevance(result.get("title", "") + " " + snippet),
            })

        # Add knowledge graph if available
        if data.get("knowledgeGraph"):
            kg = data["knowledgeGraph"]
            description = kg.get("description", "")
            if len(description) > MAX_SNIPPET_LENGTH:
                description = description[:MAX_SNIPPET_LENGTH] + "..."
                
            results.insert(0, {
                "title": kg.get("title", "Medical Information"),
                "url": kg.get("descriptionLink", ""),
                "snippet": description,
                "source": "Google Knowledge Graph",
                "type": "knowledge_graph",
                "relevance_score": 0.95,
            })

        # Add featured snippet if available
        if data.get("answerBox"):
            answer = data["answerBox"]
            snippet = answer.get("snippet", answer.get("answer", ""))
            if len(snippet) > MAX_SNIPPET_LENGTH:
                snippet = snippet[:MAX_SNIPPET_LENGTH] + "..."
                
            results.insert(0, {
                "title": answer.get("title", "Featured Answer"),
                "url": answer.get("link", ""),
                "snippet": snippet,
                "source": "Google Featured Snippet",
                "type": "featured_snippet",
                "relevance_score": 0.9,
            })

        # Filter and rank results
        filtered_results = _filter_medical_results(results)
        return sorted(filtered_results, key=lambda x: x.get("relevance_score", 0), reverse=True)[:max_results]

    except Exception as e:
        logger.error(f"Google/Serper search error: {e}")
        return []


def _calculate_medical_relevance(text: str) -> float:
    """Calculate relevance score based on medical keywords"""
    medical_keywords = [
        "medical", "health", "disease", "symptoms", "treatment", "diagnosis", 
        "condition", "medicine", "doctor", "patient", "clinical", "therapeutic",
        "healthcare", "medication", "syndrome", "disorder", "pathology"
    ]
    
    text_lower = text.lower()
    score = 0.5  # Base score
    
    for keyword in medical_keywords:
        if keyword in text_lower:
            score += 0.1
    
    # Boost score for medical domains
    for domain in MEDICAL_DOMAINS:
        if domain in text_lower:
            score += 0.2
            break
    
    return min(score, 1.0)  # Cap at 1.0


def _search_fallback(query: str, _max_results: int) -> list[dict[str, Any]]:
    """
    Fallback search method - return empty results instead of placeholder
    """
    try:
        # Instead of returning a placeholder, return empty results
        # This way the citation system won't show unhelpful fallback messages
        logger.info(f"Web search fallback for query: {query} - returning empty results")
        return []
    except Exception as e:
        logger.error(f"Fallback search error: {e}")
        return []


def _filter_medical_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Filter and rank results based on medical relevance
    """
    filtered = []

    for result in results:
        # Check if result is from a trusted medical domain
        url = result.get("url", "").lower()
        is_medical_domain = any(domain in url for domain in MEDICAL_DOMAINS)

        # Check if content contains medical terms
        text = (result.get("snippet", "") + " " + result.get("title", "")).lower()
        medical_terms = [
            "medical",
            "health",
            "disease",
            "treatment",
            "symptoms",
            "diagnosis",
            "patient",
            "clinical",
            "therapy",
            "medication",
            "doctor",
            "physician",
        ]
        has_medical_content = any(term in text for term in medical_terms)

        if is_medical_domain:
            result["relevance_score"] = result.get("relevance_score", 0.5) + 0.3

        if has_medical_content or is_medical_domain:
            filtered.append(result)

    # Sort by relevance score
    filtered.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    return filtered


def format_web_results_for_context(results: list[dict[str, Any]]) -> str:
    """
    Format web search results for inclusion in AI context
    """
    if not results:
        return ""

    context = "Recent web search results:\n\n"

    for i, result in enumerate(results[:3], 1):  # Limit to top 3 for context
        title = result.get("title", "Unknown")
        snippet = result.get("snippet", "")
        source = result.get("source", "Web")

        context += f"{i}. **{title}** ({source})\n"
        if snippet:
            # Limit snippet length
            snippet = (
                snippet[:MAX_SNIPPET_LENGTH] + "..."
                if len(snippet) > MAX_SNIPPET_LENGTH
                else snippet
            )
            context += f"   {snippet}\n\n"

    return context


def get_web_citations(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Convert web results to citation format for response processing
    """
    citations = []

    for result in results:
        citation = {
            "title": result.get("title", "Web Search Result"),
            "url": result.get("url", ""),
            "type": "Web Search",
            "source": result.get("source", "Internet"),
            "relevance": result.get("relevance_score", 0.5),
            "search_type": result.get(
                "type", "web_result"
            ),  # instant_answer, related_topic, etc.
        }
        citations.append(citation)

    return citations

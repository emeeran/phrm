"""
Web Search Utilities for PHRM

Provides functionality to search the web for medical information to supplement local knowledge.
"""

import logging
from typing import Any

import requests

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
]


def search_web_for_medical_info(
    query: str, max_results: int = MAX_WEB_RESULTS
) -> list[dict[str, Any]]:
    """
    Search the web for medical information using multiple search approaches.

    Args:
        query: Medical query to search for
        max_results: Maximum number of results to return

    Returns:
        List of search results with title, url, snippet, and source info
    """
    try:
        # Try DuckDuckGo first (privacy-focused, no API key needed)
        results = _search_duckduckgo(query, max_results)
        if results:
            return results

        # Fallback to other search methods if needed
        logger.warning("DuckDuckGo search failed, trying alternative methods")
        return _search_fallback(query, max_results)

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return []


def _search_duckduckgo(query: str, max_results: int) -> list[dict[str, Any]]:
    """
    Search using DuckDuckGo Instant Answer API
    """
    try:
        # Add medical terms to improve relevance
        medical_query = f"{query} medical health information"

        # Use DuckDuckGo's instant answer API
        url = "https://api.duckduckgo.com/"
        params = {
            "q": medical_query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }

        response = requests.get(url, params=params, timeout=WEB_SEARCH_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        results = []

        # Get instant answer if available
        if data.get("Answer"):
            results.append(
                {
                    "title": "DuckDuckGo Medical Answer",
                    "url": data.get("AnswerURL", ""),
                    "snippet": data.get("Answer", ""),
                    "source": "DuckDuckGo",
                    "type": "instant_answer",
                    "relevance_score": 0.9,
                }
            )

        # Get related topics
        for topic in data.get("RelatedTopics", [])[: max_results - 1]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(
                    {
                        "title": topic.get("FirstURL", "")
                        .split("/")[-1]
                        .replace("_", " "),
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", ""),
                        "source": "DuckDuckGo",
                        "type": "related_topic",
                        "relevance_score": 0.7,
                    }
                )

        # Filter for medical relevance
        return _filter_medical_results(results)[:max_results]

    except Exception as e:
        logger.error(f"DuckDuckGo search error: {e}")
        return []


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

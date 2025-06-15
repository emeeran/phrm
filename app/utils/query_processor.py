"""
Comprehensive Query Handler for PHRM

Implements a multi-stage query processing system:
1. Search local vectorized medical references
2. Search web for real-time information
3. Generate AI response with combined context
"""

import logging
from typing import Any

from ..utils.local_rag import get_rag_status, search_medical_references
from ..utils.web_search import (
    format_web_results_for_context,
    get_web_citations,
    search_web_for_medical_info,
)

logger = logging.getLogger(__name__)

# Constants
MIN_CITATION_CONFIDENCE = (
    0.3  # Lowered threshold for vector similarity - reasonable for RAG
)
HIGH_CONFIDENCE_THRESHOLD = 0.8  # High confidence citation threshold
MAX_CONTENT_PREVIEW = 300  # Maximum content length for context preview
CITATION_CONTENT_PREVIEW = 100  # Maximum content length for citation preview
MAX_TITLE_LENGTH = 50  # Maximum title length before truncation
MAX_LOCAL_RESULTS = 5
MAX_WEB_RESULTS = 3
MIN_LOCAL_CONFIDENCE = MIN_CITATION_CONFIDENCE  # For compatibility


class QueryProcessor:
    """Handles comprehensive query processing with local RAG and web search"""

    def __init__(self):
        self.rag_available = False
        self.web_enabled = True
        self._check_systems()

    def _check_systems(self):
        """Check availability of RAG and web search systems"""
        try:
            rag_status = get_rag_status()

            # If ChromaDB is available but not initialized, try to initialize it
            if rag_status.get("chromadb_available", False) and not rag_status.get(
                "collection_initialized", False
            ):
                # Trigger initialization by attempting a search
                try:
                    search_medical_references("test", n_results=1)
                    # Re-check status after initialization attempt
                    rag_status = get_rag_status()
                except Exception as e:
                    logger.warning(f"Could not initialize RAG during check: {e}")

            self.rag_available = rag_status.get(
                "chromadb_available", False
            ) and rag_status.get("collection_initialized", False)
            logger.info(f"RAG system available: {self.rag_available}")
        except Exception as e:
            logger.warning(f"Could not check RAG status: {e}")
            self.rag_available = False

    def process_query(
        self, query: str, user_context: str = ""
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Process a query through the complete pipeline:
        1. Local RAG search
        2. Web search
        3. Context building

        Args:
            query: User's medical query
            user_context: Additional user context (medical records, etc.)

        Returns:
            Tuple of (enhanced_context, combined_citations)
        """
        logger.info(f"Processing query: {query[:50]}...")

        enhanced_context = user_context
        all_citations = []

        # Stage 1: Search local vectorized references
        local_results, local_citations = self._search_local_references(query)
        if local_results:
            enhanced_context += f"\n\n{local_results}"
            all_citations.extend(local_citations)
            logger.info(f"Added {len(local_citations)} local reference citations")

        # Stage 2: Search web for real-time information
        web_results, web_citations = self._search_web_references(query)
        if web_results:
            enhanced_context += f"\n\n{web_results}"
            all_citations.extend(web_citations)
            logger.info(f"Added {len(web_citations)} web citations")

        # Stage 3: Add search metadata to context
        search_summary = self._build_search_summary(
            query, local_citations, web_citations
        )
        enhanced_context += f"\n\n{search_summary}"

        return enhanced_context, all_citations

    def _search_local_references(self, query: str) -> tuple[str, list[dict[str, Any]]]:
        """Search local vectorized medical references"""
        if not self.rag_available:
            logger.info("RAG system not available, skipping local search")
            return "", []

        try:
            logger.info("Searching local medical references...")
            results = search_medical_references(query, n_results=MAX_LOCAL_RESULTS)

            if not results:
                logger.info("No local reference results found")
                return "", []

            # Format results for context
            context = "Local Medical Reference Results:\n\n"
            citations = []

            for i, result in enumerate(results, 1):
                # Extract metadata for proper citation formatting
                source_file = result.get("source", "")
                page_number = result.get("page", 0)
                content = result.get("text", result.get("content", ""))
                confidence = result.get(
                    "relevance_score",
                    result.get("confidence", result.get("distance", 0)),
                )

                # Format book title from filename
                book_title = self._format_book_title(source_file)

                # Create formatted citation
                citation_ref = f"{book_title}"
                if page_number and page_number > 0:
                    citation_ref += f" p-{page_number}"

                # Only include high-confidence results in context
                if confidence >= MIN_LOCAL_CONFIDENCE:
                    context += f"{i}. **{citation_ref}**\n"
                    if content:
                        # Limit content length for context
                        content_preview = (
                            content[:MAX_CONTENT_PREVIEW] + "..."
                            if len(content) > MAX_CONTENT_PREVIEW
                            else content
                        )
                        context += f"   {content_preview}\n\n"

                # Add to citations with detailed information
                citations.append(
                    {
                        "title": citation_ref,
                        "type": "Medical Reference",
                        "source": "Local Medical Library",
                        "book": book_title,
                        "page": page_number if page_number > 0 else None,
                        "confidence": confidence,
                        "content_preview": (
                            content[:CITATION_CONTENT_PREVIEW] + "..."
                            if len(content) > CITATION_CONTENT_PREVIEW
                            else content
                        ),
                        "file_path": source_file,
                    }
                )

            logger.info(
                f"Found {len(results)} local results, {len([c for c in citations if c['confidence'] >= MIN_LOCAL_CONFIDENCE])} high-confidence"
            )
            return context, citations

        except Exception as e:
            logger.error(f"Local search error: {e}")
            return "", []

    def _format_book_title(self, file_path: str) -> str:
        """Format book title from file path for citations"""
        if not file_path:
            return "Medical Reference"

        # Extract filename
        filename = file_path.split("/")[-1] if "/" in file_path else file_path

        # Remove file extension
        if "." in filename:
            filename = ".".join(filename.split(".")[:-1])

        # Clean up common patterns and format nicely
        title = filename.replace("_", " ").replace("-", " ")

        # Handle common medical book patterns
        title_mappings = {
            "CURRENT MEDICAL DIAGNOSIS AND TREATMENT": "Current Medical Diagnosis & Treatment",
            "THE GALE ENCYCLOPEDIA OF MEDICINE": "The Gale Encyclopedia of Medicine",
            "THE COMPLETE DRUG REFERENCE": "The Complete Drug Reference",
            "AN ATLAS OF PARKINSONS DISEASE": "An Atlas of Parkinson's Disease",
        }

        # Check for exact matches first
        title_upper = title.upper()
        for pattern, formatted in title_mappings.items():
            if pattern in title_upper:
                return formatted

        # Generic formatting for other books
        words = title.split()
        formatted_words = []

        for word in words:
            # Capitalize important words, but keep articles/prepositions lowercase
            if word.lower() in [
                "and",
                "of",
                "the",
                "a",
                "an",
                "in",
                "on",
                "at",
                "by",
                "for",
                "with",
            ]:
                formatted_words.append(word.lower())
            else:
                formatted_words.append(word.capitalize())

        # Always capitalize first word
        if formatted_words:
            formatted_words[0] = formatted_words[0].capitalize()

        formatted_title = " ".join(formatted_words)

        # Limit length for readability
        if len(formatted_title) > MAX_TITLE_LENGTH:
            formatted_title = formatted_title[: MAX_TITLE_LENGTH - 3] + "..."

        return formatted_title

    def _search_web_references(self, query: str) -> tuple[str, list[dict[str, Any]]]:
        """Search web for real-time medical information"""
        if not self.web_enabled:
            logger.info("Web search disabled, skipping")
            return "", []

        try:
            logger.info("Searching web for real-time information...")
            results = search_web_for_medical_info(query, max_results=MAX_WEB_RESULTS)

            if not results:
                logger.info("No web results found")
                return "", []

            context = format_web_results_for_context(results)
            citations = get_web_citations(results)

            logger.info(f"Found {len(results)} web results")
            return context, citations

        except Exception as e:
            logger.error(f"Web search error: {e}")
            return "", []

    def _build_search_summary(
        self, query: str, local_citations: list, web_citations: list
    ) -> str:
        """Build a summary of search results for AI context"""
        summary = "Search Summary:\n"
        summary += f"- Query: {query}\n"
        summary += f"- Local references found: {len(local_citations)}\n"
        summary += f"- Web sources found: {len(web_citations)}\n"

        if local_citations:
            high_conf = len(
                [
                    c
                    for c in local_citations
                    if c.get("confidence", 0) >= MIN_LOCAL_CONFIDENCE
                ]
            )
            summary += f"- High-confidence local results: {high_conf}\n"

        summary += "\nUse this information to provide a comprehensive, evidence-based response."
        return summary


# Global instance
query_processor = QueryProcessor()


def process_medical_query(
    query: str, user_context: str = ""
) -> tuple[str, list[dict[str, Any]]]:
    """
    Main entry point for processing medical queries

    Args:
        query: The medical question or query
        user_context: Additional context (user medical records, etc.)

    Returns:
        Tuple of (enhanced_context_for_ai, citations_for_response)
    """
    return query_processor.process_query(query, user_context)

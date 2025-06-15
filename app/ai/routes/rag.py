"""
RAG (Retrieval-Augmented Generation) Routes

Provides API endpoints for searching medical reference books and managing
the local RAG system.
"""

from flask import Blueprint, current_app, jsonify, request
from flask_login import login_required

from ...utils.local_rag import (
    get_rag_status,
    refresh_reference_books,
    search_medical_references,
)

# Constants
MAX_RAG_RESULTS = 20

rag_bp = Blueprint("rag", __name__, url_prefix="/api/rag")


@rag_bp.route("/status", methods=["GET"])
@login_required
def get_status():
    """Get current status of the RAG service"""
    try:
        status = get_rag_status()
        return jsonify({"success": True, "status": status})
    except Exception as e:
        current_app.logger.error(f"Error getting RAG status: {e}")
        return jsonify({"success": False, "error": "Failed to get RAG status"}), 500


@rag_bp.route("/search", methods=["POST"])
@login_required
def search():
    """Search medical reference books"""
    try:
        data = request.get_json()
        if not data or not data.get("query"):
            return (
                jsonify({"success": False, "error": "Query parameter is required"}),
                400,
            )

        query = data["query"]
        n_results = data.get("n_results", 5)

        # Validate n_results
        if n_results < 1 or n_results > MAX_RAG_RESULTS:
            n_results = 5

        results = search_medical_references(query, n_results)

        return jsonify(
            {"success": True, "query": query, "results": results, "count": len(results)}
        )

    except Exception as e:
        current_app.logger.error(f"Error searching RAG: {e}")
        return jsonify({"success": False, "error": "Search failed"}), 500


@rag_bp.route("/refresh", methods=["POST"])
@login_required
def refresh():
    """Refresh/re-process all reference books"""
    try:
        success = refresh_reference_books()

        if success:
            return jsonify(
                {
                    "success": True,
                    "message": "Reference books refresh started in background",
                }
            )
        else:
            return (
                jsonify({"success": False, "error": "Failed to start refresh process"}),
                500,
            )

    except Exception as e:
        current_app.logger.error(f"Error refreshing RAG: {e}")
        return jsonify({"success": False, "error": "Refresh failed"}), 500


@rag_bp.route("/start-vectorization", methods=["POST"])
@login_required
def start_vectorization():
    """Start background vectorization process"""
    try:
        from ...utils.local_rag import start_background_vectorization

        success = start_background_vectorization()

        if success:
            return jsonify(
                {"success": True, "message": "Background vectorization started"}
            )
        else:
            return (
                jsonify({"success": False, "error": "Failed to start vectorization"}),
                500,
            )

    except Exception as e:
        current_app.logger.error(f"Error starting vectorization: {e}")
        return (
            jsonify({"success": False, "error": "Failed to start vectorization"}),
            500,
        )


@rag_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint for RAG service"""
    try:
        status = get_rag_status()

        # Basic health check
        is_healthy = (
            status.get("chromadb_available", False)
            and status.get("pymupdf_available", False)
            and status.get("collection_initialized", False)
        )

        return jsonify(
            {
                "healthy": is_healthy,
                "components": {
                    "chromadb": status.get("chromadb_available", False),
                    "pymupdf": status.get("pymupdf_available", False),
                    "collection": status.get("collection_initialized", False),
                },
                "processed_files": status.get("processed_files_count", 0),
                "last_updated": status.get("last_updated"),
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error checking RAG health: {e}")
        return jsonify({"healthy": False, "error": str(e)}), 500

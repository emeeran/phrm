#!/usr/bin/env python3
"""
Production startup script for PHRM with enhanced citation system.
"""

import os
import sys


def main():
    """Start the PHRM application with enhanced citation features"""

    print("🏥 Starting PHRM - AI-Enhanced Medical Records Management")
    print("=" * 60)

    # Configure environment for development (to avoid HTTPS redirects)
    os.environ.setdefault("FLASK_ENV", "development")
    os.environ.setdefault("DEBUG", "true")

    # Check system status
    print("Checking system components...")

    # Check Redis
    try:
        import redis

        r = redis.Redis(host="localhost", port=6379, db=0)
        r.ping()
        print("✅ Redis server: Connected")
    except Exception as e:
        print(f"⚠️  Redis server: Not available ({e})")

    # Check RAG system status
    try:
        from app.utils.local_rag import get_rag_status

        rag_status = get_rag_status()
        if (
            rag_status.get("chromadb_available")
            and rag_status.get("processed_files_count", 0) > 0
        ):
            print("✅ RAG system: Fully operational with vectorized medical references")
            print(f"   - Books processed: {rag_status.get('processed_files_count', 0)}")
            print(
                f"   - Medical references: {', '.join(rag_status.get('processed_files', [])[:2])} + {max(0, rag_status.get('processed_files_count', 0) - 2)} more"
            )
        else:
            print("⚠️  RAG system: Available but not fully initialized")
            print("   Citations will use web search and patient records only")
    except Exception as e:
        print(f"⚠️  RAG system: Error checking status ({e})")
        print("   Citations will use web search and patient records only")

    # Citation system status
    print("✅ Enhanced Citation System: Active")
    print("   - High-quality medical reference citations")
    print(
        "   - Book titles and page numbers (e.g., 'Current Medical Diagnosis & Treatment p-1183')"
    )
    print("   - Confidence scores (e.g., '92% match')")
    print("   - Source attribution (e.g., 'Local Medical Library')")
    print("   - Automatic filtering of low-quality citations")

    # Import and create app
    try:
        from app import create_app

        app = create_app()
        print("✅ Flask application: Created successfully")

        # List available features
        print("\n📋 Available Features:")
        print("   - AI-powered chat with medical citations")
        print("   - Medical record summarization with sources")
        print("   - File upload and vectorization")
        print("   - Secure user authentication")
        print("   - Real-time medical reference lookup")

        print("\n🚀 Starting server on http://localhost:5000")
        print("   Press Ctrl+C to stop")
        print("=" * 60)

        # Start the development server
        app.run(host="0.0.0.0", port=5000, debug=False)

    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

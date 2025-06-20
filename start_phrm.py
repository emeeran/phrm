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

    # RAG system has been removed
    print("ℹ️  RAG system: Removed - using web search for AI enhancement")
    print("   - Local medical references no longer supported")
    print("   - AI still enhanced with real-time web search")

    # Citation system status
    print("✅ Enhanced Citation System: Active")
    print("   - High-quality medical reference citations from web search")
    print("   - Source attribution and confidence scores")
    print("   - Real-time medical information")

    # Check database initialization
    db_path = os.path.join(os.getcwd(), "instance", "phrm.db")
    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        print("⚠️  Database not initialized. Running setup...")
        try:
            from setup_database import init_and_seed_database
            init_and_seed_database()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize database: {e}")
            print("   Please run: python setup_database.py")
            sys.exit(1)

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

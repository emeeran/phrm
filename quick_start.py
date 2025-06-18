#!/usr/bin/env python3
"""
PHRM Quick-Fix Launcher

This script fixes common database issues and starts the server on an available port.
"""

import os
import socket
import sys


def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def find_available_port(preferred=5000, alternatives=[5001, 5002, 8000, 8080]):
    """Find an available port to use"""
    if not is_port_in_use(preferred):
        return preferred

    for port in alternatives:
        if not is_port_in_use(port):
            return port

    return None


# Load environment variables
try:
    from dotenv import load_dotenv

    env_file = os.path.join(os.path.dirname(__file__), ".env.production")
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
    else:
        print(f"⚠️  Environment file not found: {env_file}")
except ImportError:
    print("⚠️  python-dotenv not installed, skipping .env file loading")

# Import Flask app
try:
    print("⏳ Initializing application...")
    from app import create_app
    from app.models import db

    # Create app
    app = create_app()

    # Fix database
    print("⏳ Checking database...")
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables verified")

        # Create index directly on model
        from app.models.core.medical_condition import MedicalCondition

        print("⏳ Checking indexes...")
        try:
            from sqlalchemy import Index

            # Create index programmatically
            idx = Index(
                "idx_medical_conditions_user",
                MedicalCondition.user_id,
                MedicalCondition.current_status,
            )
            idx.create(db.engine, checkfirst=True)
            print("✅ Database indexes verified")
        except Exception as e:
            print(f"⚠️  Index check: {e}")

    print("✅ Database initialization complete")

    # Find available port
    port = find_available_port()
    if not port:
        print("❌ No available ports found. Please free a port and try again.")
        sys.exit(1)

    print(f"\n🚀 Starting PHRM server on http://localhost:{port}")
    print("   Press CTRL+C to stop the server")
    print("=" * 60)

    # Start the server
    app.run(host="0.0.0.0", port=port, debug=True)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

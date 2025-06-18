#!/usr/bin/env python3
"""
Simple database initialization script for PHRM.
"""

import os
import sys

# Load environment variables
try:
    from dotenv import load_dotenv

    env_file = os.path.join(os.path.dirname(__file__), ".env.production")
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
except ImportError:
    print("⚠️  python-dotenv not installed, using environment as-is")

# Import the Flask app and database
try:
    print("Importing app...")
    from app import create_app
    from app.models import db

    print("Creating app...")
    app = create_app()

    print("Initializing database...")
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created")

        # Commit changes
        db.session.commit()
        print("✅ Database initialization successful")

except Exception as e:
    print(f"❌ Error during database initialization: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("\n✅ Database initialization complete!")

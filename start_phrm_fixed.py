#!/usr/bin/env python3
"""
Simple PHRM startup script (fixed version)
"""

import os
import sys

from dotenv import load_dotenv


def main():
    """Start the PHRM application with basic error handling"""
    print("🏥 Starting PHRM - AI-Enhanced Medical Records Management")
    print("=" * 60)

    # Load .env.production file
    env_file = os.path.join(os.path.dirname(__file__), ".env.production")
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")

    # Initialize the database first
    try:
        from app import create_app
        from app.models import db

        app = create_app()

        with app.app_context():
            # Create all tables that might be missing
            db.create_all()
            print("✅ Database initialized")

            # Create the index on medical_condition table
            try:
                db.session.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_medical_conditions_user
                    ON medical_condition (user_id, status);
                """
                )
                print("✅ Database indexes created")
            except Exception as e:
                print(f"⚠️  Note: Couldn't create index: {e}")

        print("✅ Flask app initialized successfully")
        print("\n🚀 Starting server on http://localhost:5001")
        print("   Press Ctrl+C to stop")

        # Run on port 5001 to avoid conflicts
        app.run(host="0.0.0.0", port=5001, debug=False)

    except Exception as e:
        print(f"⚠️  Error starting application: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

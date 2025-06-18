#!/usr/bin/env python3
"""
Database initialization script for PHRM.
Creates all necessary tables and indexes for first-time setup.
"""

import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv

    env_file = os.path.join(project_root, ".env.production")
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
except ImportError:
    print("⚠️  python-dotenv not installed, using environment as-is")

# Import the Flask app and models
from app import create_app
from app.models import db
from app.models.core.medical_condition import MedicalCondition


def init_db():
    """Initialize the database with all required tables"""
    print("🗄️  Initializing database...")

    # Create Flask app context
    app = create_app()

    # Print database URI for troubleshooting
    db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    print(f"💾 Using database: {db_uri}")

    with app.app_context():
        # Create all tables
        db.create_all()

        # Verify MedicalCondition table specifically
        try:
            MedicalCondition.__table__.create(db.engine, checkfirst=True)
            print("✅ Verified MedicalCondition table exists")
        except Exception as e:
            print(f"⚠️  Note on MedicalCondition table: {e}")

        # Create any required indexes
        try:
            from sqlalchemy import text

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_medical_conditions_user
                ON medical_conditions (user_id, current_status);
            """
                )
            )
            print("✅ Created index on medical_condition table")
        except Exception as e:
            print(f"⚠️  Note: Could not create index: {e}")
            print("   This is normal if the table doesn't exist yet")

        # Commit changes
        db.session.commit()
        print("✅ Database schema created successfully")

        # Verify tables exist using SQLAlchemy 2.0+ compatible method
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"📊 Database has {len(tables)} tables:")
        for table in tables:
            print(f"   - {table}")


if __name__ == "__main__":
    init_db()
    print("\n✅ Database initialization complete!")

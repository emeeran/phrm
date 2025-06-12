"""
Personal Health Record Manager
-----------------------------
Main entry point for the application.
"""

import os

from dotenv import load_dotenv

from app import create_app, db
from app.models import AISummary, Document, FamilyMember, HealthRecord, User

# Load environment variables from .env file if present
load_dotenv()

# Check for Hugging Face API key (Primary for MedGemma)
if not os.getenv('HUGGINGFACE_ACCESS_TOKEN'):
    print("⚠️ Hugging Face Access Token is not configured.")
    print("   MedGemma (primary AI) will not be available via Inference API.")
    print("   The application will attempt to use local MedGemma or fallback to GROQ/DEEPSEEK.")
else:
    print("✅ Hugging Face Access Token configured.")

# Check for GROQ API key (Secondary)
if not os.getenv('GROQ_API_KEY'):
    print("⚠️ GROQ API key is not configured.")
    print("   GROQ (secondary AI) will not be available.")
else:
    print("✅ GROQ API key configured.")

# Check for DEEPSEEK API key (Fallback)
if not os.getenv('DEEPSEEK_API_KEY'):
    print("⚠️ DEEPSEEK API key is not configured.")
    print("   DEEPSEEK (fallback AI) will not be available.")
else:
    print("✅ DEEPSEEK API key configured.")

# Ensure at least one fallback is configured if Hugging Face is not
if not os.getenv('HUGGINGFACE_ACCESS_TOKEN') and not os.getenv('GROQ_API_KEY') and not os.getenv('DEEPSEEK_API_KEY'):
    print("❌ CRITICAL: No AI providers are configured. AI features will not work.")
elif not os.getenv('HUGGINGFACE_ACCESS_TOKEN') and (not os.getenv('GROQ_API_KEY') or not os.getenv('DEEPSEEK_API_KEY')):
    print("⚠️ WARNING: Primary AI (MedGemma via Hugging Face) is not configured, and one or more fallback AIs are also not configured.")
    print("   AI functionality might be limited or unavailable.")

# Create Flask application instance
app = create_app()

# Create an application context for shell commands
@app.shell_context_processor
def make_shell_context():
    """Make shell context for Flask shell commands"""
    return {
        'db': db,
        'User': User,
        'FamilyMember': FamilyMember,
        'HealthRecord': HealthRecord,
        'Document': Document,
        'AISummary': AISummary
    }

# Custom Jinja2 filter to format dates and other template helpers

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Run the Personal Health Record Manager')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the application on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the application on')
    args = parser.parse_args()

    # Create the upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Check if database exists, if not create tables
    with app.app_context():
        if not os.path.exists(os.path.join(os.path.dirname(__file__), 'app', 'phrm.db')):
            db.create_all()
            print("Database tables created.")

    # Run the application
    app.run(host=args.host, port=args.port, debug=True)

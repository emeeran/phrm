"""
Personal Health Record Manager
-----------------------------
Main entry point for the application.
"""

import os
import sys
import requests
from dotenv import load_dotenv
from app import create_app, db
from app.models import User, FamilyMember, HealthRecord, Document, AISummary

# Load environment variables from .env file if present
load_dotenv()

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

# Check if Gemini API is configured
def check_gemini_configuration():
    """Check if Gemini API is properly configured"""
    gemini_api_key = app.config.get('GEMINI_API_KEY')
    gemini_model = app.config.get('GEMINI_MODEL', 'gemini-1.5-pro')
    
    if not gemini_api_key:
        print("⚠️ Gemini API key is not configured")
        print("   AI features will fall back to OpenAI if configured.")
        return False
    
    try:
        # Import here to avoid circular imports
        import google.generativeai as genai
        genai.configure(api_key=gemini_api_key)
        print(f"✅ Gemini API configured successfully")
        print(f"   Using model: {gemini_model}")
        return True
    except ImportError:
        print("⚠️ Google Generative AI package not installed")
        print("   Run: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"⚠️ Error configuring Gemini API: {e}")
        return False

# Try to check Gemini configuration on startup
check_gemini_configuration()

# Custom Jinja2 filter to format dates and other template helpers

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run the Personal Health Record Manager')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the application on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the application on')
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port, debug=True)
@app.template_filter('format_date')
def format_date_filter(date):
    """Format a date object to a readable string"""
    if date:
        return date.strftime('%B %d, %Y')
    return ''

if __name__ == '__main__':
    # Create the upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Check if database exists, if not create tables
    with app.app_context():
        if not os.path.exists(os.path.join(os.path.dirname(__file__), 'app', 'phrm.db')):
            db.create_all()
            print("Database tables created.")

    # Run the application
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
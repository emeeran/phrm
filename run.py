"""
Personal Health Record Manager
-----------------------------
Main entry point for the application.
"""

import os
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

# Custom Jinja2 filter to format dates and other template helpers
@app.template_filter('format_date')
def format_date_filter(date):
    """Format a date object to a readable string"""
    if date:
        return date.strftime('%B %d, %Y')
    return ''

@app.context_processor
def utility_processor():
    """Add utility functions to Jinja2 context"""
    def get_record_badge_class(record_type):
        """Get the appropriate badge class for a record type"""
        badge_classes = {
            'complaint': 'bg-danger',
            'doctor_visit': 'bg-primary',
            'investigation': 'bg-purple',
            'prescription': 'bg-success',
            'lab_report': 'bg-warning',
            'note': 'bg-secondary'
        }
        return badge_classes.get(record_type, 'bg-info')

    def get_record_icon(record_type):
        """Get the appropriate icon for a record type"""
        icons = {
            'complaint': 'fa-face-frown',
            'doctor_visit': 'fa-user-doctor',
            'investigation': 'fa-microscope',
            'prescription': 'fa-prescription',
            'lab_report': 'fa-flask',
            'note': 'fa-clipboard'
        }
        return icons.get(record_type, 'fa-file-medical')

    # Add current date to templates (for the footer)
    from datetime import datetime
    now = datetime.now()

    return dict(
        get_record_badge_class=get_record_badge_class,
        get_record_icon=get_record_icon,
        now=now
    )

if __name__ == '__main__':
    # Create the upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Check if database exists, if not create tables
    with app.app_context():
        if not os.path.exists(os.path.join(os.path.dirname(__file__), 'app', 'phrm.db')):
            db.create_all()
            print("Database tables created.")

    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)
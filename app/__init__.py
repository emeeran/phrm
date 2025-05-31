from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from .config import get_config
from .models import db, User
import os

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_name=None):
    """Application factory function"""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(get_config())

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    from .auth import auth_bp
    app.register_blueprint(auth_bp)

    from .records import records_bp
    app.register_blueprint(records_bp)

    from .ai import ai_bp
    app.register_blueprint(ai_bp)

    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # Inject utility functions into all templates
    from datetime import datetime
    @app.context_processor
    def inject_utilities():
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

        def calculate_age(birth_date):
            """Calculate age in years from a birth date"""
            if birth_date is None:
                return None
            
            today = datetime.now().date()
            # Convert birth_date to date if it's a datetime object
            if hasattr(birth_date, 'date'):
                birth_date = birth_date.date()
            
            # Calculate age
            age = today.year - birth_date.year
            # Adjust if birthday hasn't occurred this year
            if today < birth_date.replace(year=today.year):
                age -= 1
            
            return age

        return {
            'now': datetime.now(),
            'get_record_badge_class': get_record_badge_class,
            'get_record_icon': get_record_icon,
            'calculate_age': calculate_age
        }

    # Register custom Jinja2 filters
    def format_date(value, format='%b %d, %Y'):
        if value is None:
            return ''
        return value.strftime(format)
    app.jinja_env.filters['format_date'] = format_date

    def nl2br(value):
        if value is None:
            return ''
        return value.replace('\n', '<br>')
    app.jinja_env.filters['nl2br'] = nl2br

    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()  # Roll back session in case of database error
        return render_template('errors/500.html'), 500

    # Add a route for the root URL
    @app.route('/')
    def index():
        from flask_login import current_user
        from flask import redirect, url_for
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return render_template('index.html')

    return app
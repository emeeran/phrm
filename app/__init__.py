from flask import Flask, render_template, request, g
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_caching import Cache
from flask_talisman import Talisman
from .config import get_config
from .models import db, User
# from .utils.database_optimizer import DatabaseOptimizer, QueryOptimizer
# from .utils.redis_config import RedisConfig, get_user_id
# from .utils.config_manager import config_manager
# from .utils.ai_config_integration import initialize_ai_configuration
import os
import time
import click

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

migrate = Migrate()
# Configure limiter with Redis storage if available
# redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
# try:
#     # Test Redis connection
#     import redis
#     r = redis.from_url(redis_url, decode_responses=True)
#     r.ping()
#     limiter = Limiter(key_func=get_user_id, storage_uri=redis_url)
# except:
#     # Fallback to in-memory storage
#     limiter = Limiter(key_func=get_user_id)

# Simple in-memory limiter without Redis dependency
from flask_limiter.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)

cache = Cache()
talisman = Talisman()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_name=None):
    """Application factory function"""
    app = Flask(__name__)

    # Initialize AI configuration integration
    # initialize_ai_configuration()

    # Validate configuration using the configuration manager
    # validation_result = config_manager.validate_configuration()
    # if not validation_result['valid']:
    #     # Log configuration issues
    #     print("⚠️ Configuration validation issues detected:")
    #     for error in validation_result.get('missing_required', []):
    #         print(f"  Missing required: {error['key']} - {error['description']}")
    #     for error in validation_result.get('invalid_values', []):
    #         print(f"  Invalid value: {error['key']} - {error.get('reason', 'Invalid format')}")
    #     for issue in validation_result.get('security_issues', []):
    #         print(f"  Security issue: {issue['key']} - {issue['issue']}")
    #     
    #     # Only fail fast in production for critical issues
    #     if config_manager.environment.value == 'production' and validation_result.get('missing_required'):
    #         raise ValueError("Critical configuration missing in production environment")

    # Load configuration
    app.config.from_object(get_config())
    
    # Configure Redis-based caching
    # cache_config = RedisConfig.get_cache_config()
    # app.config.update(cache_config)
    
    # Store application start time for metrics
    app.start_time = time.time()

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize security extensions
    limiter.init_app(app)
    cache.init_app(app)
    
    # Configure Talisman for security headers (only in production)
    if not app.config.get('DEBUG'):
        talisman.init_app(app, 
            force_https=app.config.get('SESSION_COOKIE_SECURE', False),
            strict_transport_security=True,
            content_security_policy={
                'default-src': "'self'",
                'script-src': "'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net cdnjs.cloudflare.com",
                'style-src': "'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com fonts.googleapis.com",
                'font-src': "'self' fonts.gstatic.com",
                'img-src': "'self' data:",
                'connect-src': "'self'"
            }
        )

    # Set up logging and monitoring
    # from .utils.logging_config import setup_logging
    # from .utils.performance import setup_performance_monitoring
    # from .utils.security import rate_limit_exceeded_handler
    
    # setup_logging(app)
    # setup_performance_monitoring(app, db)
    
    # Register rate limit error handler
    # app.register_error_handler(429, rate_limit_exceeded_handler)

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
    
    # Register operations dashboard blueprint
    from .ops import ops_bp
    app.register_blueprint(ops_bp)
    
    # Register health check blueprint
    # from .health import health_bp
    # app.register_blueprint(health_bp)

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

    # Apply database optimizations
    if app.config.get('ENABLE_DATABASE_OPTIMIZATION', False):
        def initialize_database():
            # Create optimized indexes
            # DatabaseOptimizer.create_indexes(db)
            # Analyze database for optimization
            # DatabaseOptimizer.analyze_database(db)
            pass
        app.before_request(initialize_database)

    # Register CLI commands for admin management
    @app.cli.command()
    @click.option('--email', prompt=True, help='Admin user email address')
    @click.option('--username', prompt=True, help='Admin username')
    @click.option('--first-name', prompt=True, help='Admin first name')
    @click.option('--last-name', prompt=True, help='Admin last name')
    def create_admin(email, username, first_name, last_name):
        """Create a new admin user"""
        import getpass
        from .utils.security import log_security_event
        
        try:
            # Check if user already exists
            existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
            if existing_user:
                click.echo(f"❌ User with email '{email}' or username '{username}' already exists!")
                return
            
            # Get password securely
            password = getpass.getpass("Enter password for admin user: ")
            password_confirm = getpass.getpass("Confirm password: ")
            
            if password != password_confirm:
                click.echo("❌ Passwords do not match!")
                return
            
            if len(password) < 8:
                click.echo("❌ Password must be at least 8 characters long!")
                return
            
            # Create admin user
            admin_user = User(
                email=email.lower().strip(),
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_admin=True  # Set admin flag
            )
            admin_user.set_password(password)
            
            db.session.add(admin_user)
            db.session.commit()
            
            # Log admin creation
            log_security_event('admin_user_created', {
                'admin_user_id': admin_user.id,
                'admin_email': admin_user.email,
                'admin_username': admin_user.username
            })
            
            click.echo(f"✅ Admin user '{username}' created successfully!")
            click.echo(f"📧 Email: {email}")
            click.echo(f"👤 Name: {first_name} {last_name}")
            click.echo(f"🔑 Admin privileges: Enabled")
            
        except Exception as e:
            db.session.rollback()
            click.echo(f"❌ Error creating admin user: {e}")

    @app.cli.command()
    @click.option('--email', prompt=True, help='User email address to promote to admin')
    def promote_to_admin(email):
        """Promote an existing user to admin"""
        from .utils.security import log_security_event
        
        try:
            user = User.query.filter_by(email=email.lower().strip()).first()
            if not user:
                click.echo(f"❌ User with email '{email}' not found!")
                return
            
            if user.is_admin:
                click.echo(f"ℹ️  User '{user.username}' is already an admin!")
                return
            
            # Confirm promotion
            click.echo(f"👤 Found user: {user.first_name} {user.last_name} ({user.username})")
            if not click.confirm("Are you sure you want to promote this user to admin?"):
                click.echo("Operation cancelled.")
                return
            
            user.is_admin = True
            db.session.commit()
            
            # Log admin promotion
            log_security_event('user_promoted_to_admin', {
                'promoted_user_id': user.id,
                'promoted_email': user.email,
                'promoted_username': user.username
            })
            
            click.echo(f"✅ User '{user.username}' has been promoted to admin!")
            
        except Exception as e:
            db.session.rollback()
            click.echo(f"❌ Error promoting user to admin: {e}")

    @app.cli.command()
    def list_admins():
        """List all admin users"""
        try:
            admin_users = User.query.filter_by(is_admin=True).all()
            
            if not admin_users:
                click.echo("ℹ️  No admin users found.")
                return
            
            click.echo(f"👥 Found {len(admin_users)} admin user(s):")
            click.echo("-" * 80)
            
            for admin in admin_users:
                click.echo(f"📧 {admin.email}")
                click.echo(f"👤 {admin.first_name} {admin.last_name} ({admin.username})")
                click.echo(f"📅 Created: {admin.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                click.echo(f"🔐 Active: {'Yes' if admin.is_active else 'No'}")
                click.echo("-" * 80)
            
        except Exception as e:
            click.echo(f"❌ Error listing admin users: {e}")

    return app
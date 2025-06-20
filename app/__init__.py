import os
import time

import click
from flask import Flask, jsonify, render_template
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_talisman import Talisman

from .models import User, db
from .utils.config_manager import get_config
from .utils.redis_cache import cache as redis_cache

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

migrate = Migrate()


def get_limiter_key():
    """Get key for rate limiting - user ID if authenticated, otherwise IP"""
    from flask_login import current_user

    if current_user and current_user.is_authenticated:
        return f"user:{current_user.id}"
    return get_remote_address()


# Try to use Redis for rate limiting, fallback to in-memory
redis_available = False
try:
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    import redis

    r = redis.from_url(redis_url, decode_responses=True)
    r.ping()
    limiter = Limiter(
        key_func=get_limiter_key,
        storage_uri=redis_url,
        default_limits=["100 per hour", "20 per minute"],
    )
    redis_available = True
    print("✅ Redis connected successfully for rate limiting")
except Exception as e:
    # Fallback to in-memory storage with explicit configuration
    limiter = Limiter(
        key_func=get_limiter_key,
        storage_uri="memory://",  # Explicitly specify in-memory storage
        default_limits=["100 per hour", "20 per minute"],
    )
    print(f"⚠️ Redis unavailable, using in-memory rate limiting: {e}")
    print("   This is acceptable for development but not recommended for production.")

cache = Cache()
talisman = Talisman()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def _configure_app(app):
    """Configure application settings and security"""
    # Load configuration
    app.config.from_object(get_config())

    # Store application start time for metrics
    app.start_time = time.time()

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def _initialize_extensions(app):
    """Initialize Flask extensions"""
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Initialize Redis cache
    redis_cache.init_app(app)

    # Initialize security extensions
    limiter.init_app(app)
    cache.init_app(app)

    # Initialize RAG service for medical reference books (temporarily disabled for troubleshooting)
    # with app.app_context():
    #     try:
    #         from .utils.local_rag import initialize_rag
    #         initialize_rag()
    #     except Exception as e:
    #         app.logger.error(f"Failed to initialize RAG service: {e}")
    #         app.logger.info("Application will continue without RAG functionality")


def _configure_security(app):
    """Configure security settings including Talisman"""
    # Configure Talisman for security headers (only in production)
    if not app.config.get("DEBUG"):
        talisman.init_app(
            app,
            force_https=app.config.get("SESSION_COOKIE_SECURE", False),
            strict_transport_security=True,
            content_security_policy={
                "default-src": "'self'",
                "script-src": "'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net cdnjs.cloudflare.com",
                "style-src": "'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com fonts.googleapis.com",
                "font-src": "'self' fonts.gstatic.com",
                "img-src": "'self' data:",
                "connect-src": "'self'",
            },
        )


def _register_blueprints(app):
    """Register application blueprints"""
    from .auth import auth_bp

    app.register_blueprint(auth_bp)

    from .records import records_bp

    app.register_blueprint(records_bp)

    from .appointments import appointments_bp

    app.register_blueprint(appointments_bp)

    from .ai import ai_bp

    app.register_blueprint(ai_bp)

    from .api import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    from .ops import ops_bp

    app.register_blueprint(ops_bp)


def _configure_templates(app):
    """Configure template utilities and filters"""
    from .utils.template_utils import get_template_filters, get_template_utilities

    @app.context_processor
    def inject_utilities():
        return get_template_utilities()

    # Register custom Jinja2 filters
    template_filters = get_template_filters()
    for filter_name, filter_func in template_filters.items():
        app.jinja_env.filters[filter_name] = filter_func


def _register_error_handlers(app):
    """Register application error handlers"""

    @app.errorhandler(404)
    def page_not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()  # Roll back session in case of database error
        return render_template("errors/500.html"), 500


def _add_main_routes(app):
    """Add main application routes"""

    @app.route("/")
    def index():
        from flask import redirect, url_for
        from flask_login import current_user

        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        return render_template("index.html")


def _configure_database_optimization(app):
    """Configure database optimization if enabled"""
    if app.config.get("ENABLE_DATABASE_OPTIMIZATION", False):

        def initialize_database():
            # Create optimized indexes
            # DatabaseOptimizer.create_indexes(db)
            # Analyze database for optimization
            # DatabaseOptimizer.analyze_database(db)
            pass

        app.before_request(initialize_database)


def _register_cli_commands(app):
    """Register CLI commands for admin management"""

    @app.cli.command()
    @click.option("--email", prompt=True, help="Admin user email address")
    @click.option("--username", prompt=True, help="Admin username")
    @click.option("--first-name", prompt=True, help="Admin first name")
    @click.option("--last-name", prompt=True, help="Admin last name")
    def create_admin(email, username, first_name, last_name):
        """Create a new admin user"""
        _create_admin_user(email, username, first_name, last_name)

    @app.cli.command()
    @click.option("--email", prompt=True, help="User email address to promote to admin")
    def promote_to_admin(email):
        """Promote an existing user to admin"""
        _promote_user_to_admin(email)

    @app.cli.command()
    def list_admins():
        """List all admin users"""
        _list_admin_users()


def _create_admin_user(email, username, first_name, last_name):
    """Helper function to create admin user"""
    import getpass

    from .utils.shared import log_security_event

    try:
        # Check if user already exists
        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()
        if existing_user:
            click.echo(
                f"❌ User with email '{email}' or username '{username}' already exists!"
            )
            return

        # Get password securely
        password = getpass.getpass("Enter password for admin user: ")
        password_confirm = getpass.getpass("Confirm password: ")

        if password != password_confirm:
            click.echo("❌ Passwords do not match!")
            return

        # Password validation
        MIN_PASSWORD_LENGTH = 8
        if len(password) < MIN_PASSWORD_LENGTH:
            click.echo("❌ Password must be at least 8 characters long!")
            return

        # Create admin user
        admin_user = User(
            email=email.lower().strip(),
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_admin=True,  # Set admin flag
        )
        admin_user.set_password(password)

        db.session.add(admin_user)
        db.session.commit()

        # Log admin creation
        log_security_event(
            "admin_user_created",
            {
                "admin_user_id": admin_user.id,
                "admin_email": admin_user.email,
                "admin_username": admin_user.username,
            },
        )

        click.echo(f"✅ Admin user '{username}' created successfully!")
        click.echo(f"📧 Email: {email}")
        click.echo(f"👤 Name: {first_name} {last_name}")
        click.echo("🔑 Admin privileges: Enabled")

    except Exception as e:
        db.session.rollback()
        click.echo(f"❌ Error creating admin user: {e}")


def _promote_user_to_admin(email):
    """Helper function to promote user to admin"""
    from .utils.shared import log_security_event

    try:
        user = User.query.filter_by(email=email.lower().strip()).first()
        if not user:
            click.echo(f"❌ User with email '{email}' not found!")
            return

        if user.is_admin:
            click.echo(f"INFO: User '{user.username}' is already an admin!")
            return

        # Confirm promotion
        click.echo(
            f"👤 Found user: {user.first_name} {user.last_name} ({user.username})"
        )
        if not click.confirm("Are you sure you want to promote this user to admin?"):
            click.echo("Operation cancelled.")
            return

        user.is_admin = True
        db.session.commit()

        # Log admin promotion
        log_security_event(
            "user_promoted_to_admin",
            {
                "promoted_user_id": user.id,
                "promoted_email": user.email,
                "promoted_username": user.username,
            },
        )

        click.echo(f"✅ User '{user.username}' has been promoted to admin!")

    except Exception as e:
        db.session.rollback()
        click.echo(f"❌ Error promoting user to admin: {e}")


def _list_admin_users():
    """Helper function to list admin users"""
    try:
        admin_users = User.query.filter_by(is_admin=True).all()

        if not admin_users:
            click.echo("INFO: No admin users found.")
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


def _add_health_check_routes(app):
    """Add health check endpoints"""

    @app.route("/health")
    def health_check():
        """Main health check endpoint"""
        try:
            # Check database connectivity
            from sqlalchemy import text

            db.session.execute(text("SELECT 1"))
            db_healthy = True
        except Exception:
            db_healthy = False

        return jsonify(
            {
                "status": "healthy" if db_healthy else "unhealthy",
                "database": "connected" if db_healthy else "disconnected",
                "uptime": time.time() - app.start_time,
            }
        )


def create_app(_config_name=None):
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

    # Configure Redis-based caching
    # cache_config = RedisConfig.get_cache_config()
    # app.config.update(cache_config)

    # Set up application components
    _configure_app(app)
    _initialize_extensions(app)
    _configure_security(app)
    _register_blueprints(app)
    _configure_templates(app)
    _register_error_handlers(app)
    _add_main_routes(app)
    _configure_database_optimization(app)
    _register_cli_commands(app)
    _add_health_check_routes(app)

    return app

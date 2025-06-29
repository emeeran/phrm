"""
Optimized Template Utilities for PHRM
Consolidated template functions and filters with enhanced performance
"""

from datetime import date, datetime
from typing import Any, Optional

from flask import current_app
from markupsafe import Markup


# ============================================================================
# CORE TEMPLATE FUNCTIONS
# ============================================================================

def get_record_badge_class(record_type: str) -> str:
    """Get the appropriate badge class for a record type"""
    badge_mapping = {
        'complaint': 'bg-primary',
        'diagnosis': 'bg-success', 
        'prescription': 'bg-info',
        'symptom': 'bg-warning',
        'treatment': 'bg-secondary',
        'followup': 'bg-light text-dark',
        'emergency': 'bg-danger',
        'routine': 'bg-success',
        'appointment': 'bg-info'
    }
    return badge_mapping.get(record_type.lower(), 'bg-secondary')


def get_record_icon(record_type: str) -> str:
    """Get the appropriate icon for a record type"""
    icon_mapping = {
        'complaint': 'fas fa-exclamation-circle',
        'diagnosis': 'fas fa-stethoscope',
        'prescription': 'fas fa-pills',
        'symptom': 'fas fa-thermometer-half',
        'treatment': 'fas fa-user-md',
        'followup': 'fas fa-calendar-check',
        'emergency': 'fas fa-ambulance',
        'routine': 'fas fa-heartbeat',
        'appointment': 'fas fa-calendar-alt',
        'document': 'fas fa-file-medical',
        'lab': 'fas fa-vial',
        'imaging': 'fas fa-x-ray'
    }
    return icon_mapping.get(record_type.lower(), 'fas fa-file-medical')


def calculate_age(birth_date: Any) -> Optional[int]:
    """Calculate age in years from a birth date"""
    if not birth_date:
        return None
    
    try:
        if isinstance(birth_date, str):
            birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
        elif isinstance(birth_date, datetime):
            birth_date = birth_date.date()
        elif not isinstance(birth_date, date):
            return None
            
        today = date.today()
        age = today.year - birth_date.year
        
        # Adjust if birthday hasn't occurred this year
        if today < birth_date.replace(year=today.year):
            age -= 1
            
        return max(0, age)  # Ensure non-negative age
        
    except (ValueError, TypeError, AttributeError):
        return None


def format_date(value: Any, format_str: str = "%b %d, %Y") -> str:
    """Format date for display with fallback handling"""
    if not value:
        return ""
    
    try:
        if isinstance(value, str):
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    value = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue
            else:
                return value  # Return original string if no format matches
        
        if isinstance(value, datetime):
            return value.strftime(format_str)
        elif isinstance(value, date):
            return value.strftime(format_str)
        else:
            return str(value)
            
    except (ValueError, AttributeError):
        return str(value) if value else ""


def format_datetime(value: Any, format_str: str = "%b %d, %Y at %I:%M %p") -> str:
    """Format datetime for display"""
    return format_date(value, format_str)


def format_time(value: Any, format_str: str = "%I:%M %p") -> str:
    """Format time for display"""
    if not value:
        return ""
    
    try:
        if isinstance(value, str):
            # Try to parse time string
            try:
                value = datetime.strptime(value, '%H:%M:%S').time()
            except ValueError:
                try:
                    value = datetime.strptime(value, '%H:%M').time()
                except ValueError:
                    return value
        
        if hasattr(value, 'strftime'):
            return value.strftime(format_str)
        else:
            return str(value)
            
    except (ValueError, AttributeError):
        return str(value) if value else ""


def nl2br(value: Optional[str]) -> str:
    """Convert newlines to HTML line breaks"""
    if not value:
        return ""
    
    # Escape HTML first, then convert newlines
    from markupsafe import escape
    escaped = escape(value)
    return Markup(str(escaped).replace('\n', '<br>\n'))


def truncate_text(text: str, length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix"""
    if not text:
        return ""
    
    if len(text) <= length:
        return text
    
    return text[:length - len(suffix)].rstrip() + suffix


def pluralize(count: int, singular: str, plural: str = None) -> str:
    """Return plural form based on count"""
    if plural is None:
        plural = singular + 's'
    
    return singular if count == 1 else plural


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"


def get_status_badge(status: str) -> str:
    """Get appropriate badge class for status"""
    status_mapping = {
        'active': 'bg-success',
        'inactive': 'bg-secondary',
        'pending': 'bg-warning',
        'completed': 'bg-primary',
        'cancelled': 'bg-danger',
        'draft': 'bg-info',
        'archived': 'bg-dark'
    }
    return status_mapping.get(status.lower(), 'bg-secondary')


def get_priority_badge(priority: str) -> str:
    """Get appropriate badge class for priority"""
    priority_mapping = {
        'high': 'bg-danger',
        'medium': 'bg-warning', 
        'low': 'bg-success',
        'urgent': 'bg-danger',
        'normal': 'bg-primary'
    }
    return priority_mapping.get(priority.lower(), 'bg-secondary')


# ============================================================================
# ENHANCED UTILITY FUNCTIONS
# ============================================================================

def smart_join(items: list, separator: str = ", ", last_separator: str = " and ") -> str:
    """Join items with smart conjunction"""
    if not items:
        return ""
    
    items = [str(item) for item in items if item]
    
    if len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return last_separator.join(items)
    else:
        return separator.join(items[:-1]) + last_separator + items[-1]


def format_list(items: list, format_func=None) -> str:
    """Format a list with optional formatting function"""
    if not items:
        return ""
    
    if format_func:
        items = [format_func(item) for item in items]
    
    return smart_join(items)


def relative_time(dt: datetime) -> str:
    """Get relative time description (e.g., '2 hours ago')"""
    if not dt:
        return ""
    
    try:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            if diff.days == 1:
                return "yesterday"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            elif diff.days < 30:
                weeks = diff.days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            else:
                months = diff.days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
        
        seconds = diff.seconds
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
            
    except (ValueError, TypeError, AttributeError):
        return str(dt) if dt else ""


def format_currency(amount: float, currency: str = "$") -> str:
    """Format currency amount"""
    if amount is None:
        return ""
    
    try:
        return f"{currency}{amount:,.2f}"
    except (ValueError, TypeError):
        return str(amount)


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format percentage value"""
    if value is None:
        return ""
    
    try:
        return f"{value:.{decimals}f}%"
    except (ValueError, TypeError):
        return str(value)


# ============================================================================
# TEMPLATE FILTERS REGISTRATION
# ============================================================================

def register_template_filters(app):
    """Register all template filters with the Flask app"""
    
    filters = {
        'record_badge': get_record_badge_class,
        'record_icon': get_record_icon,
        'age': calculate_age,
        'date': format_date,
        'datetime': format_datetime,
        'time': format_time,
        'nl2br': nl2br,
        'truncate': truncate_text,
        'pluralize': pluralize,
        'filesize': format_file_size,
        'status_badge': get_status_badge,
        'priority_badge': get_priority_badge,
        'smart_join': smart_join,
        'format_list': format_list,
        'relative_time': relative_time,
        'currency': format_currency,
        'percentage': format_percentage,
        'format_date': format_date  # <-- Added this line
    }
    
    for name, func in filters.items():
        app.jinja_env.filters[name] = func
    
    # Add global functions
    globals_dict = {
        'get_record_badge_class': get_record_badge_class,
        'get_record_icon': get_record_icon,
        'calculate_age': calculate_age,
        'format_date': format_date,
        'nl2br': nl2br
    }
    
    app.jinja_env.globals.update(globals_dict)
    
    app.logger.info("Template filters and globals registered successfully")


# ============================================================================
# JINJA2 ENVIRONMENT OPTIMIZATIONS
# ============================================================================

def optimize_jinja_environment(app):
    """Optimize Jinja2 environment for better performance"""
    
    # Enable auto-reload only in debug mode
    app.jinja_env.auto_reload = app.debug
    
    # Cache compiled templates
    app.jinja_env.cache_size = 400 if not app.debug else 0
    
    # Enable optimizations
    app.jinja_env.optimized = not app.debug
    
    # Custom undefined class for better error handling
    from jinja2 import DebugUndefined, Undefined
    app.jinja_env.undefined = DebugUndefined if app.debug else Undefined
    
    # Enable automatic HTML escaping
    app.jinja_env.autoescape = True
    
    app.logger.info("Jinja2 environment optimized")


# ============================================================================
# TEMPLATE CONTEXT PROCESSORS
# ============================================================================

def register_context_processors(app):
    """Register template context processors"""
    
    @app.context_processor
    def inject_globals():
        """Inject global variables into all templates"""
        from datetime import datetime
        now = datetime.now()
        return {
            'app_name': app.config.get('APP_NAME', 'PHRM'),
            'app_version': app.config.get('APP_VERSION', '1.0.0'),
            'current_year': now.year,
            'now': now,  # Add the now variable that templates expect
            'debug': app.debug
        }
    
    @app.context_processor
    def utility_functions():
        """Inject utility functions into templates"""
        return {
            'enumerate': enumerate,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'zip': zip,
            'min': min,
            'max': max,
            'sum': sum,
            'sorted': sorted,
            'reversed': reversed
        }
    
    app.logger.info("Template context processors registered")


# ============================================================================
# INITIALIZATION FUNCTION
# ============================================================================

def init_template_system(app):
    """Initialize the complete template system"""
    register_template_filters(app)
    register_context_processors(app)
    optimize_jinja_environment(app)
    
    app.logger.info("✅ Template system initialized successfully")

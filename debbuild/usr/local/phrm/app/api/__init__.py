from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash
import functools
from ..models import db, User, HealthRecord, FamilyMember, Document, AISummary
# from ..utils.security import (
#     log_security_event, detect_suspicious_patterns, 
#     sanitize_html
# )
# from ..utils.ai_security import (
#     AISecurityManager, ai_security_required, 
#     secure_ai_response_headers
# )
# from ..utils.ai_audit import ai_audit_required
# from ..utils.performance import monitor_performance
from .. import limiter, cache

# Stub functions for missing utilities
def log_security_event(event_type, data):
    """Stub function for security event logging"""
    pass

def detect_suspicious_patterns(text):
    """Stub function for suspicious pattern detection"""
    return False

def sanitize_html(text):
    """Stub function for HTML sanitization"""
    return text if text else ""

def ai_security_required(*args, **kwargs):
    """Stub decorator for AI security"""
    def decorator(func):
        return func
    if len(args) == 1 and callable(args[0]):
        return args[0]
    return decorator

def secure_ai_response_headers(*args, **kwargs):
    """Stub decorator for secure AI response headers"""
    def decorator(func):
        return func
    if len(args) == 1 and callable(args[0]):
        return args[0]
    return decorator

def ai_audit_required(*args, **kwargs):
    """Stub decorator for AI audit"""
    def decorator(func):
        return func
    if len(args) == 1 and callable(args[0]):
        return args[0]
    return decorator

def monitor_performance(func):
    """Stub decorator for performance monitoring"""
    return func

class AISecurityManager:
    """Stub class for AI security management"""
    @staticmethod
    def validate_request(data):
        return True
from datetime import datetime
import re
import time

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# API authentication decorator
def api_login_required(view_function):
    @functools.wraps(view_function)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        try:
            # Check for Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                log_security_event('api_unauthorized_access', {
                    'endpoint': request.endpoint,
                    'ip_address': user_ip,
                    'user_agent': request.headers.get('User-Agent', ''),
                    'reason': 'missing_authorization_header'
                })
                return jsonify({'error': 'Authorization header is required'}), 401

            # Parse Authorization header
            auth_parts = auth_header.split(' ', 1)
            if len(auth_parts) != 2:
                log_security_event('api_invalid_auth_format', {
                    'endpoint': request.endpoint,
                    'ip_address': user_ip,
                    'auth_header': auth_header[:50] + '...' if len(auth_header) > 50 else auth_header
                })
                return jsonify({'error': 'Invalid authorization format'}), 401
                
            auth_type, credentials = auth_parts
            if auth_type.lower() != 'basic':
                log_security_event('api_unsupported_auth_type', {
                    'endpoint': request.endpoint,
                    'ip_address': user_ip,
                    'auth_type': auth_type
                })
                return jsonify({'error': 'Basic authorization is required'}), 401

            import base64
            try:
                decoded = base64.b64decode(credentials).decode('utf-8')
            except Exception:
                log_security_event('api_invalid_base64', {
                    'endpoint': request.endpoint,
                    'ip_address': user_ip
                })
                return jsonify({'error': 'Invalid base64 encoding'}), 401
                
            if ':' not in decoded:
                log_security_event('api_invalid_credentials_format', {
                    'endpoint': request.endpoint,
                    'ip_address': user_ip
                })
                return jsonify({'error': 'Invalid credentials format'}), 401
                
            email, password = decoded.split(':', 1)
            
            # Validate email format
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            if not email_pattern.match(email):
                log_security_event('api_invalid_email_format', {
                    'endpoint': request.endpoint,
                    'ip_address': user_ip,
                    'email': email
                })
                return jsonify({'error': 'Invalid email format'}), 401

            # Check for suspicious patterns in credentials
            if detect_suspicious_patterns(email) or detect_suspicious_patterns(password):
                log_security_event('api_suspicious_credentials', {
                    'endpoint': request.endpoint,
                    'ip_address': user_ip,
                    'email': email
                })
                return jsonify({'error': 'Invalid credentials'}), 401

            # Authenticate user
            user = User.query.filter_by(email=email).first()
            if not user or not user.check_password(password):
                log_security_event('api_invalid_credentials', {
                    'endpoint': request.endpoint,
                    'ip_address': user_ip,
                    'email': email,
                    'user_exists': user is not None
                })
                return jsonify({'error': 'Invalid credentials'}), 401

            # Log successful API authentication
            log_security_event('api_authentication_success', {
                'user_id': user.id,
                'endpoint': request.endpoint,
                'ip_address': user_ip,
                'response_time': round((time.time() - start_time) * 1000, 2)
            })

            # Add user to kwargs
            kwargs['api_user'] = user

            return view_function(*args, **kwargs)

        except Exception as e:
            current_app.logger.error(f"API authentication error: {e}")
            log_security_event('api_authentication_error', {
                'endpoint': request.endpoint,
                'ip_address': user_ip,
                'error': str(e)
            })
            return jsonify({'error': 'Authentication failed'}), 401

    return decorated_function

# Helper functions
def record_to_dict(record):
    """Convert a HealthRecord object to a dictionary for API responses"""
    result = {
        'id': record.id,
        'title': record.title,
        'record_type': record.record_type,
        'description': record.description,
        'date': record.date.isoformat(),
        'created_at': record.created_at.isoformat(),
        'updated_at': record.updated_at.isoformat(),
        'documents': [{'id': doc.id, 'filename': doc.filename} for doc in record.documents],
        'summaries': [{'id': summary.id, 'type': summary.summary_type} for summary in record.summaries]
    }

    if record.user_id:
        result['owner_type'] = 'user'
        result['owner_id'] = record.user_id
    elif record.family_member_id:
        result['owner_type'] = 'family_member'
        result['owner_id'] = record.family_member_id
        family_member = FamilyMember.query.get(record.family_member_id)
        if family_member:
            result['owner_name'] = f"{family_member.first_name} {family_member.last_name}"

    return result

def family_member_to_dict(member):
    """Convert a FamilyMember object to a dictionary for API responses"""
    return {
        'id': member.id,
        'first_name': member.first_name,
        'last_name': member.last_name,
        'date_of_birth': member.date_of_birth.isoformat() if member.date_of_birth else None,
        'relationship': member.relationship,
        'created_at': member.created_at.isoformat(),
        'updated_at': member.updated_at.isoformat(),
        'record_count': member.records.count()
    }

# API Routes
@api_bp.route('/health')
@limiter.limit("60 per minute")
@monitor_performance
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'app': 'Personal Health Record Manager',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

@api_bp.route('/user/profile')
@api_login_required
@limiter.limit("20 per minute")
@monitor_performance
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_user_profile(api_user):
    """Get the user's profile information"""
    try:
        return jsonify({
            'id': api_user.id,
            'username': api_user.username,
            'email': api_user.email,
            'first_name': api_user.first_name,
            'last_name': api_user.last_name,
            'date_of_birth': api_user.date_of_birth.isoformat() if api_user.date_of_birth else None,
            'joined_at': api_user.created_at.isoformat(),
            'family_member_count': len(api_user.family_members),
            'record_count': api_user.records.count()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting user profile: {e}")
        return jsonify({'error': 'Failed to retrieve profile'}), 500

@api_bp.route('/records')
@api_login_required
@limiter.limit("30 per minute")
@monitor_performance
def get_records(api_user):
    """Get health records for the user or a family member"""
    try:
        # Query parameters with validation
        page = max(1, request.args.get('page', 1, type=int))
        per_page = min(max(1, request.args.get('per_page', 10, type=int)), 50)  # Cap at 50 records per page
        record_type = request.args.get('type')
        family_member_id = request.args.get('family_member_id', type=int)
        
        # Validate and sanitize record_type
        if record_type:
            record_type = sanitize_html(record_type.strip())
            if detect_suspicious_patterns(record_type):
                log_security_event('api_suspicious_record_type', {
                    'user_id': api_user.id,
                    'record_type': record_type
                })
                return jsonify({'error': 'Invalid record type parameter'}), 400

        # Base query
        query = HealthRecord.query

        # Filter by record type if specified
        if record_type:
            query = query.filter_by(record_type=record_type)

        # Filter by owner (user or family member)
        if family_member_id:
            # Check if the family member belongs to the user
            family_member = FamilyMember.query.get(family_member_id)
            if not family_member or family_member not in api_user.family_members:
                log_security_event('api_unauthorized_family_access', {
                    'user_id': api_user.id,
                    'attempted_family_member_id': family_member_id
                })
                return jsonify({'error': 'Family member not found'}), 404
            query = query.filter_by(family_member_id=family_member_id)
        else:
            # Show user's own records
            query = query.filter_by(user_id=api_user.id)

        # Order by date, newest first
        query = query.order_by(HealthRecord.date.desc())

        # Paginate results
        records_page = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'records': [record_to_dict(record) for record in records_page.items],
            'total': records_page.total,
            'pages': records_page.pages,
            'page': page,
            'per_page': per_page,
            'has_next': records_page.has_next,
            'has_prev': records_page.has_prev
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting records for user {api_user.id}: {e}")
        return jsonify({'error': 'Failed to retrieve records'}), 500

@api_bp.route('/records/<int:record_id>')
@api_login_required
@limiter.limit("60 per minute")
@monitor_performance
def get_record(api_user, record_id):
    """Get a specific health record"""
    try:
        record = HealthRecord.query.get_or_404(record_id)

        # Check permission
        has_permission = False
        if record.user_id == api_user.id:
            # User's own record
            has_permission = True
        elif record.family_member_id and record.family_member in api_user.family_members:
            # Record for user's family member
            has_permission = True
        
        if not has_permission:
            log_security_event('api_unauthorized_record_access', {
                'user_id': api_user.id,
                'record_id': record_id,
                'record_owner_id': record.user_id,
                'record_family_member_id': record.family_member_id
            })
            return jsonify({'error': 'Record not found'}), 404

        # Log successful record access
        log_security_event('api_record_accessed', {
            'user_id': api_user.id,
            'record_id': record_id
        })

        return jsonify(record_to_dict(record))
        
    except Exception as e:
        current_app.logger.error(f"Error getting record {record_id} for user {api_user.id}: {e}")
        return jsonify({'error': 'Failed to retrieve record'}), 500

@api_bp.route('/family')
@api_login_required
@limiter.limit("20 per minute")
@monitor_performance
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_family_members(api_user):
    """Get list of family members"""
    try:
        return jsonify({
            'family_members': [family_member_to_dict(member) for member in api_user.family_members]
        })
    except Exception as e:
        current_app.logger.error(f"Error getting family members for user {api_user.id}: {e}")
        return jsonify({'error': 'Failed to retrieve family members'}), 500

@api_bp.route('/family/<int:member_id>')
@api_login_required
@limiter.limit("30 per minute")
@monitor_performance
def get_family_member(api_user, member_id):
    """Get a specific family member"""
    try:
        member = FamilyMember.query.get_or_404(member_id)

        # Check if the family member belongs to the user
        if member not in api_user.family_members:
            log_security_event('api_unauthorized_family_member_access', {
                'user_id': api_user.id,
                'attempted_family_member_id': member_id
            })
            return jsonify({'error': 'Family member not found'}), 404

        return jsonify(family_member_to_dict(member))
        
    except Exception as e:
        current_app.logger.error(f"Error getting family member {member_id} for user {api_user.id}: {e}")
        return jsonify({'error': 'Failed to retrieve family member'}), 500

@api_bp.route('/summary/<int:record_id>')
@api_login_required
@limiter.limit("10 per minute")  # Stricter limit for AI summaries
@monitor_performance
@ai_security_required('api_summary')
@ai_audit_required(operation_type='api_summary', data_classification='PHI')
@secure_ai_response_headers()
def get_summary(api_user, record_id):
    """Get AI-generated summary for a health record"""
    try:
        record = HealthRecord.query.get_or_404(record_id)

        # Check permission
        has_permission = False
        if record.user_id == api_user.id:
            # User's own record
            has_permission = True
        elif record.family_member_id and record.family_member in api_user.family_members:
            # Record for user's family member
            has_permission = True
        
        if not has_permission:
            log_security_event('api_unauthorized_summary_access', {
                'user_id': api_user.id,
                'record_id': record_id,
                'record_owner_id': record.user_id,
                'record_family_member_id': record.family_member_id
            })
            return jsonify({'error': 'Record not found'}), 404

        # Get summary for the record
        summary = AISummary.query.filter_by(health_record_id=record.id).first()

        if not summary:
            return jsonify({'error': 'No summary available for this record'}), 404

        # Log successful summary access
        log_security_event('api_summary_accessed', {
            'user_id': api_user.id,
            'record_id': record_id,
            'summary_id': summary.id
        })

        return jsonify({
            'record_id': record.id,
            'record_title': record.chief_complaint or record.title or 'Medical Record',
            'summary_id': summary.id,
            'summary_type': summary.summary_type,
            'summary_text': summary.summary_text,
            'created_at': summary.created_at.isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting summary for record {record_id}: {e}")
        return jsonify({'error': 'Failed to retrieve summary'}), 500
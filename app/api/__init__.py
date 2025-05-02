from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash
import functools
from ..models import db, User, HealthRecord, FamilyMember, Document, AISummary
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# API authentication decorator
def api_login_required(view_function):
    @functools.wraps(view_function)
    def decorated_function(*args, **kwargs):
        # Check for Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header is required'}), 401

        # Parse Authorization header
        try:
            auth_type, credentials = auth_header.split(' ', 1)
            if auth_type.lower() != 'basic':
                return jsonify({'error': 'Basic authorization is required'}), 401

            import base64
            decoded = base64.b64decode(credentials).decode('utf-8')
            email, password = decoded.split(':', 1)

            # Authenticate user
            user = User.query.filter_by(email=email).first()
            if not user or not user.check_password(password):
                return jsonify({'error': 'Invalid credentials'}), 401

            # Add user to kwargs
            kwargs['api_user'] = user

            return view_function(*args, **kwargs)

        except Exception as e:
            current_app.logger.error(f"API authentication error: {e}")
            return jsonify({'error': 'Invalid authorization format'}), 401

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
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'app': 'Personal Health Record Manager',
        'timestamp': datetime.utcnow().isoformat()
    })

@api_bp.route('/user/profile')
@api_login_required
def get_user_profile(api_user):
    """Get the user's profile information"""
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

@api_bp.route('/records')
@api_login_required
def get_records(api_user):
    """Get health records for the user or a family member"""
    # Query parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)  # Cap at 50 records per page
    record_type = request.args.get('type')
    family_member_id = request.args.get('family_member_id', type=int)

    # Base query
    query = HealthRecord.query

    # Filter by record type if specified
    if record_type:
        query = query.filter_by(record_type=record_type)

    # Filter by owner (user or family member)
    if family_member_id:
        # Check if the family member belongs to the user
        if FamilyMember.query.get(family_member_id) in api_user.family_members:
            query = query.filter_by(family_member_id=family_member_id)
        else:
            return jsonify({'error': 'Family member not found'}), 404
    else:
        # Show user's own records
        query = query.filter_by(user_id=api_user.id)

    # Order by date, newest first
    query = query.order_by(HealthRecord.date.desc())

    # Paginate results
    records_page = query.paginate(page=page, per_page=per_page)

    return jsonify({
        'records': [record_to_dict(record) for record in records_page.items],
        'total': records_page.total,
        'pages': records_page.pages,
        'page': page,
        'per_page': per_page,
        'has_next': records_page.has_next,
        'has_prev': records_page.has_prev
    })

@api_bp.route('/records/<int:record_id>')
@api_login_required
def get_record(api_user, record_id):
    """Get a specific health record"""
    record = HealthRecord.query.get_or_404(record_id)

    # Check permission
    if record.user_id == api_user.id:
        # User's own record
        pass
    elif record.family_member_id and record.family_member in api_user.family_members:
        # Record for user's family member
        pass
    else:
        return jsonify({'error': 'Record not found'}), 404

    return jsonify(record_to_dict(record))

@api_bp.route('/family')
@api_login_required
def get_family_members(api_user):
    """Get list of family members"""
    return jsonify({
        'family_members': [family_member_to_dict(member) for member in api_user.family_members]
    })

@api_bp.route('/family/<int:member_id>')
@api_login_required
def get_family_member(api_user, member_id):
    """Get a specific family member"""
    member = FamilyMember.query.get_or_404(member_id)

    # Check if the family member belongs to the user
    if member not in api_user.family_members:
        return jsonify({'error': 'Family member not found'}), 404

    return jsonify(family_member_to_dict(member))

@api_bp.route('/summary/<int:record_id>')
@api_login_required
def get_summary(api_user, record_id):
    """Get AI-generated summary for a health record"""
    record = HealthRecord.query.get_or_404(record_id)

    # Check permission
    if record.user_id == api_user.id:
        # User's own record
        pass
    elif record.family_member_id and record.family_member in api_user.family_members:
        # Record for user's family member
        pass
    else:
        return jsonify({'error': 'Record not found'}), 404

    # Get summary for the record
    summary = AISummary.query.filter_by(health_record_id=record.id).first()

    if not summary:
        return jsonify({'error': 'No summary available for this record'}), 404

    return jsonify({
        'record_id': record.id,
        'record_title': record.title,
        'summary_id': summary.id,
        'summary_type': summary.summary_type,
        'summary_text': summary.summary_text,
        'created_at': summary.created_at.isoformat()
    })
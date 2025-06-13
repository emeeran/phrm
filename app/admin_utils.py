"""
Admin utilities for PHRM - Quick database statistics
"""

from flask import Blueprint, render_template_string
from flask_login import current_user, login_required

from app.models import FamilyMember, HealthRecord, User

admin_utils_bp = Blueprint("admin_utils", __name__, url_prefix="/admin")


@admin_utils_bp.route("/stats")
@login_required
def database_stats():
    """Simple database statistics page"""

    # Only allow admin users (you can modify this check)
    if not current_user.is_admin:
        return "Access denied - Admin only", 403

    # Get statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    inactive_users = User.query.filter_by(is_active=False).count()
    admin_users = User.query.filter_by(is_admin=True).count()

    total_records = HealthRecord.query.count()
    total_family_members = FamilyMember.query.count()

    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PHRM Database Statistics</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .stat-card {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                margin: 10px 0;
                display: inline-block;
                min-width: 200px;
            }
            .stat-number { font-size: 2em; color: #0d6efd; font-weight: bold; }
            .stat-label { color: #6c757d; margin-top: 5px; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>📊 PHRM Database Statistics</h1>

        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-number">{{ total_users }}</div>
                <div class="stat-label">Total Users</div>
            </div>

            <div class="stat-card">
                <div class="stat-number">{{ active_users }}</div>
                <div class="stat-label">Active Users</div>
            </div>

            <div class="stat-card">
                <div class="stat-number">{{ total_records }}</div>
                <div class="stat-label">Health Records</div>
            </div>

            <div class="stat-card">
                <div class="stat-number">{{ total_family_members }}</div>
                <div class="stat-label">Family Members</div>
            </div>
        </div>

        <h2>📋 User Details</h2>
        <table>
            <tr>
                <th>Email</th>
                <th>Username</th>
                <th>Status</th>
                <th>Role</th>
                <th>Created</th>
            </tr>
            {% for user in recent_users %}
            <tr>
                <td>{{ user.email }}</td>
                <td>{{ user.username }}</td>
                <td>{{ "Active" if user.is_active else "Inactive" }}</td>
                <td>{{ "Admin" if user.is_admin else "User" }}</td>
                <td>{{ user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else 'Unknown' }}</td>
            </tr>
            {% endfor %}
        </table>

        <div style="margin-top: 20px;">
            <a href="{{ url_for('records.dashboard_routes.dashboard') }}">← Back to Dashboard</a>
        </div>
    </body>
    </html>
    """

    return render_template_string(
        template,
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        admin_users=admin_users,
        total_records=total_records,
        total_family_members=total_family_members,
        recent_users=recent_users,
    )

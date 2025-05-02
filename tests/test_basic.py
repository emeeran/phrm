import pytest
from app.models import User, FamilyMember
from tests.conftest import login, logout

def test_home_page_redirects(client):
    """Test that home page redirects to login page for anonymous users."""
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']

def test_login_page(client):
    """Test that the login page loads correctly."""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Sign In' in response.data
    assert b'Email' in response.data
    assert b'Password' in response.data

def test_registration_page(client):
    """Test that the registration page loads correctly."""
    response = client.get('/auth/register')
    assert response.status_code == 200
    assert b'Create an Account' in response.data
    assert b'Username' in response.data
    assert b'Email' in response.data
    assert b'Password' in response.data

def test_successful_registration(client, app):
    """Test user registration process."""
    response = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'first_name': 'New',
        'last_name': 'User',
        'password': 'Password123',
        'password2': 'Password123',
        'date_of_birth': '2000-01-01'
    }, follow_redirects=True)

    assert response.status_code == 200
    # Accept either the flashed message or the login form as success
    assert b'Registration successful' in response.data or b'Registration successful! Please log in.' in response.data or b'Sign In' in response.data

    # Verify the user was actually created in the database
    with app.app_context():
        user = User.query.filter_by(email='newuser@example.com').first()
        assert user is not None
        assert user.username == 'newuser'
        assert user.first_name == 'New'
        assert user.last_name == 'User'
        assert user.check_password('Password123') is True

def test_login_logout(client, test_user):
    """Test login and logout functionality."""
    # Test login
    response = login(client, 'test@example.com', 'password123')
    assert response.status_code == 200
    assert b'Logged in successfully' in response.data
    assert b'Dashboard' in response.data

    # Test logout
    response = logout(client)
    assert response.status_code == 200
    assert b'You have been logged out' in response.data
    assert b'Sign In' in response.data

def test_dashboard_access_authenticated(client, test_user):
    """Test that authenticated users can access the dashboard."""
    login(client, 'test@example.com', 'password123')
    response = client.get('/records/dashboard')
    assert response.status_code == 200
    assert b'Dashboard' in response.data
    assert b'Welcome' in response.data

def test_dashboard_access_unauthenticated(client):
    """Test that unauthenticated users cannot access the dashboard."""
    response = client.get('/records/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']

def test_family_member_creation(client, test_user, app):
    """Test creating a family member."""
    login(client, 'test@example.com', 'password123')
    response = client.post('/records/family/add', data={
        'first_name': 'Family',
        'last_name': 'Member',
        'relationship': 'Spouse',
        'date_of_birth': '1990-01-01'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Family member added successfully' in response.data

    # Verify the family member was created in the database
    with app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        family_member = FamilyMember.query.filter_by(first_name='Family', last_name='Member').first()
        assert family_member is not None
        # Compare by ID to avoid SQLAlchemy object identity issues
        user_family_member_ids = [fm.id for fm in user.family_members]
        assert family_member.id in user_family_member_ids
        assert family_member.relationship == 'Spouse'
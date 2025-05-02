import os
import sys
import pytest
import tempfile
from app import create_app, db
from app.models import User, FamilyMember, HealthRecord, Document

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()

    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'UPLOAD_FOLDER': tempfile.mkdtemp(),
    })

    # Create the database and the tables
    with app.app_context():
        db.create_all()
        yield app

    # Close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def test_user(app):
    """Create a test user for authentication tests."""
    with app.app_context():
        # Remove any existing user with the same username or email
        existing = User.query.filter((User.username == 'testuser') | (User.email == 'test@example.com')).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
        user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def test_family_member(app, test_user):
    """Create a test family member for the test user."""
    with app.app_context():
        family_member = FamilyMember(
            first_name='Test',
            last_name='Family',
            relationship='Child'
        )
        test_user.family_members.append(family_member)
        db.session.add(family_member)
        db.session.commit()
        return family_member

@pytest.fixture
def test_record(app, test_user):
    """Create a test health record for the test user."""
    with app.app_context():
        record = HealthRecord(
            title='Test Record',
            record_type='doctor_visit',
            description='This is a test record',
            user_id=test_user.id
        )
        db.session.add(record)
        db.session.commit()
        return record

def login(client, email, password):
    """Helper function to log in a user."""
    return client.post('/auth/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)

def logout(client):
    """Helper function to log out a user."""
    return client.get('/auth/logout', follow_redirects=True)
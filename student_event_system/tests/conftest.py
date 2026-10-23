"""Shared test fixtures."""
import os
import sys
import tempfile
import sqlite3
import pytest


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """Create application for testing with temporary database."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    test_app = create_app()
    test_app.config.update({
        'TESTING': True,
        'DATABASE': db_path,
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost',
    })


    with test_app.app_context():
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'schema.sql')
        conn = sqlite3.connect(db_path)
        conn.execute('PRAGMA foreign_keys = ON')
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()

    yield test_app


    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def db(app):
    """Get database connection."""
    with app.app_context():
        from app import get_db
        database = get_db()
        yield database


@pytest.fixture
def admin_user(app, db):
    """Create an admin user and return credentials."""
    pw_hash = generate_password_hash('adminpass123')
    db.execute(
        "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        ('Test Admin', 'admin@test.com', pw_hash, 'admin')
    )
    db.commit()
    return {'email': 'admin@test.com', 'password': 'adminpass123', 'full_name': 'Test Admin'}


@pytest.fixture
def officer_user(app, db):
    """Create an officer user."""
    pw_hash = generate_password_hash('officerpass123')
    db.execute(
        "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        ('Test Officer', 'officer@test.com', pw_hash, 'officer')
    )
    db.commit()
    return {'email': 'officer@test.com', 'password': 'officerpass123'}


@pytest.fixture
def student_user(app, db):
    """Create a student user."""
    pw_hash = generate_password_hash('studentpass123')
    db.execute(
        "INSERT INTO users (student_no, full_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
        ('2024-0001', 'Test Student', 'student@test.com', pw_hash, 'student')
    )
    db.commit()
    return {'email': 'student@test.com', 'password': 'studentpass123', 'student_no': '2024-0001'}


@pytest.fixture
def organization(app, db):
    """Create a test organization."""
    db.execute(
        "INSERT INTO organizations (name, description) VALUES (?, ?)",
        ('Test Org', 'A test organization')
    )
    db.commit()
    return {'name': 'Test Org', 'organization_id': db.execute("SELECT last_insert_rowid()").fetchone()[0]}


@pytest.fixture
def officer_with_org(app, db, officer_user, organization):
    """Create an officer assigned to an organization."""
    officer = db.execute("SELECT user_id FROM users WHERE email = ?",
                          (officer_user['email'],)).fetchone()
    db.execute(
        "INSERT INTO organization_members (organization_id, user_id, member_role) VALUES (?, ?, ?)",
        (organization['organization_id'], officer[0], 'officer')
    )
    db.commit()
    return {**officer_user, 'user_id': officer[0], 'organization_id': organization['organization_id']}


def login(client, email, password):
    """Helper to log in a user."""
    return client.post('/login', data={'email': email, 'password': password},
                       follow_redirects=True)


def logout(client):
    """Helper to log out."""
    return client.post('/logout', follow_redirects=True)

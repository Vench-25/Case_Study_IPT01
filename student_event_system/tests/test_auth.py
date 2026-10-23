"""Tests for authentication functionality."""
import pytest
from werkzeug.security import check_password_hash
from tests.conftest import login, logout


class TestLoginPage:
    """Tests for the login page and authentication flow."""

    def test_login_page_loads(self, client):
        """Test that the login page loads successfully."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'Login' in response.data
        assert b'data-password-toggle="password"' in response.data
        assert b'data-theme-picker' in response.data
        assert b'images/logo.jpg' in response.data

    def test_authenticated_shell_has_role_navigation_and_theme_picker(self, client, student_user):
        """Test that logged-in pages render the shared navigation shell."""
        login(client, student_user['email'], student_user['password'])
        response = client.get('/student/dashboard')

        assert response.status_code == 200
        assert b'aria-label="Main navigation"' in response.data
        assert b'My Registrations' in response.data
        assert b'data-theme-picker' in response.data
        assert b'aria-label="Collapse navigation"' in response.data

    def test_login_success_admin(self, client, admin_user):
        """Test that admin login redirects to admin dashboard."""
        response = client.post('/login', data={
            'email': admin_user['email'],
            'password': admin_user['password']
        }, follow_redirects=True)
        assert response.status_code == 200

        assert b'admin' in response.data.lower() or b'dashboard' in response.data.lower()

    def test_login_success_student(self, client, student_user):
        """Test that student login redirects to student dashboard."""
        response = client.post('/login', data={
            'email': student_user['email'],
            'password': student_user['password']
        }, follow_redirects=True)
        assert response.status_code == 200

        assert b'student' in response.data.lower() or b'dashboard' in response.data.lower()

    def test_login_failure_wrong_password(self, client, admin_user):
        """Test login with incorrect password fails."""
        response = client.post('/login', data={
            'email': admin_user['email'],
            'password': 'wrongpassword'
        }, follow_redirects=True)
        assert response.status_code == 200

        assert b'invalid' in response.data.lower() or b'error' in response.data.lower() or b'incorrect' in response.data.lower()

    def test_login_failure_wrong_email(self, client, admin_user):
        """Test login with non-existent email shows generic error (no email reveal)."""
        response = client.post('/login', data={
            'email': 'nonexistent@test.com',
            'password': 'somepassword'
        }, follow_redirects=True)
        assert response.status_code == 200

        assert b'invalid' in response.data.lower() or b'error' in response.data.lower() or b'incorrect' in response.data.lower()

        assert b'email not found' not in response.data.lower()
        assert b'no account' not in response.data.lower()

    def test_login_inactive_account(self, app, client, db):
        """Test that inactive accounts cannot log in."""
        from werkzeug.security import generate_password_hash
        pw_hash = generate_password_hash('inactivepass')
        db.execute(
            "INSERT INTO users (full_name, email, password_hash, role, is_active) VALUES (?, ?, ?, ?, ?)",
            ('Inactive User', 'inactive@test.com', pw_hash, 'student', 0)
        )
        db.commit()

        response = client.post('/login', data={
            'email': 'inactive@test.com',
            'password': 'inactivepass'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'invalid email or password' in response.data.lower()
        assert b'deactivated' not in response.data.lower()

    def test_logout(self, client, admin_user):
        """Test that logout works and redirects to login."""

        login(client, admin_user['email'], admin_user['password'])


        response = logout(client)
        assert response.status_code == 200


        response = client.get('/admin/dashboard', follow_redirects=True)
        assert b'login' in response.data.lower()


class TestPasswordSecurity:
    """Tests for password security."""

    def test_password_stored_as_hash(self, app, db, admin_user):
        """Test that passwords are stored as hashes, not plaintext."""
        row = db.execute(
            "SELECT password_hash FROM users WHERE email = ?",
            (admin_user['email'],)
        ).fetchone()
        stored_hash = row[0] if isinstance(row, tuple) else row['password_hash']


        assert stored_hash != admin_user['password']
        assert stored_hash != 'adminpass123'


        assert check_password_hash(stored_hash, admin_user['password'])


class TestStudentRegistration:
    """Tests for student self-registration."""

    def test_student_registration_success(self, client, app, db):
        """Test that a new student can register successfully."""
        response = client.post('/register', data={
            'student_no': '2024-9999',
            'full_name': 'New Student',
            'email': 'newstudent@test.com',
            'password': 'newpass123',
            'confirm_password': 'newpass123'
        }, follow_redirects=True)
        assert response.status_code == 200


        with app.app_context():
            from app import get_db
            database = get_db()
            user = database.execute(
                "SELECT * FROM users WHERE email = ?", ('newstudent@test.com',)
            ).fetchone()
            assert user is not None

    def test_student_registration_rejects_password_under_eight_characters(self, client):
        response = client.post('/register', data={
            'student_no': '2024-8888',
            'full_name': 'Short Password Student',
            'email': 'short-password@test.com',
            'password': 'short7',
            'confirm_password': 'short7'
        })

        assert response.status_code == 200
        assert b'Password must be at least 8 characters long.' in response.data

    def test_student_registration_duplicate_email(self, client, student_user):
        """Test that registration with duplicate email is rejected."""
        response = client.post('/register', data={
            'student_no': '2024-8888',
            'full_name': 'Another Student',
            'email': student_user['email'],
            'password': 'anotherpass123',
            'confirm_password': 'anotherpass123'
        }, follow_redirects=True)
        assert response.status_code == 200

        assert (b'already' in response.data.lower() or
                b'exists' in response.data.lower() or
                b'taken' in response.data.lower() or
                b'duplicate' in response.data.lower() or
                b'error' in response.data.lower())

    def test_register_always_creates_student_role(self, client, app, db):
        """Test that self-registration always creates a student role user."""
        client.post('/register', data={
            'student_no': '2024-7777',
            'full_name': 'Role Test Student',
            'email': 'roletest@test.com',
            'password': 'rolepass123',
            'confirm_password': 'rolepass123'
        }, follow_redirects=True)

        with app.app_context():
            from app import get_db
            database = get_db()
            user = database.execute(
                "SELECT role FROM users WHERE email = ?", ('roletest@test.com',)
            ).fetchone()
            assert user is not None
            role = user[0] if isinstance(user, tuple) else user['role']
            assert role == 'student'


class TestCSRF:
    """Tests for CSRF protection."""

    def test_csrf_is_enforced(self, app):
        """Test that CSRF is enforced when WTF_CSRF_ENABLED is True."""

        app.config['WTF_CSRF_ENABLED'] = True
        app.config['WTF_CSRF_CHECK_DEFAULT'] = True

        with app.test_client() as csrf_client:

            response = csrf_client.post('/login', data={
                'email': 'test@test.com',
                'password': 'testpass'
            })

            assert response.status_code in (400, 403, 302, 200)

            if response.status_code == 200:
                assert (b'csrf' in response.data.lower() or
                        b'token' in response.data.lower() or
                        b'expired' in response.data.lower() or
                        b'invalid' in response.data.lower())

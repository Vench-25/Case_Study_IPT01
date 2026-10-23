"""Tests for role-based access control and permissions."""
import pytest
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from tests.conftest import login, logout


def _future(days=30):
    """Return a future datetime string."""
    return (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')


def _get_user_id(db, email):
    """Helper to get user_id by email."""
    row = db.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
    return row[0] if isinstance(row, tuple) else row['user_id']


class TestStudentPermissions:
    """Tests for student role restrictions."""

    def test_student_cannot_access_admin_dashboard(self, client, student_user):
        """Test that a student cannot access the admin dashboard."""
        login(client, student_user['email'], student_user['password'])

        response = client.get('/admin/dashboard')

        assert response.status_code in (403, 302)
        if response.status_code == 302:

            assert '/admin/' not in response.headers.get('Location', '')

    def test_student_cannot_access_officer_dashboard(self, client, student_user):
        """Test that a student cannot access the officer dashboard."""
        login(client, student_user['email'], student_user['password'])

        response = client.get('/officer/dashboard')

        assert response.status_code in (403, 302)
        if response.status_code == 302:
            assert '/officer/' not in response.headers.get('Location', '')


class TestOfficerPermissions:
    """Tests for officer role restrictions."""

    def test_officer_cannot_access_admin_dashboard(self, client, officer_user):
        """Test that an officer cannot access the admin dashboard."""
        login(client, officer_user['email'], officer_user['password'])

        response = client.get('/admin/dashboard')

        assert response.status_code in (403, 302)
        if response.status_code == 302:
            assert '/admin/' not in response.headers.get('Location', '')

    def test_officer_cannot_access_other_org_event(self, client, app, db, officer_with_org):
        """Test that an officer cannot access events from another organization."""

        db.execute(
            "INSERT INTO organizations (name, description) VALUES (?, ?)",
            ('Other Org', 'Another organization')
        )
        db.commit()
        other_org_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]


        pw_hash = generate_password_hash('otherofficerpass')
        db.execute(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ('Other Officer', 'otherofficer@test.com', pw_hash, 'officer')
        )
        db.commit()
        other_officer_id = _get_user_id(db, 'otherofficer@test.com')
        db.execute(
            "INSERT INTO organization_members (organization_id, user_id, member_role) VALUES (?, ?, ?)",
            (other_org_id, other_officer_id, 'officer')
        )
        db.commit()


        db.execute(
            """INSERT INTO events (organization_id, created_by, title, description, venue,
               start_at, end_at, registration_deadline, capacity, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (other_org_id, other_officer_id, 'Other Org Event', 'Desc', 'Venue',
             _future(30), _future(31), _future(25), 50, 'draft')
        )
        db.commit()
        other_event_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]


        login(client, officer_with_org['email'], officer_with_org['password'])

        response = client.get(f'/officer/events/{other_event_id}/edit')

        assert response.status_code in (403, 302, 404)


class TestUnauthenticatedAccess:
    """Tests for unauthenticated user restrictions."""

    def test_unauthenticated_redirected_to_login(self, client):
        """Test that unauthenticated users are redirected to login."""
        protected_routes = [
            '/admin/dashboard',
            '/officer/dashboard',
            '/student/dashboard',
            '/student/events',
        ]

        for route in protected_routes:
            response = client.get(route)

            assert response.status_code in (302, 401, 403), \
                f"Route {route} returned {response.status_code} instead of redirect"
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                assert 'login' in location.lower(), \
                    f"Route {route} redirected to {location} instead of login"


class TestAdminPermissions:
    """Tests for admin role access."""

    def test_admin_can_access_admin_routes(self, client, admin_user):
        """Test that admin can access admin routes."""
        login(client, admin_user['email'], admin_user['password'])

        admin_routes = [
            '/admin/dashboard',
            '/admin/users',
        ]

        for route in admin_routes:
            response = client.get(route)

            assert response.status_code in (200, 302), \
                f"Admin denied access to {route} with status {response.status_code}"
            if response.status_code == 302:
                location = response.headers.get('Location', '')

                assert 'login' not in location.lower(), \
                    f"Admin redirected to login from {route}"

    def test_admin_can_delete_deactivated_user(self, client, db, admin_user, student_user):
        """Deleting a deactivated user removes the account and records the action."""
        target_id = _get_user_id(db, student_user['email'])
        db.execute('UPDATE users SET is_active = 0 WHERE user_id = ?', (target_id,))
        db.commit()
        login(client, admin_user['email'], admin_user['password'])

        response = client.post(f'/admin/users/{target_id}/delete', follow_redirects=True)

        assert response.status_code == 200
        assert db.execute(
            'SELECT user_id FROM users WHERE user_id = ?', (target_id,)
        ).fetchone() is None
        audit = db.execute(
            "SELECT action, target_id FROM audit_log WHERE action = 'user_deleted'"
        ).fetchone()
        assert audit['action'] == 'user_deleted'
        assert audit['target_id'] == target_id
        assert b'permanently deleted' in response.data

    def test_admin_cannot_delete_active_user(self, client, db, admin_user, student_user):
        """An account must be deactivated before it can be deleted."""
        target_id = _get_user_id(db, student_user['email'])
        login(client, admin_user['email'], admin_user['password'])

        response = client.post(f'/admin/users/{target_id}/delete', follow_redirects=True)

        assert response.status_code == 200
        assert db.execute(
            'SELECT user_id FROM users WHERE user_id = ?', (target_id,)
        ).fetchone() is not None
        assert b'Deactivate this account before deleting it.' in response.data

    def test_admin_cannot_delete_user_with_linked_records(
            self, client, db, admin_user, student_user, organization):
        """Linked organization history is preserved and prevents account deletion."""
        target_id = _get_user_id(db, student_user['email'])
        db.execute('UPDATE users SET is_active = 0 WHERE user_id = ?', (target_id,))
        db.execute(
            'INSERT INTO organization_members (organization_id, user_id) VALUES (?, ?)',
            (organization['organization_id'], target_id)
        )
        db.commit()
        login(client, admin_user['email'], admin_user['password'])

        response = client.post(f'/admin/users/{target_id}/delete', follow_redirects=True)

        assert response.status_code == 200
        assert db.execute(
            'SELECT user_id FROM users WHERE user_id = ?', (target_id,)
        ).fetchone() is not None
        assert b'existing records are linked to this account' in response.data

    def test_admin_can_delete_inactive_organization(self, client, db, admin_user, organization):
        """Deleting an inactive organization removes it and records the action."""
        organization_id = organization['organization_id']
        db.execute(
            'UPDATE organizations SET is_active = 0 WHERE organization_id = ?',
            (organization_id,)
        )
        db.commit()
        login(client, admin_user['email'], admin_user['password'])

        response = client.post(
            f'/admin/organizations/{organization_id}/delete',
            follow_redirects=True
        )

        assert response.status_code == 200
        assert db.execute(
            'SELECT organization_id FROM organizations WHERE organization_id = ?',
            (organization_id,)
        ).fetchone() is None
        audit = db.execute(
            "SELECT action, target_id FROM audit_log WHERE action = 'organization_deleted'"
        ).fetchone()
        assert audit['action'] == 'organization_deleted'
        assert audit['target_id'] == organization_id
        assert b'permanently deleted' in response.data

    def test_admin_cannot_delete_active_organization(
            self, client, db, admin_user, organization):
        """An organization must be deactivated before it can be deleted."""
        organization_id = organization['organization_id']
        login(client, admin_user['email'], admin_user['password'])

        response = client.post(
            f'/admin/organizations/{organization_id}/delete',
            follow_redirects=True
        )

        assert response.status_code == 200
        assert db.execute(
            'SELECT organization_id FROM organizations WHERE organization_id = ?',
            (organization_id,)
        ).fetchone() is not None
        assert b'Deactivate this organization before deleting it.' in response.data

    def test_admin_cannot_delete_organization_with_linked_records(
            self, client, db, admin_user, organization):
        """Existing organization membership history is preserved."""
        organization_id = organization['organization_id']
        db.execute(
            'UPDATE organizations SET is_active = 0 WHERE organization_id = ?',
            (organization_id,)
        )
        db.execute(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ('Organization Member', 'member@test.com',
             generate_password_hash('memberpass123'), 'student')
        )
        member_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        db.execute(
            'INSERT INTO organization_members (organization_id, user_id) VALUES (?, ?)',
            (organization_id, member_id)
        )
        db.commit()
        login(client, admin_user['email'], admin_user['password'])

        response = client.post(
            f'/admin/organizations/{organization_id}/delete',
            follow_redirects=True
        )

        assert response.status_code == 200
        assert db.execute(
            'SELECT organization_id FROM organizations WHERE organization_id = ?',
            (organization_id,)
        ).fetchone() is not None
        assert b'existing records are linked to it' in response.data

    def test_student_cannot_delete_organization(
            self, client, db, student_user, organization):
        """Organization deletion remains restricted to administrators."""
        organization_id = organization['organization_id']
        db.execute(
            'UPDATE organizations SET is_active = 0 WHERE organization_id = ?',
            (organization_id,)
        )
        db.commit()
        login(client, student_user['email'], student_user['password'])

        response = client.post(f'/admin/organizations/{organization_id}/delete')

        assert response.status_code == 403
        assert db.execute(
            'SELECT organization_id FROM organizations WHERE organization_id = ?',
            (organization_id,)
        ).fetchone() is not None


class TestExportAuthorization:
    """Tests for CSV export authorization."""

    def test_csv_export_requires_authorization(self, client, app, db, student_user, officer_with_org):
        """Test that CSV export requires proper authorization (officer or admin)."""

        db.execute(
            """INSERT INTO events (organization_id, created_by, title, description, venue,
               start_at, end_at, registration_deadline, capacity, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (officer_with_org['organization_id'], officer_with_org['user_id'],
             'Export Test Event', 'Desc', 'Venue',
             _future(30), _future(31), _future(25), 50, 'published')
        )
        db.commit()
        event_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]


        response = client.get(f'/officer/events/{event_id}/export')
        assert response.status_code in (302, 401, 403)


        login(client, student_user['email'], student_user['password'])
        response = client.get(f'/officer/events/{event_id}/export')
        assert response.status_code in (302, 403)

        logout(client)


        login(client, officer_with_org['email'], officer_with_org['password'])
        response = client.get(f'/officer/events/{event_id}/export')

        assert response.status_code in (200, 302)

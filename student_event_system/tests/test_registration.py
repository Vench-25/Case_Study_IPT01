"""Tests for event registration functionality."""
import pytest
from datetime import datetime, timedelta
from tests.conftest import login, logout


def _future(days=30):
    """Return a future datetime string."""
    return (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')


def _past(days=1):
    """Return a past datetime string."""
    return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')


def _create_event(db, org_id, created_by, title='Reg Test Event', status='published',
                  start_at=None, end_at=None, deadline=None, capacity=50):
    """Helper to insert an event directly into the database."""
    start_at = start_at or _future(30)
    end_at = end_at or _future(31)
    deadline = deadline or _future(25)

    db.execute(
        """INSERT INTO events (organization_id, created_by, title, description, venue,
           start_at, end_at, registration_deadline, capacity, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (org_id, created_by, title, 'Registration test event', 'Test Venue',
         start_at, end_at, deadline, capacity, status)
    )
    db.commit()
    return db.execute("SELECT last_insert_rowid()").fetchone()[0]


def _get_student_id(db, email):
    """Helper to get user_id by email."""
    row = db.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
    return row[0] if isinstance(row, tuple) else row['user_id']


class TestStudentRegistration:
    """Tests for student event registration."""

    def test_student_can_register(self, client, app, db, student_user, officer_with_org):
        """Test that a student can register for a published event."""
        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Open Event'
        )

        login(client, student_user['email'], student_user['password'])

        response = client.post(f'/student/events/{event_id}/register', follow_redirects=True)
        assert response.status_code == 200


        with app.app_context():
            from app import get_db
            database = get_db()
            student_id = _get_student_id(database, student_user['email'])
            reg = database.execute(
                "SELECT * FROM registrations WHERE event_id = ? AND user_id = ?",
                (event_id, student_id)
            ).fetchone()
            assert reg is not None

    def test_duplicate_registration_rejected(self, client, app, db, student_user, officer_with_org):
        """Test that a student cannot register for the same event twice."""
        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Dup Reg Event'
        )


        student_id = _get_student_id(db, student_user['email'])
        db.execute(
            "INSERT INTO registrations (event_id, user_id, status) VALUES (?, ?, ?)",
            (event_id, student_id, 'registered')
        )
        db.commit()

        login(client, student_user['email'], student_user['password'])

        response = client.post(f'/student/events/{event_id}/register', follow_redirects=True)
        assert response.status_code in (200, 400, 409)

        if response.status_code == 200:
            assert (b'already' in response.data.lower() or
                    b'registered' in response.data.lower() or
                    b'error' in response.data.lower() or
                    b'duplicate' in response.data.lower())

    def test_registration_after_deadline_rejected(self, client, db, student_user, officer_with_org):
        """Test that registration after the deadline is rejected."""
        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Deadline Passed Event',
            deadline=_past(1),
            start_at=_future(5),
            end_at=_future(6)
        )

        login(client, student_user['email'], student_user['password'])

        response = client.post(f'/student/events/{event_id}/register', follow_redirects=True)
        assert response.status_code in (200, 400, 403)

        if response.status_code == 200:
            assert (b'deadline' in response.data.lower() or
                    b'closed' in response.data.lower() or
                    b'expired' in response.data.lower() or
                    b'error' in response.data.lower() or
                    b'cannot' in response.data.lower())

    def test_registration_when_full_rejected(self, client, app, db, student_user, officer_with_org):
        """Test that registration is rejected when event is at capacity."""
        from werkzeug.security import generate_password_hash

        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Full Event', capacity=1
        )


        pw_hash = generate_password_hash('fillerpass')
        db.execute(
            "INSERT INTO users (student_no, full_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            ('2024-FILL', 'Filler Student', 'filler@test.com', pw_hash, 'student')
        )
        db.commit()
        filler_id = _get_student_id(db, 'filler@test.com')
        db.execute(
            "INSERT INTO registrations (event_id, user_id, status) VALUES (?, ?, ?)",
            (event_id, filler_id, 'registered')
        )
        db.commit()


        login(client, student_user['email'], student_user['password'])

        response = client.post(f'/student/events/{event_id}/register', follow_redirects=True)
        assert response.status_code in (200, 400, 403)
        if response.status_code == 200:
            assert (b'full' in response.data.lower() or
                    b'capacity' in response.data.lower() or
                    b'no more' in response.data.lower() or
                    b'error' in response.data.lower() or
                    b'cannot' in response.data.lower())

    def test_registration_for_draft_event_rejected(self, client, db, student_user, officer_with_org):
        """Test that students cannot register for draft events."""
        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Draft Only Event', status='draft'
        )

        login(client, student_user['email'], student_user['password'])

        response = client.post(f'/student/events/{event_id}/register', follow_redirects=True)
        assert response.status_code in (200, 400, 403, 404)

        if response.status_code == 200:
            assert (b'draft' in response.data.lower() or
                    b'not available' in response.data.lower() or
                    b'cannot' in response.data.lower() or
                    b'error' in response.data.lower() or
                    b'not published' in response.data.lower())

    def test_registration_for_cancelled_event_rejected(self, client, db, student_user, officer_with_org):
        """Test that students cannot register for cancelled events."""
        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Cancelled Event', status='cancelled'
        )

        login(client, student_user['email'], student_user['password'])

        response = client.post(f'/student/events/{event_id}/register', follow_redirects=True)
        assert response.status_code in (200, 400, 403, 404)
        if response.status_code == 200:
            assert (b'cancelled' in response.data.lower() or
                    b'canceled' in response.data.lower() or
                    b'not available' in response.data.lower() or
                    b'cannot' in response.data.lower() or
                    b'error' in response.data.lower())

    def test_cancel_registration(self, client, app, db, student_user, officer_with_org):
        """Test that a student can cancel their registration."""
        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Cancel Reg Event'
        )

        student_id = _get_student_id(db, student_user['email'])
        db.execute(
            "INSERT INTO registrations (event_id, user_id, status) VALUES (?, ?, ?)",
            (event_id, student_id, 'registered')
        )
        db.commit()

        login(client, student_user['email'], student_user['password'])

        response = client.post(f'/student/events/{event_id}/cancel', follow_redirects=True)
        assert response.status_code == 200


        with app.app_context():
            from app import get_db
            database = get_db()
            reg = database.execute(
                "SELECT status FROM registrations WHERE event_id = ? AND user_id = ?",
                (event_id, student_id)
            ).fetchone()
            reg_status = reg[0] if isinstance(reg, tuple) else reg['status']
            assert reg_status == 'cancelled'

    def test_reactivate_cancelled_registration(self, client, app, db, student_user, officer_with_org):
        """Test that a cancelled registration can be reactivated."""
        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Reactivate Reg Event'
        )

        student_id = _get_student_id(db, student_user['email'])
        db.execute(
            "INSERT INTO registrations (event_id, user_id, status) VALUES (?, ?, ?)",
            (event_id, student_id, 'cancelled')
        )
        db.commit()

        login(client, student_user['email'], student_user['password'])


        response = client.post(f'/student/events/{event_id}/register', follow_redirects=True)
        assert response.status_code == 200


        with app.app_context():
            from app import get_db
            database = get_db()
            reg = database.execute(
                "SELECT status FROM registrations WHERE event_id = ? AND user_id = ?",
                (event_id, student_id)
            ).fetchone()
            reg_status = reg[0] if isinstance(reg, tuple) else reg['status']
            assert reg_status == 'registered'

    def test_capacity_enforcement(self, client, app, db, officer_with_org):
        """Test that capacity is strictly enforced — register up to capacity, next one fails."""
        from werkzeug.security import generate_password_hash

        capacity = 3
        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Capacity Test Event', capacity=capacity
        )


        for i in range(capacity):
            pw_hash = generate_password_hash(f'cappass{i}')
            db.execute(
                "INSERT INTO users (student_no, full_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
                (f'2024-C{i:03d}', f'Cap Student {i}', f'cap{i}@test.com', pw_hash, 'student')
            )
            db.commit()
            uid = _get_student_id(db, f'cap{i}@test.com')
            db.execute(
                "INSERT INTO registrations (event_id, user_id, status) VALUES (?, ?, ?)",
                (event_id, uid, 'registered')
            )
            db.commit()


        pw_hash = generate_password_hash('overflowpass')
        db.execute(
            "INSERT INTO users (student_no, full_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            ('2024-OVER', 'Overflow Student', 'overflow@test.com', pw_hash, 'student')
        )
        db.commit()

        login(client, 'overflow@test.com', 'overflowpass')

        response = client.post(f'/student/events/{event_id}/register', follow_redirects=True)
        assert response.status_code in (200, 400, 403)


        with app.app_context():
            from app import get_db
            database = get_db()
            overflow_id = _get_student_id(database, 'overflow@test.com')
            reg = database.execute(
                "SELECT * FROM registrations WHERE event_id = ? AND user_id = ? AND status = 'registered'",
                (event_id, overflow_id)
            ).fetchone()
            assert reg is None

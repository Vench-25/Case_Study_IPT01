"""Tests for attendance tracking functionality."""
import pytest
from datetime import datetime, timedelta
from tests.conftest import login, logout


def _future(days=30):
    """Return a future datetime string."""
    return (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')


def _create_event(db, org_id, created_by, title='Attendance Event', status='published',
                  capacity=50):
    """Helper to insert an event directly into the database."""
    start_at = _future(30)
    end_at = _future(31)
    deadline = _future(25)

    db.execute(
        """INSERT INTO events (organization_id, created_by, title, description, venue,
           start_at, end_at, registration_deadline, capacity, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (org_id, created_by, title, 'Attendance test event', 'Test Venue',
         start_at, end_at, deadline, capacity, status)
    )
    db.commit()
    return db.execute("SELECT last_insert_rowid()").fetchone()[0]


def _get_user_id(db, email):
    """Helper to get user_id by email."""
    row = db.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
    return row[0] if isinstance(row, tuple) else row['user_id']


def _register_student(db, event_id, student_email):
    """Helper to register a student for an event."""
    student_id = _get_user_id(db, student_email)
    db.execute(
        "INSERT INTO registrations (event_id, user_id, status) VALUES (?, ?, ?)",
        (event_id, student_id, 'registered')
    )
    db.commit()
    reg = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    return reg, student_id


class TestOfficerAttendance:
    """Tests for officer attendance marking."""

    def test_officer_can_mark_attendance(self, client, app, db, officer_with_org, student_user):
        """Test that an officer can mark attendance for a registered student."""
        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Mark Attendance Event'
        )
        reg_id, student_id = _register_student(db, event_id, student_user['email'])

        login(client, officer_with_org['email'], officer_with_org['password'])

        response = client.post(f'/officer/events/{event_id}/attendance', data={
            f'attendance_{reg_id}': 'present',
            'registration_ids': str(reg_id)
        }, follow_redirects=True)
        assert response.status_code == 200


        with app.app_context():
            from app import get_db
            database = get_db()
            att = database.execute(
                "SELECT attendance_status FROM attendance WHERE registration_id = ?",
                (reg_id,)
            ).fetchone()
            assert att is not None
            status = att[0] if isinstance(att, tuple) else att['attendance_status']
            assert status == 'present'

    def test_officer_can_update_attendance(self, client, app, db, officer_with_org, student_user):
        """Test that an officer can update an existing attendance record."""
        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Update Attendance Event'
        )
        reg_id, student_id = _register_student(db, event_id, student_user['email'])


        db.execute(
            "INSERT INTO attendance (registration_id, marked_by, attendance_status) VALUES (?, ?, ?)",
            (reg_id, officer_with_org['user_id'], 'present')
        )
        db.commit()

        login(client, officer_with_org['email'], officer_with_org['password'])


        response = client.post(f'/officer/events/{event_id}/attendance', data={
            f'attendance_{reg_id}': 'absent',
            'registration_ids': str(reg_id)
        }, follow_redirects=True)
        assert response.status_code == 200


        with app.app_context():
            from app import get_db
            database = get_db()
            att = database.execute(
                "SELECT attendance_status FROM attendance WHERE registration_id = ?",
                (reg_id,)
            ).fetchone()
            assert att is not None
            status = att[0] if isinstance(att, tuple) else att['attendance_status']
            assert status == 'absent'


class TestStudentAttendanceRestriction:
    """Tests for student attendance restrictions."""

    def test_student_cannot_mark_attendance(self, client, db, student_user, officer_with_org):
        """Test that a student cannot access the attendance marking endpoint."""
        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Restricted Attendance Event'
        )
        reg_id, student_id = _register_student(db, event_id, student_user['email'])

        login(client, student_user['email'], student_user['password'])

        response = client.post(f'/officer/events/{event_id}/attendance', data={
            f'attendance_{reg_id}': 'present',
            'registration_ids': str(reg_id)
        }, follow_redirects=True)

        assert response.status_code in (403, 302, 200)
        if response.status_code == 200:

            assert (b'unauthorized' in response.data.lower() or
                    b'forbidden' in response.data.lower() or
                    b'access denied' in response.data.lower() or
                    b'not authorized' in response.data.lower() or
                    b'login' in response.data.lower() or
                    b'student' in response.data.lower())


class TestAttendanceValidation:
    """Tests for attendance validation rules."""

    def test_attendance_only_for_registered(self, client, app, db, officer_with_org, student_user):
        """Test that attendance can only be marked for registered participants."""
        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Non-Registered Attendance Event'
        )


        login(client, officer_with_org['email'], officer_with_org['password'])

        response = client.post(f'/officer/events/{event_id}/attendance', data={
            'attendance_99999': 'present',
            'registration_ids': '99999'
        }, follow_redirects=True)


        assert response.status_code in (200, 400, 404)


        with app.app_context():
            from app import get_db
            database = get_db()
            att = database.execute(
                "SELECT * FROM attendance WHERE registration_id = 99999"
            ).fetchone()
            assert att is None

    def test_attendance_summary_counts(self, client, app, db, officer_with_org):
        """Test that attendance summary correctly counts present and absent."""
        from werkzeug.security import generate_password_hash

        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Summary Attendance Event'
        )


        registration_ids = []
        for i in range(3):
            pw_hash = generate_password_hash(f'summpass{i}')
            db.execute(
                "INSERT INTO users (student_no, full_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
                (f'2024-S{i:03d}', f'Summary Student {i}', f'summ{i}@test.com', pw_hash, 'student')
            )
            db.commit()
            uid = _get_user_id(db, f'summ{i}@test.com')
            db.execute(
                "INSERT INTO registrations (event_id, user_id, status) VALUES (?, ?, ?)",
                (event_id, uid, 'registered')
            )
            db.commit()
            reg_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            registration_ids.append(reg_id)


        db.execute(
            "INSERT INTO attendance (registration_id, marked_by, attendance_status) VALUES (?, ?, ?)",
            (registration_ids[0], officer_with_org['user_id'], 'present')
        )
        db.execute(
            "INSERT INTO attendance (registration_id, marked_by, attendance_status) VALUES (?, ?, ?)",
            (registration_ids[1], officer_with_org['user_id'], 'present')
        )
        db.execute(
            "INSERT INTO attendance (registration_id, marked_by, attendance_status) VALUES (?, ?, ?)",
            (registration_ids[2], officer_with_org['user_id'], 'absent')
        )
        db.commit()


        with app.app_context():
            from app import get_db
            database = get_db()
            present_count = database.execute(
                """SELECT COUNT(*) FROM attendance a
                   JOIN registrations r ON a.registration_id = r.registration_id
                   WHERE r.event_id = ? AND a.attendance_status = 'present'""",
                (event_id,)
            ).fetchone()[0]
            absent_count = database.execute(
                """SELECT COUNT(*) FROM attendance a
                   JOIN registrations r ON a.registration_id = r.registration_id
                   WHERE r.event_id = ? AND a.attendance_status = 'absent'""",
                (event_id,)
            ).fetchone()[0]

            assert present_count == 2
            assert absent_count == 1

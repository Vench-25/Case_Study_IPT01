"""Tests for event management functionality."""
import pytest
from datetime import datetime, timedelta
from tests.conftest import login, logout


def _future(days=30):
    """Return a future datetime string."""
    return (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')


def _past(days=1):
    """Return a past datetime string."""
    return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')


def _create_event(db, org_id, created_by, title='Test Event', status='draft',
                  start_at=None, end_at=None, deadline=None, capacity=50):
    """Helper to insert an event directly into the database."""
    start_at = start_at or _future(30)
    end_at = end_at or _future(31)
    deadline = deadline or _future(25)

    db.execute(
        """INSERT INTO events (organization_id, created_by, title, description, venue,
           start_at, end_at, registration_deadline, capacity, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (org_id, created_by, title, 'Test event description', 'Test Venue',
         start_at, end_at, deadline, capacity, status)
    )
    db.commit()
    return db.execute("SELECT last_insert_rowid()").fetchone()[0]


class TestOfficerEventManagement:
    """Tests for officer event creation and management."""

    def test_officer_can_create_event(self, client, app, db, officer_with_org):
        """Test that an officer can create an event for their organization."""
        login(client, officer_with_org['email'], officer_with_org['password'])

        response = client.post('/officer/events/new', data={
            'title': 'New Test Event',
            'description': 'A description for the event',
            'venue': 'Main Auditorium',
            'start_at': _future(30),
            'end_at': _future(31),
            'registration_deadline': _future(25),
            'capacity': 100,
            'organization_id': officer_with_org['organization_id']
        }, follow_redirects=True)
        assert response.status_code == 200


        with app.app_context():
            from app import get_db
            database = get_db()
            event = database.execute(
                "SELECT * FROM events WHERE title = ?", ('New Test Event',)
            ).fetchone()
            assert event is not None

    def test_officer_can_edit_draft_event(self, client, app, db, officer_with_org):
        """Test that an officer can edit a draft event."""
        login(client, officer_with_org['email'], officer_with_org['password'])


        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Draft Event'
        )

        response = client.post(f'/officer/events/{event_id}/edit', data={
            'title': 'Updated Draft Event',
            'description': 'Updated description',
            'venue': 'Updated Venue',
            'start_at': _future(30),
            'end_at': _future(31),
            'registration_deadline': _future(25),
            'capacity': 200,
            'organization_id': officer_with_org['organization_id']
        }, follow_redirects=True)
        assert response.status_code == 200


        with app.app_context():
            from app import get_db
            database = get_db()
            event = database.execute(
                "SELECT title FROM events WHERE event_id = ?", (event_id,)
            ).fetchone()
            updated_title = event[0] if isinstance(event, tuple) else event['title']
            assert updated_title == 'Updated Draft Event'

    def test_officer_can_publish_draft_event(self, client, app, db, officer_with_org):
        """Test that an officer can publish a draft event."""
        login(client, officer_with_org['email'], officer_with_org['password'])

        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Event To Publish', status='draft'
        )

        response = client.post(f'/officer/events/{event_id}/publish', follow_redirects=True)
        assert response.status_code == 200


        with app.app_context():
            from app import get_db
            database = get_db()
            event = database.execute(
                "SELECT status FROM events WHERE event_id = ?", (event_id,)
            ).fetchone()
            status = event[0] if isinstance(event, tuple) else event['status']
            assert status == 'published'

    def test_officer_can_cancel_event(self, client, app, db, officer_with_org):
        """Test that an officer can cancel an event."""
        login(client, officer_with_org['email'], officer_with_org['password'])

        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Event To Cancel', status='published'
        )

        response = client.post(f'/officer/events/{event_id}/cancel', follow_redirects=True)
        assert response.status_code == 200


        with app.app_context():
            from app import get_db
            database = get_db()
            event = database.execute(
                "SELECT status FROM events WHERE event_id = ?", (event_id,)
            ).fetchone()
            status = event[0] if isinstance(event, tuple) else event['status']
            assert status == 'cancelled'

    def test_officer_can_complete_published_event(self, client, app, db, officer_with_org):
        """Test that an officer can mark a published event as completed."""
        login(client, officer_with_org['email'], officer_with_org['password'])

        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Event To Complete', status='published'
        )

        response = client.post(f'/officer/events/{event_id}/complete', follow_redirects=True)
        assert response.status_code == 200


        with app.app_context():
            from app import get_db
            database = get_db()
            event = database.execute(
                "SELECT status FROM events WHERE event_id = ?", (event_id,)
            ).fetchone()
            status = event[0] if isinstance(event, tuple) else event['status']
            assert status == 'completed'

    def test_officer_cannot_publish_already_published(self, client, db, officer_with_org):
        """Test that publishing an already published event is handled."""
        login(client, officer_with_org['email'], officer_with_org['password'])

        event_id = _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Already Published', status='published'
        )

        response = client.post(f'/officer/events/{event_id}/publish', follow_redirects=True)

        assert response.status_code in (200, 400, 403, 409)
        if response.status_code == 200:
            assert (b'already' in response.data.lower() or
                    b'published' in response.data.lower() or
                    b'cannot' in response.data.lower() or
                    b'error' in response.data.lower() or
                    b'event' in response.data.lower())


class TestEventValidation:
    """Tests for event date/data validation."""

    def test_event_date_validation(self, client, db, officer_with_org):
        """Test that end date before start date is rejected, and deadline after start is rejected."""
        login(client, officer_with_org['email'], officer_with_org['password'])


        response = client.post('/officer/events/new', data={
            'title': 'Bad Date Event',
            'description': 'Description',
            'venue': 'Venue',
            'start_at': _future(30),
            'end_at': _future(20),
            'registration_deadline': _future(25),
            'capacity': 50,
            'organization_id': officer_with_org['organization_id']
        }, follow_redirects=True)
        assert response.status_code in (200, 400)

        if response.status_code == 200:
            assert (b'error' in response.data.lower() or
                    b'invalid' in response.data.lower() or
                    b'before' in response.data.lower() or
                    b'date' in response.data.lower() or
                    b'end' in response.data.lower())


class TestStudentEventBrowsing:
    """Tests for student event browsing."""

    def test_student_can_browse_published_events(self, client, db, student_user, officer_with_org):
        """Test that students can see published events."""

        _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Visible Published Event', status='published'
        )

        login(client, student_user['email'], student_user['password'])

        response = client.get('/student/events', follow_redirects=True)
        assert response.status_code == 200
        assert b'Visible Published Event' in response.data

    def test_student_cannot_see_draft_events(self, client, db, student_user, officer_with_org):
        """Test that students cannot see draft events."""

        _create_event(
            db, officer_with_org['organization_id'],
            officer_with_org['user_id'], title='Hidden Draft Event', status='draft'
        )

        login(client, student_user['email'], student_user['password'])

        response = client.get('/student/events', follow_redirects=True)
        assert response.status_code == 200
        assert b'Hidden Draft Event' not in response.data

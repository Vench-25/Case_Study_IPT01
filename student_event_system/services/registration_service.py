"""
Registration service.
Handles event registration, cancellation, reactivation with full validation.
"""
from datetime import datetime


def parse_dt(dt_str):
    """Helper to parse datetime from multiple supported string formats."""
    if not dt_str:
        return None
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(dt_str, fmt)
        except (ValueError, TypeError):
            continue
    return None


def get_registration_count(db, event_id):
    """Count active registrations for an event."""
    result = db.execute(
        "SELECT COUNT(*) FROM registrations WHERE event_id = ? AND status = 'registered'",
        (event_id,)
    ).fetchone()
    return result[0]


def get_user_event_registration(db, event_id, user_id):
    """Get a user's registration for a specific event (any status)."""
    return db.execute(
        'SELECT * FROM registrations WHERE event_id = ? AND user_id = ?',
        (event_id, user_id)
    ).fetchone()


def register_for_event(db, event_id, user_id):
    """
    Register a student for an event. Handles new registration and reactivation
    of cancelled registration. Uses a transaction for atomicity.
    Returns (success: bool, message: str).
    """
    try:

        event = db.execute(
            'SELECT * FROM events WHERE event_id = ?', (event_id,)
        ).fetchone()

        if not event:
            return False, 'Event not found.'

        if event['status'] != 'published':
            return False, f'Registration is not available. Event is {event["status"]} and not published, cannot register.'


        org = db.execute(
            'SELECT is_active FROM organizations WHERE organization_id = ?',
            (event['organization_id'],)
        ).fetchone()
        if not org or not org['is_active']:
            return False, 'The organizing body for this event is not active.'


        now = datetime.now()
        deadline = parse_dt(event['registration_deadline'])
        if deadline and now > deadline:
            return False, 'The registration deadline has passed.'


        existing = db.execute(
            'SELECT * FROM registrations WHERE event_id = ? AND user_id = ?',
            (event_id, user_id)
        ).fetchone()

        if existing:
            if existing['status'] == 'registered':
                return False, 'You are already registered for this event.'
            elif existing['status'] == 'cancelled':

                active_count = get_registration_count(db, event_id)
                if active_count >= event['capacity']:
                    return False, 'This event has reached its maximum capacity.'

                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                db.execute(
                    '''UPDATE registrations SET status = 'registered', registered_at = ?
                       WHERE registration_id = ?''',
                    (now_str, existing['registration_id'])
                )
                db.commit()
                return True, 'Your registration has been reactivated successfully.'


        active_count = get_registration_count(db, event_id)
        if active_count >= event['capacity']:
            return False, 'This event has reached its maximum capacity.'


        db.execute(
            'INSERT INTO registrations (event_id, user_id, status) VALUES (?, ?, ?)',
            (event_id, user_id, 'registered')
        )
        db.commit()
        return True, 'You have been successfully registered for this event.'

    except Exception as e:
        db.rollback()
        return False, 'An error occurred during registration. Please try again.'


def cancel_registration(db, registration_id, user_id):
    """
    Cancel a student's own registration.
    Returns (success: bool, message: str).
    """
    try:
        reg = db.execute(
            'SELECT * FROM registrations WHERE registration_id = ? AND user_id = ?',
            (registration_id, user_id)
        ).fetchone()

        if not reg:
            return False, 'Registration not found.'

        if reg['status'] == 'cancelled':
            return False, 'This registration is already cancelled.'


        event = db.execute(
            'SELECT * FROM events WHERE event_id = ?', (reg['event_id'],)
        ).fetchone()

        if not event:
            return False, 'Associated event not found.'

        if event['status'] != 'published':
            return False, 'Cancellation is not allowed for events that are not published.'


        now = datetime.now()
        start = parse_dt(event['start_at'])
        if start and now >= start:
            return False, 'Cannot cancel registration after the event has started.'

        db.execute(
            "UPDATE registrations SET status = 'cancelled' WHERE registration_id = ?",
            (registration_id,)
        )
        db.commit()
        return True, 'Your registration has been cancelled.'

    except Exception as e:
        db.rollback()
        return False, 'An error occurred. Please try again.'


def cancel_event_registration(db, event_id, user_id):
    """Cancel registration for a user by event_id."""
    reg = get_user_event_registration(db, event_id, user_id)
    if not reg:
        return False, 'Registration not found.'
    return cancel_registration(db, reg['registration_id'], user_id)


def get_registration_by_id(db, registration_id):
    """Get a registration by ID with event and user details."""
    return db.execute(
        '''SELECT r.*, e.title as event_title, e.start_at as event_start,
                  e.status as event_status, u.full_name as user_name,
                  u.email as user_email, u.student_no
           FROM registrations r
           JOIN events e ON r.event_id = e.event_id
           JOIN users u ON r.user_id = u.user_id
           WHERE r.registration_id = ?''',
        (registration_id,)
    ).fetchone()


def get_user_registrations(db, user_id):
    """Get all registrations for a user with event details."""
    return db.execute(
        '''SELECT r.*, e.title as event_title, e.start_at as event_start,
                  e.end_at as event_end, e.venue, e.status as event_status,
                  o.name as organization_name
           FROM registrations r
           JOIN events e ON r.event_id = e.event_id
           JOIN organizations o ON e.organization_id = o.organization_id
           WHERE r.user_id = ?
           ORDER BY r.registered_at DESC''',
        (user_id,)
    ).fetchall()


def get_event_registrations(db, event_id):
    """Get all registrations for an event with user details and attendance."""
    return db.execute(
        '''SELECT r.*, u.full_name, u.email, u.student_no,
                  a.attendance_status, a.marked_at as attendance_marked_at
           FROM registrations r
           JOIN users u ON r.user_id = u.user_id
           LEFT JOIN attendance a ON r.registration_id = a.registration_id
           WHERE r.event_id = ?
           ORDER BY u.full_name''',
        (event_id,)
    ).fetchall()


def get_user_registrations_paginated(db, user_id, page=1, per_page=20):
    """Get a user's registrations with pagination."""
    count = db.execute(
        'SELECT COUNT(*) FROM registrations WHERE user_id = ?', (user_id,)
    ).fetchone()[0]

    offset = (page - 1) * per_page
    registrations = db.execute(
        '''SELECT r.*, e.title as event_title, e.start_at as event_start,
                  e.end_at as event_end, e.venue, e.status as event_status,
                  o.name as organization_name
           FROM registrations r
           JOIN events e ON r.event_id = e.event_id
           JOIN organizations o ON e.organization_id = o.organization_id
           WHERE r.user_id = ?
           ORDER BY r.registered_at DESC
           LIMIT ? OFFSET ?''',
        (user_id, per_page, offset)
    ).fetchall()

    return registrations, count

"""
Event management service.
Handles CRUD operations and status management for events.
"""
from datetime import datetime


def create_event(db, organization_id, created_by, title, description, venue,
                 start_at, end_at, registration_deadline, capacity):
    """Create a new event in draft status. Returns the new event_id."""
    cursor = db.execute(
        '''INSERT INTO events (organization_id, created_by, title, description, venue,
                               start_at, end_at, registration_deadline, capacity, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft')''',
        (organization_id, created_by, title, description, venue,
         start_at, end_at or None, registration_deadline, capacity)
    )
    db.commit()
    return cursor.lastrowid


def update_event(db, event_id, title, description, venue, start_at, end_at,
                 registration_deadline, capacity):
    """Update event details. Only allowed for draft events (enforced in routes)."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db.execute(
        '''UPDATE events SET title = ?, description = ?, venue = ?, start_at = ?,
               end_at = ?, registration_deadline = ?, capacity = ?, updated_at = ?
           WHERE event_id = ?''',
        (title, description, venue, start_at, end_at or None,
         registration_deadline, capacity, now, event_id)
    )
    db.commit()


def get_event_by_id(db, event_id):
    """Retrieve a single event by ID, including organization name."""
    return db.execute(
        '''SELECT e.*, o.name as organization_name
           FROM events e
           JOIN organizations o ON e.organization_id = o.organization_id
           WHERE e.event_id = ?''',
        (event_id,)
    ).fetchone()


def update_event_status(db, event_id, new_status):
    """Update the status of an event."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db.execute(
        'UPDATE events SET status = ?, updated_at = ? WHERE event_id = ?',
        (new_status, now, event_id)
    )
    db.commit()


def get_officer_events(db, user_id, search=None, status=None, org_id=None,
                       page=1, per_page=20):
    """Get events for organizations where the user is an officer/president."""
    query = '''SELECT e.*, o.name as organization_name,
                      (SELECT COUNT(*) FROM registrations r
                       WHERE r.event_id = e.event_id AND r.status = 'registered') AS reg_count
               FROM events e
               JOIN organizations o ON e.organization_id = o.organization_id
               JOIN organization_members om ON e.organization_id = om.organization_id
               WHERE om.user_id = ? AND om.member_role IN ('officer', 'president')'''
    count_query = '''SELECT COUNT(*)
                     FROM events e
                     JOIN organization_members om ON e.organization_id = om.organization_id
                     WHERE om.user_id = ? AND om.member_role IN ('officer', 'president')'''
    params = [user_id]
    count_params = [user_id]

    if search:
        query += ' AND (e.title LIKE ? OR e.description LIKE ?)'
        count_query += ' AND (e.title LIKE ? OR e.description LIKE ?)'
        s = f'%{search}%'
        params.extend([s, s])
        count_params.extend([s, s])

    if status:
        query += ' AND e.status = ?'
        count_query += ' AND e.status = ?'
        params.append(status)
        count_params.append(status)

    if org_id:
        query += ' AND e.organization_id = ?'
        count_query += ' AND e.organization_id = ?'
        params.append(org_id)
        count_params.append(org_id)

    total = db.execute(count_query, count_params).fetchone()[0]

    query += ' ORDER BY e.created_at DESC LIMIT ? OFFSET ?'
    offset = (page - 1) * per_page
    params.extend([per_page, offset])

    events = db.execute(query, params).fetchall()
    return events, total


def get_published_events(db, search=None, org_id=None, page=1, per_page=20):
    """Get published events from active organizations for students to browse."""
    query = '''SELECT e.*, o.name as organization_name
               FROM events e
               JOIN organizations o ON e.organization_id = o.organization_id
               WHERE e.status = 'published' AND o.is_active = 1'''
    count_query = '''SELECT COUNT(*)
                     FROM events e
                     JOIN organizations o ON e.organization_id = o.organization_id
                     WHERE e.status = 'published' AND o.is_active = 1'''
    params = []
    count_params = []

    if search:
        query += ' AND (e.title LIKE ? OR e.description LIKE ?)'
        count_query += ' AND (e.title LIKE ? OR e.description LIKE ?)'
        s = f'%{search}%'
        params.extend([s, s])
        count_params.extend([s, s])

    if org_id:
        query += ' AND e.organization_id = ?'
        count_query += ' AND e.organization_id = ?'
        params.append(int(org_id))
        count_params.append(int(org_id))

    total = db.execute(count_query, count_params).fetchone()[0]

    query += ' ORDER BY e.start_at ASC LIMIT ? OFFSET ?'
    offset = (page - 1) * per_page
    params.extend([per_page, offset])

    events = db.execute(query, params).fetchall()
    return events, total


def get_all_events(db, search=None, status=None, org_id=None, page=1, per_page=20):
    """Get all events (for admin). Returns (events, total_count)."""
    query = '''SELECT e.*, o.name as organization_name
               FROM events e
               JOIN organizations o ON e.organization_id = o.organization_id
               WHERE 1=1'''
    count_query = '''SELECT COUNT(*)
                     FROM events e
                     JOIN organizations o ON e.organization_id = o.organization_id
                     WHERE 1=1'''
    params = []
    count_params = []

    if search:
        query += ' AND (e.title LIKE ? OR e.description LIKE ?)'
        count_query += ' AND (e.title LIKE ? OR e.description LIKE ?)'
        s = f'%{search}%'
        params.extend([s, s])
        count_params.extend([s, s])

    if status:
        query += ' AND e.status = ?'
        count_query += ' AND e.status = ?'
        params.append(status)
        count_params.append(status)

    if org_id:
        query += ' AND e.organization_id = ?'
        count_query += ' AND e.organization_id = ?'
        params.append(int(org_id))
        count_params.append(int(org_id))

    total = db.execute(count_query, count_params).fetchone()[0]

    query += ' ORDER BY e.created_at DESC LIMIT ? OFFSET ?'
    offset = (page - 1) * per_page
    params.extend([per_page, offset])

    events = db.execute(query, params).fetchall()
    return events, total


def get_officer_organizations(db, user_id):
    """Get organizations where user is officer or president."""
    return db.execute(
        '''SELECT o.* FROM organizations o
           JOIN organization_members om ON o.organization_id = om.organization_id
           WHERE om.user_id = ? AND om.member_role IN ('officer', 'president')
           AND o.is_active = 1
           ORDER BY o.name''',
        (user_id,)
    ).fetchall()


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


def validate_event_dates(start_at, end_at, registration_deadline):
    """Validate event date ordering. Returns error message or None."""
    start = parse_dt(start_at)
    if not start:
        return 'Invalid start date format.'

    if end_at:
        end = parse_dt(end_at)
        if not end:
            return 'Invalid end date format.'
        if end <= start:
            return 'End date must be after start date.'

    deadline = parse_dt(registration_deadline)
    if not deadline:
        return 'Invalid registration deadline format.'

    if deadline > start:
        return 'Registration deadline must not be later than the event start date.'

    return None


def format_datetime_for_storage(dt_str):
    """Convert datetime input to storage format (YYYY-MM-DD HH:MM:SS)."""
    if not dt_str:
        return None
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            dt = datetime.strptime(dt_str, fmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue
    return dt_str


def format_datetime_for_input(dt_str):
    """Convert storage format to datetime-local input format (YYYY-MM-DDTHH:MM) for HTML forms."""
    if not dt_str:
        return ''
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'):
        try:
            dt = datetime.strptime(dt_str, fmt)
            return dt.strftime('%Y-%m-%dT%H:%M')
        except ValueError:
            continue
    return dt_str

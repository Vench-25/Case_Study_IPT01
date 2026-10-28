"""
Report service.
Generates reports and CSV export data for events and organizations.
"""
import csv
import io
import re
from datetime import datetime


def get_admin_dashboard_stats(db):
    """Get summary statistics for the admin dashboard."""
    stats = {}
    stats['total_users'] = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    stats['active_users'] = db.execute("SELECT COUNT(*) FROM users WHERE is_active = 1").fetchone()[0]
    stats['total_organizations'] = db.execute('SELECT COUNT(*) FROM organizations').fetchone()[0]
    stats['active_organizations'] = db.execute("SELECT COUNT(*) FROM organizations WHERE is_active = 1").fetchone()[0]
    stats['total_events'] = db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
    stats['published_events'] = db.execute("SELECT COUNT(*) FROM events WHERE status = 'published'").fetchone()[0]
    stats['total_registrations'] = db.execute("SELECT COUNT(*) FROM registrations WHERE status = 'registered'").fetchone()[0]


    stats['recent_activity'] = db.execute(
        '''SELECT al.*, u.full_name
           FROM audit_log al
           LEFT JOIN users u ON al.user_id = u.user_id
           ORDER BY al.created_at DESC LIMIT 10'''
    ).fetchall()


    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    stats['upcoming_events'] = db.execute(
        '''SELECT e.*, o.name as organization_name
           FROM events e
           JOIN organizations o ON e.organization_id = o.organization_id
           WHERE e.status = 'published' AND e.start_at > ?
           ORDER BY e.start_at ASC LIMIT 5''',
        (now,)
    ).fetchall()

    return stats


def get_officer_dashboard_stats(db, user_id):
    """Get summary statistics for an officer's dashboard."""
    stats = {}
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


    stats['upcoming_events'] = db.execute(
        '''SELECT COUNT(*)
           FROM events e
           JOIN organization_members om ON e.organization_id = om.organization_id
           WHERE om.user_id = ? AND om.member_role IN ('officer', 'president')
           AND e.status = 'published' AND e.start_at > ?''',
        (user_id, now)
    ).fetchone()[0]

    stats['total_events'] = db.execute(
        '''SELECT COUNT(*)
           FROM events e
           JOIN organization_members om ON e.organization_id = om.organization_id
           WHERE om.user_id = ? AND om.member_role IN ('officer', 'president')''',
        (user_id,)
    ).fetchone()[0]

    stats['active_registrations'] = db.execute(
        '''SELECT COUNT(*)
           FROM registrations reg
           JOIN events e ON reg.event_id = e.event_id
           JOIN organization_members om ON e.organization_id = om.organization_id
           WHERE om.user_id = ? AND om.member_role IN ('officer', 'president')
           AND reg.status = 'registered' AND e.status = 'published' ''',
        (user_id,)
    ).fetchone()[0]

    stats['draft_events'] = db.execute(
        '''SELECT COUNT(*)
           FROM events e
           JOIN organization_members om ON e.organization_id = om.organization_id
           WHERE om.user_id = ? AND om.member_role IN ('officer', 'president')
           AND e.status = 'draft' ''',
        (user_id,)
    ).fetchone()[0]


    stats['recent_events'] = db.execute(
        '''SELECT e.*, o.name as organization_name,
                  (SELECT COUNT(*) FROM registrations r WHERE r.event_id = e.event_id AND r.status = 'registered') as reg_count
           FROM events e
           JOIN organizations o ON e.organization_id = o.organization_id
           JOIN organization_members om ON e.organization_id = om.organization_id
           WHERE om.user_id = ? AND om.member_role IN ('officer', 'president')
           ORDER BY e.created_at DESC LIMIT 5''',
        (user_id,)
    ).fetchall()

    return stats


def get_student_dashboard_stats(db, user_id):
    """Get summary statistics for a student's dashboard."""
    stats = {}
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    stats['active_registrations'] = db.execute(
        '''SELECT COUNT(*) FROM registrations r
           JOIN events e ON r.event_id = e.event_id
           WHERE r.user_id = ? AND r.status = 'registered' AND e.status = 'published' ''',
        (user_id,)
    ).fetchone()[0]

    stats['total_registrations'] = db.execute(
        'SELECT COUNT(*) FROM registrations WHERE user_id = ?', (user_id,)
    ).fetchone()[0]

    stats['events_attended'] = db.execute(
        '''SELECT COUNT(*) FROM attendance a
           JOIN registrations r ON a.registration_id = r.registration_id
           WHERE r.user_id = ? AND a.attendance_status = 'present' ''',
        (user_id,)
    ).fetchone()[0]


    stats['upcoming_events'] = db.execute(
        '''SELECT e.*, o.name as organization_name, r.status as reg_status
           FROM registrations r
           JOIN events e ON r.event_id = e.event_id
           JOIN organizations o ON e.organization_id = o.organization_id
           WHERE r.user_id = ? AND r.status = 'registered'
           AND e.status = 'published' AND e.start_at > ?
           ORDER BY e.start_at ASC LIMIT 5''',
        (user_id, now)
    ).fetchall()

    return stats


def get_event_report(db, event_id):
    """Generate a detailed report for a single event."""
    event = db.execute(
        '''SELECT e.*, o.name as organization_name
           FROM events e
           JOIN organizations o ON e.organization_id = o.organization_id
           WHERE e.event_id = ?''',
        (event_id,)
    ).fetchone()

    if not event:
        return None

    report = dict(event)


    reg_stats = db.execute(
        '''SELECT
               COUNT(CASE WHEN status = 'registered' THEN 1 END) as registered_count,
               COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_count
           FROM registrations WHERE event_id = ?''',
        (event_id,)
    ).fetchone()
    report['registered_count'] = reg_stats['registered_count']
    report['cancelled_count'] = reg_stats['cancelled_count']


    att_stats = db.execute(
        '''SELECT
               COUNT(CASE WHEN a.attendance_status = 'present' THEN 1 END) as present_count,
               COUNT(CASE WHEN a.attendance_status = 'absent' THEN 1 END) as absent_count,
               COUNT(CASE WHEN r.status = 'registered' AND a.attendance_id IS NULL THEN 1 END) as unmarked_count
           FROM registrations r
           LEFT JOIN attendance a ON r.registration_id = a.registration_id
           WHERE r.event_id = ?''',
        (event_id,)
    ).fetchone()
    report['present_count'] = att_stats['present_count']
    report['absent_count'] = att_stats['absent_count']
    report['unmarked_count'] = att_stats['unmarked_count']

    return report


def sanitize_csv_field(value):
    """Sanitize a field to prevent CSV/spreadsheet formula injection."""
    if value is None:
        return ''
    s = str(value)

    if s and s[0] in ('=', '+', '-', '@', '\t', '\r'):
        s = "'" + s
    return s


def get_event_participants_csv(db, event_id):
    """Generate CSV data for event participants."""
    participants = db.execute(
        '''SELECT u.student_no, u.full_name, u.email,
                  r.status as registration_status, r.registered_at,
                  a.attendance_status
           FROM registrations r
           JOIN users u ON r.user_id = u.user_id
           LEFT JOIN attendance a ON r.registration_id = a.registration_id
           WHERE r.event_id = ?
           ORDER BY u.full_name''',
        (event_id,)
    ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student No', 'Full Name', 'Email', 'Registration Status',
                     'Registered At', 'Attendance Status'])

    for p in participants:
        writer.writerow([
            sanitize_csv_field(p['student_no']),
            sanitize_csv_field(p['full_name']),
            sanitize_csv_field(p['email']),
            sanitize_csv_field(p['registration_status']),
            sanitize_csv_field(p['registered_at']),
            sanitize_csv_field(p['attendance_status'] or 'Not Marked')
        ])

    return output.getvalue()


def get_admin_reports(db, org_id=None, date_from=None, date_to=None):
    """Get event reports for admin, optionally filtered."""
    query = '''SELECT e.event_id, e.title, e.start_at, e.status, e.capacity,
                      o.name as organization_name,
                      COUNT(CASE WHEN r.status = 'registered' THEN 1 END) as registered_count,
                      COUNT(CASE WHEN a.attendance_status = 'present' THEN 1 END) as present_count,
                      COUNT(CASE WHEN a.attendance_status = 'absent' THEN 1 END) as absent_count,
                      COUNT(CASE WHEN r.status = 'registered' AND a.attendance_id IS NULL THEN 1 END) as unmarked_count
               FROM events e
               JOIN organizations o ON e.organization_id = o.organization_id
               LEFT JOIN registrations r ON e.event_id = r.event_id
               LEFT JOIN attendance a ON r.registration_id = a.registration_id
               WHERE 1=1'''
    params = []

    if org_id:
        query += ' AND e.organization_id = ?'
        params.append(int(org_id))

    if date_from:
        query += ' AND e.start_at >= ?'
        params.append(date_from)

    if date_to:
        query += ' AND e.start_at <= ?'
        params.append(date_to + ' 23:59:59')

    query += ' GROUP BY e.event_id ORDER BY e.start_at DESC'

    return db.execute(query, params).fetchall()


def get_officer_reports(db, user_id, org_id=None, date_from=None, date_to=None):
    """Get event reports for officer, restricted to their organizations."""
    query = '''SELECT e.event_id, e.title, e.start_at, e.status, e.capacity,
                      o.name as organization_name,
                      COUNT(CASE WHEN r.status = 'registered' THEN 1 END) as registered_count,
                      COUNT(CASE WHEN a.attendance_status = 'present' THEN 1 END) as present_count,
                      COUNT(CASE WHEN a.attendance_status = 'absent' THEN 1 END) as absent_count,
                      COUNT(CASE WHEN r.status = 'registered' AND a.attendance_id IS NULL THEN 1 END) as unmarked_count
               FROM events e
               JOIN organizations o ON e.organization_id = o.organization_id
               JOIN organization_members om ON e.organization_id = om.organization_id
               LEFT JOIN registrations r ON e.event_id = r.event_id
               LEFT JOIN attendance a ON r.registration_id = a.registration_id
               WHERE om.user_id = ? AND om.member_role IN ('officer', 'president')'''
    params = [user_id]

    if org_id:
        query += ' AND e.organization_id = ?'
        params.append(int(org_id))

    if date_from:
        query += ' AND e.start_at >= ?'
        params.append(date_from)

    if date_to:
        query += ' AND e.start_at <= ?'
        params.append(date_to + ' 23:59:59')

    query += ' GROUP BY e.event_id ORDER BY e.start_at DESC'

    return db.execute(query, params).fetchall()


def get_audit_log(db, user_id=None, action=None, page=1, per_page=50):
    """Get audit log entries with optional filtering and pagination."""
    query = '''SELECT al.*, u.full_name
               FROM audit_log al
               LEFT JOIN users u ON al.user_id = u.user_id
               WHERE 1=1'''
    count_query = 'SELECT COUNT(*) FROM audit_log al WHERE 1=1'
    params = []
    count_params = []

    if user_id:
        query += ' AND al.user_id = ?'
        count_query += ' AND al.user_id = ?'
        params.append(user_id)
        count_params.append(user_id)

    if action:
        query += ' AND al.action = ?'
        count_query += ' AND al.action = ?'
        params.append(action)
        count_params.append(action)

    total = db.execute(count_query, count_params).fetchone()[0]

    query += ' ORDER BY al.created_at DESC LIMIT ? OFFSET ?'
    offset = (page - 1) * per_page
    params.extend([per_page, offset])

    logs = db.execute(query, params).fetchall()
    return logs, total

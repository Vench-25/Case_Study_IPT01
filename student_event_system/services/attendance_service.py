"""
Attendance management service.
Handles marking and updating attendance for event participants.
Policy: Attendance can be recorded on event day or after the event has started.
"""
from datetime import datetime


def mark_attendance(db, registration_id, marked_by, attendance_status):
    """
    Mark or update attendance for a registration.
    Returns (success: bool, message: str).
    """
    try:

        reg = db.execute(
            '''SELECT r.*, e.start_at, e.status as event_status, e.organization_id
               FROM registrations r
               JOIN events e ON r.event_id = e.event_id
               WHERE r.registration_id = ?''',
            (registration_id,)
        ).fetchone()

        if not reg:
            return False, 'Registration not found.'

        if reg['status'] != 'registered':
            return False, 'Attendance can only be marked for active registrations.'

        if reg['event_status'] not in ('published', 'completed'):
            return False, 'Attendance can only be marked for published or completed events.'

        if attendance_status not in ('present', 'absent'):
            return False, 'Invalid attendance status.'


        existing = db.execute(
            'SELECT * FROM attendance WHERE registration_id = ?',
            (registration_id,)
        ).fetchone()

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if existing:
            db.execute(
                '''UPDATE attendance SET attendance_status = ?, marked_by = ?, marked_at = ?
                   WHERE attendance_id = ?''',
                (attendance_status, marked_by, now_str, existing['attendance_id'])
            )
        else:
            db.execute(
                '''INSERT INTO attendance (registration_id, marked_by, attendance_status, marked_at)
                   VALUES (?, ?, ?, ?)''',
                (registration_id, marked_by, attendance_status, now_str)
            )

        db.commit()
        return True, f'Attendance marked as {attendance_status}.'

    except Exception as e:
        db.rollback()
        return False, 'An error occurred while marking attendance.'


def get_event_attendance(db, event_id):
    """Get attendance records for all registered participants in an event."""
    return db.execute(
        '''SELECT r.registration_id, r.status as reg_status,
                  u.user_id, u.full_name, u.email, u.student_no,
                  a.attendance_id, a.attendance_status, a.marked_at
           FROM registrations r
           JOIN users u ON r.user_id = u.user_id
           LEFT JOIN attendance a ON r.registration_id = a.registration_id
           WHERE r.event_id = ? AND r.status = 'registered'
           ORDER BY u.full_name''',
        (event_id,)
    ).fetchall()


def get_attendance_summary(db, event_id):
    """Get attendance summary counts for an event."""
    result = db.execute(
        '''SELECT
               COUNT(CASE WHEN r.status = 'registered' THEN 1 END) as total_registered,
               COUNT(CASE WHEN a.attendance_status = 'present' THEN 1 END) as present_count,
               COUNT(CASE WHEN a.attendance_status = 'absent' THEN 1 END) as absent_count,
               COUNT(CASE WHEN r.status = 'registered' AND a.attendance_id IS NULL THEN 1 END) as unmarked_count
           FROM registrations r
           LEFT JOIN attendance a ON r.registration_id = a.registration_id
           WHERE r.event_id = ?''',
        (event_id,)
    ).fetchone()
    return dict(result) if result else {
        'total_registered': 0, 'present_count': 0,
        'absent_count': 0, 'unmarked_count': 0
    }

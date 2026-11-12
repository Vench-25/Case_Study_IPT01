"""
Report service.
Generates formatted Excel reports for events and organization reporting.
"""
import io
import re
from datetime import datetime
import xlsxwriter


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


def get_event_participants(db, event_id):
    """Get registration and attendance details for every event participant."""
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
    return participants


def get_event_participants_xlsx(db, event, attendance_summary):
    """Create a formatted Excel participant and attendance report."""
    participants = get_event_participants(db, event['event_id'])
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(
        output, {'in_memory': True, 'strings_to_formulas': False}
    )
    worksheet = workbook.add_worksheet('Participants')
    worksheet.hide_gridlines(2)
    worksheet.set_tab_color('#217A68')

    title_format = workbook.add_format({
        'bold': True, 'font_size': 22, 'font_color': '#FFFFFF',
        'bg_color': '#17324D', 'valign': 'vcenter', 'left': 1
    })
    subtitle_format = workbook.add_format({
        'font_size': 11, 'font_color': '#DCE7EF',
        'bg_color': '#17324D', 'valign': 'vcenter'
    })
    metadata_label_format = workbook.add_format({
        'bold': True, 'font_color': '#526579', 'bg_color': '#EEF3F7',
        'border': 1, 'border_color': '#D8E1E8', 'valign': 'vcenter'
    })
    metadata_value_format = workbook.add_format({
        'font_color': '#17324D', 'bg_color': '#FFFFFF',
        'border': 1, 'border_color': '#D8E1E8', 'valign': 'vcenter'
    })
    metric_label_format = workbook.add_format({
        'bold': True, 'font_size': 9, 'font_color': '#FFFFFF',
        'bg_color': '#217A68', 'align': 'center', 'valign': 'vcenter',
        'text_wrap': True
    })
    metric_value_format = workbook.add_format({
        'bold': True, 'font_size': 16, 'font_color': '#17324D',
        'bg_color': '#EAF4F1', 'align': 'center', 'valign': 'vcenter',
        'num_format': '0.0%'
    })
    metric_count_format = workbook.add_format({
        'bold': True, 'font_size': 16, 'font_color': '#17324D',
        'bg_color': '#EAF4F1', 'align': 'center', 'valign': 'vcenter'
    })
    section_format = workbook.add_format({
        'bold': True, 'font_size': 11, 'font_color': '#17324D',
        'bg_color': '#EEF3F7', 'valign': 'vcenter'
    })
    header_format = workbook.add_format({
        'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#17324D',
        'border': 1, 'border_color': '#FFFFFF', 'valign': 'vcenter',
        'text_wrap': True
    })
    even_row_format = workbook.add_format({
        'font_color': '#243746', 'bg_color': '#F5F8FA',
        'bottom': 1, 'bottom_color': '#E1E8ED', 'valign': 'top'
    })
    odd_row_format = workbook.add_format({
        'font_color': '#243746', 'bg_color': '#FFFFFF',
        'bottom': 1, 'bottom_color': '#E1E8ED', 'valign': 'top'
    })
    date_format = workbook.add_format({
        'font_color': '#243746', 'bg_color': '#FFFFFF',
        'num_format': 'mmm d, yyyy h:mm AM/PM',
        'bottom': 1, 'bottom_color': '#E1E8ED', 'valign': 'top'
    })
    registration_status_formats = {
        'registered': workbook.add_format({
            'font_color': '#17633A', 'bg_color': '#E7F4EC',
            'bottom': 1, 'bottom_color': '#E1E8ED'
        }),
        'cancelled': workbook.add_format({
            'font_color': '#5F6B76', 'bg_color': '#EDF0F2',
            'bottom': 1, 'bottom_color': '#E1E8ED'
        })
    }
    attendance_status_formats = {
        'present': workbook.add_format({
            'font_color': '#17633A', 'bg_color': '#E7F4EC',
            'bottom': 1, 'bottom_color': '#E1E8ED'
        }),
        'absent': workbook.add_format({
            'font_color': '#9B2C2C', 'bg_color': '#FCE8E6',
            'bottom': 1, 'bottom_color': '#E1E8ED'
        }),
        'not marked': workbook.add_format({
            'font_color': '#526579', 'bg_color': '#EDF0F2',
            'bottom': 1, 'bottom_color': '#E1E8ED'
        })
    }

    worksheet.set_column('A:A', 20)
    worksheet.set_column('B:B', 28)
    worksheet.set_column('C:C', 34)
    worksheet.set_column('D:D', 21)
    worksheet.set_column('E:E', 24)
    worksheet.set_column('F:F', 21)
    worksheet.set_row(0, 38)
    worksheet.set_row(1, 23)

    worksheet.merge_range(0, 0, 0, 5, event['title'], title_format)
    worksheet.merge_range(
        1, 0, 1, 5,
        f"{event['organization_name']}  |  PARTICIPANT & ATTENDANCE REPORT",
        subtitle_format
    )

    worksheet.write(3, 0, 'Organization', metadata_label_format)
    worksheet.merge_range(3, 1, 3, 2, event['organization_name'], metadata_value_format)
    worksheet.write(3, 3, 'Venue', metadata_label_format)
    worksheet.merge_range(3, 4, 3, 5, event['venue'], metadata_value_format)
    worksheet.write(4, 0, 'Event schedule', metadata_label_format)
    schedule = f"{event['start_at']} to {event['end_at'] or 'Not specified'}"
    worksheet.merge_range(4, 1, 4, 2, schedule, metadata_value_format)
    worksheet.write(4, 3, 'Generated', metadata_label_format)
    worksheet.merge_range(
        4, 4, 4, 5, datetime.now(), workbook.add_format({
            'font_color': '#17324D', 'bg_color': '#FFFFFF',
            'border': 1, 'border_color': '#D8E1E8',
            'num_format': 'mmm d, yyyy h:mm AM/PM'
        })
    )

    registered_count = sum(p['registration_status'] == 'registered' for p in participants)
    cancelled_count = sum(p['registration_status'] == 'cancelled' for p in participants)
    metrics = [
        ('ACTIVE REGISTRANTS', registered_count, False),
        ('CANCELLED', cancelled_count, False),
        ('PRESENT', attendance_summary['present_count'], False),
        ('ABSENT', attendance_summary['absent_count'], False),
        ('NOT MARKED', attendance_summary['unmarked_count'], False),
        (
            'ATTENDANCE RATE',
            attendance_summary['present_count'] / registered_count if registered_count else 0,
            True
        )
    ]
    for column, (label, value, is_percentage) in enumerate(metrics):
        worksheet.write(6, column, label, metric_label_format)
        worksheet.write(
            7, column, value,
            metric_value_format if is_percentage else metric_count_format
        )
    worksheet.set_row(6, 26)
    worksheet.set_row(7, 32)

    table_header_row = 9
    worksheet.merge_range(table_header_row - 1, 0, table_header_row - 1, 5,
                          'PARTICIPANT ROSTER', section_format)
    headers = [
        'Student No', 'Full Name', 'Email', 'Registration Status',
        'Registered At', 'Attendance Status'
    ]
    for column, header in enumerate(headers):
        worksheet.write(table_header_row, column, header, header_format)
    worksheet.set_row(table_header_row, 30)

    for participant_index, p in enumerate(participants):
        row = table_header_row + 1 + participant_index
        base_format = even_row_format if (row - table_header_row) % 2 else odd_row_format
        for column, value in enumerate((p['student_no'], p['full_name'], p['email'])):
            worksheet.write_string(row, column, str(value or ''), base_format)

        registration_status = p['registration_status'] or ''
        worksheet.write_string(
            row, 3, registration_status.title(),
            registration_status_formats.get(registration_status, base_format)
        )

        try:
            registered_at = datetime.strptime(p['registered_at'], '%Y-%m-%d %H:%M:%S')
            worksheet.write_datetime(row, 4, registered_at, date_format)
        except (TypeError, ValueError):
            worksheet.write_string(row, 4, str(p['registered_at'] or ''), base_format)

        attendance_status = (p['attendance_status'] or 'Not Marked').title()
        worksheet.write_string(
            row, 5, attendance_status,
            attendance_status_formats.get(attendance_status.lower(), base_format)
        )

    last_row = table_header_row + len(participants)
    worksheet.autofilter(table_header_row, 0, last_row, len(headers) - 1)
    worksheet.freeze_panes(table_header_row + 1, 0)
    worksheet.set_landscape()
    worksheet.fit_to_pages(1, 0)
    worksheet.repeat_rows(table_header_row)
    worksheet.set_margins(0.3, 0.3, 0.5, 0.5)
    worksheet.set_footer('&LConfidential — For authorized event use&CPage &P of &N')
    worksheet.print_area(0, 0, last_row, len(headers) - 1)

    workbook.close()
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

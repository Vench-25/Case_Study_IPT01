"""
Organization officer routes for NEUST–TOC Student Event System.
"""
from functools import wraps
from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, session, abort, Response)
from db import get_db
from services import (auth_service, event_service, registration_service,
                      attendance_service, report_service)

officer_bp = Blueprint('officer', __name__, url_prefix='/officer')


def officer_required(f):
    """Decorator to require an active officer or administrator account."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') not in ('officer', 'admin'):
            abort(403)
        db = get_db()
        user = auth_service.get_user_by_id(db, session['user_id'])
        if not user or not user['is_active']:
            session.clear()
            flash('Your account has been deactivated.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def check_event_authorization(db, event_id, user_id):
    """Verify officer is authorized for the event's organization."""
    event = event_service.get_event_by_id(db, event_id)
    if not event:
        abort(404)
    if session.get('role') == 'admin':
        return event
    if not auth_service.is_officer_of_organization(db, user_id, event['organization_id']):
        abort(403)
    return event


@officer_bp.route('/dashboard')
@officer_required
def dashboard():
    db = get_db()
    stats = report_service.get_officer_dashboard_stats(db, session['user_id'])
    return render_template('officer/dashboard.html', stats=stats)


@officer_bp.route('/events')
@officer_required
def events():
    db = get_db()
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    org_id = request.args.get('org_id', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    events_list, total = event_service.get_officer_events(
        db,
        session['user_id'],
        search=search or None,
        status=status or None,
        org_id=int(org_id) if org_id else None,
        page=page,
        per_page=per_page
    )
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    orgs = event_service.get_officer_organizations(db, session['user_id'])
    return render_template(
        'officer/events.html',
        events=events_list,
        organizations=orgs,
        search=search,
        status=status,
        org_id=org_id,
        page=page,
        total_pages=total_pages,
        total=total
    )


@officer_bp.route('/events/new', methods=['GET', 'POST'])
@officer_required
def event_new():
    db = get_db()
    orgs = event_service.get_officer_organizations(db, session['user_id'])

    if not orgs and session.get('role') != 'admin':
        flash('You are not currently assigned as an officer to any organization.', 'warning')
        return redirect(url_for('officer.dashboard'))

    if session.get('role') == 'admin' and not orgs:
        orgs, _ = auth_service.get_all_organizations(db, per_page=100)

    if request.method == 'POST':
        organization_id = request.form.get('organization_id', type=int)
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        venue = request.form.get('venue', '').strip()
        start_at = request.form.get('start_at', '').strip()
        end_at = request.form.get('end_at', '').strip() or None
        registration_deadline = request.form.get('registration_deadline', '').strip()
        capacity = request.form.get('capacity', type=int)

        errors = []
        if not organization_id:
            errors.append('Please select an organization.')
        elif session.get('role') != 'admin' and not auth_service.is_officer_of_organization(db, session['user_id'], organization_id):
            errors.append('You are not authorized for the selected organization.')

        if not title:
            errors.append('Event title is required.')
        if not description:
            errors.append('Event description is required.')
        if not venue:
            errors.append('Event venue is required.')
        if not start_at:
            errors.append('Start date and time is required.')
        if not registration_deadline:
            errors.append('Registration deadline is required.')
        if not capacity or capacity < 1:
            errors.append('Capacity must be a positive number greater than 0.')

        if start_at and registration_deadline:
            date_err = event_service.validate_event_dates(start_at, end_at, registration_deadline)
            if date_err:
                errors.append(date_err)

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template(
                'officer/event_form.html',
                action='new',
                organizations=orgs,
                organization_id=organization_id,
                title=title,
                description=description,
                venue=venue,
                start_at=start_at,
                end_at=end_at or '',
                registration_deadline=registration_deadline,
                capacity=capacity
            ), 200

        try:
            start_stored = event_service.format_datetime_for_storage(start_at)
            end_stored = event_service.format_datetime_for_storage(end_at) if end_at else None
            deadline_stored = event_service.format_datetime_for_storage(registration_deadline)

            event_id = event_service.create_event(
                db, organization_id, session['user_id'], title, description,
                venue, start_stored, end_stored, deadline_stored, capacity
            )
            auth_service.log_audit(db, session['user_id'], 'event_created',
                                   'event', event_id, f'Created draft: {title}')
            flash(f'Event "{title}" created as draft. You can publish it when ready.', 'success')
            return redirect(url_for('officer.events'))
        except Exception:
            flash('An error occurred while creating the event.', 'danger')

    return render_template('officer/event_form.html', action='new', organizations=orgs)


@officer_bp.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@officer_required
def event_edit(event_id):
    db = get_db()
    event = check_event_authorization(db, event_id, session['user_id'])

    if event['status'] not in ('draft', 'published'):
        flash('Only draft or published events can be edited.', 'warning')
        return redirect(url_for('officer.events'))

    orgs = event_service.get_officer_organizations(db, session['user_id'])
    if session.get('role') == 'admin':
        orgs, _ = auth_service.get_all_organizations(db, per_page=100)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        venue = request.form.get('venue', '').strip()
        start_at = request.form.get('start_at', '').strip()
        end_at = request.form.get('end_at', '').strip() or None
        registration_deadline = request.form.get('registration_deadline', '').strip()
        capacity = request.form.get('capacity', type=int)

        errors = []
        if not title:
            errors.append('Event title is required.')
        if not description:
            errors.append('Event description is required.')
        if not venue:
            errors.append('Event venue is required.')
        if not start_at:
            errors.append('Start date and time is required.')
        if not registration_deadline:
            errors.append('Registration deadline is required.')
        if not capacity or capacity < 1:
            errors.append('Capacity must be a positive number.')

        if start_at and registration_deadline:
            date_err = event_service.validate_event_dates(start_at, end_at, registration_deadline)
            if date_err:
                errors.append(date_err)

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template(
                'officer/event_form.html',
                action='edit',
                event=event,
                organizations=orgs,
                title=title,
                description=description,
                venue=venue,
                start_at=start_at,
                end_at=end_at or '',
                registration_deadline=registration_deadline,
                capacity=capacity
            ), 200

        try:
            start_stored = event_service.format_datetime_for_storage(start_at)
            end_stored = event_service.format_datetime_for_storage(end_at) if end_at else None
            deadline_stored = event_service.format_datetime_for_storage(registration_deadline)

            event_service.update_event(
                db, event_id, title, description, venue,
                start_stored, end_stored, deadline_stored, capacity
            )
            auth_service.log_audit(db, session['user_id'], 'event_updated',
                                   'event', event_id, f'Updated {title}')
            flash(f'Event "{title}" updated successfully.', 'success')
            return redirect(url_for('officer.events'))
        except Exception:
            flash('An error occurred while updating the event.', 'danger')

    return render_template(
        'officer/event_form.html',
        action='edit',
        event=event,
        organizations=orgs,
        title=event['title'],
        description=event['description'],
        venue=event['venue'],
        start_at=event_service.format_datetime_for_input(event['start_at']),
        end_at=event_service.format_datetime_for_input(event['end_at']),
        registration_deadline=event_service.format_datetime_for_input(event['registration_deadline']),
        capacity=event['capacity']
    )


@officer_bp.route('/events/<int:event_id>/publish', methods=['POST'])
@officer_required
def event_publish(event_id):
    db = get_db()
    event = check_event_authorization(db, event_id, session['user_id'])

    if event['status'] != 'draft':
        flash(f'Event "{event["title"]}" is already {event["status"]}. Only draft events can be published.', 'warning')
        return redirect(url_for('officer.events'))

    event_service.update_event_status(db, event_id, 'published')
    auth_service.log_audit(db, session['user_id'], 'event_published',
                           'event', event_id, f'Published: {event["title"]}')
    flash(f'Event "{event["title"]}" has been published and is now open for registration.', 'success')
    return redirect(url_for('officer.events'))


@officer_bp.route('/events/<int:event_id>/cancel', methods=['POST'])
@officer_required
def event_cancel(event_id):
    db = get_db()
    event = check_event_authorization(db, event_id, session['user_id'])

    if event['status'] not in ('draft', 'published'):
        flash(f'This event is {event["status"]} and cannot be cancelled.', 'warning')
        return redirect(url_for('officer.events'))

    event_service.update_event_status(db, event_id, 'cancelled')
    auth_service.log_audit(db, session['user_id'], 'event_cancelled',
                           'event', event_id, f'Cancelled: {event["title"]}')
    flash(f'Event "{event["title"]}" has been cancelled.', 'success')
    return redirect(url_for('officer.events'))


@officer_bp.route('/events/<int:event_id>/complete', methods=['POST'])
@officer_required
def event_complete(event_id):
    db = get_db()
    event = check_event_authorization(db, event_id, session['user_id'])

    if event['status'] != 'published':
        flash('Only published events can be marked as completed.', 'warning')
        return redirect(url_for('officer.events'))

    event_service.update_event_status(db, event_id, 'completed')
    auth_service.log_audit(db, session['user_id'], 'event_completed',
                           'event', event_id, f'Completed: {event["title"]}')
    flash(f'Event "{event["title"]}" has been marked as completed.', 'success')
    return redirect(url_for('officer.events'))


@officer_bp.route('/events/<int:event_id>/participants')
@officer_required
def event_participants(event_id):
    db = get_db()
    event = check_event_authorization(db, event_id, session['user_id'])
    participants = registration_service.get_event_registrations(db, event_id)
    reg_count = registration_service.get_registration_count(db, event_id)
    summary = attendance_service.get_attendance_summary(db, event_id)

    return render_template(
        'officer/participants.html',
        event=event,
        participants=participants,
        reg_count=reg_count,
        summary=summary
    )


@officer_bp.route('/events/<int:event_id>/attendance', methods=['GET', 'POST'])
@officer_required
def event_attendance(event_id):
    db = get_db()
    event = check_event_authorization(db, event_id, session['user_id'])

    if event['status'] not in ('published', 'completed'):
        flash('Attendance can only be managed for published or completed events.', 'warning')
        return redirect(url_for('officer.events'))

    if request.method == 'POST':
        updated = 0
        for key, value in request.form.items():
            if key.startswith('attendance_'):
                try:
                    reg_id = int(key.replace('attendance_', ''))
                    if value in ('present', 'absent'):
                        success, _ = attendance_service.mark_attendance(
                            db, reg_id, session['user_id'], value
                        )
                        if success:
                            updated += 1
                except (ValueError, TypeError):
                    continue

        if updated > 0:
            auth_service.log_audit(
                db, session['user_id'], 'attendance_updated',
                'event', event_id, f'Marked attendance for {updated} participants'
            )
            flash(f'Attendance recorded for {updated} participant(s).', 'success')
        else:
            flash('No attendance changes were submitted.', 'info')

        return redirect(url_for('officer.event_attendance', event_id=event_id))

    attendance_list = attendance_service.get_event_attendance(db, event_id)
    summary = attendance_service.get_attendance_summary(db, event_id)

    return render_template(
        'officer/attendance.html',
        event=event,
        attendance=attendance_list,
        summary=summary
    )


@officer_bp.route('/events/<int:event_id>/report')
@officer_required
def event_report(event_id):
    db = get_db()
    event = check_event_authorization(db, event_id, session['user_id'])
    report_data = report_service.get_event_report(db, event_id)

    if not report_data:
        abort(404)

    participants = registration_service.get_event_registrations(db, event_id)
    summary = attendance_service.get_attendance_summary(db, event_id)

    return render_template(
        'officer/reports.html',
        event=event,
        report=report_data,
        participants=participants,
        summary=summary,
        single_event=True
    )


@officer_bp.route('/events/<int:event_id>/export')
@officer_bp.route('/events/<int:event_id>/export.csv')
@officer_required
def event_export_csv(event_id):
    db = get_db()
    event = check_event_authorization(db, event_id, session['user_id'])
    csv_data = report_service.get_event_participants_csv(db, event_id)

    response = Response(
        '\ufeff' + csv_data,
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename=event_{event_id}_participants.csv'
        }
    )
    return response


@officer_bp.route('/reports')
@officer_required
def reports():
    db = get_db()
    org_id = request.args.get('org_id', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    reports_data = report_service.get_officer_reports(
        db,
        session['user_id'],
        org_id=int(org_id) if org_id else None,
        date_from=date_from or None,
        date_to=date_to or None
    )
    orgs = event_service.get_officer_organizations(db, session['user_id'])

    return render_template(
        'officer/reports.html',
        reports=reports_data,
        organizations=orgs,
        org_id=org_id,
        date_from=date_from,
        date_to=date_to,
        single_event=False
    )

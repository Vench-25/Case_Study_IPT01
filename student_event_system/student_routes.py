"""
Student routes for NEUST–TOC Student Event System.
"""
import re
from datetime import datetime
from functools import wraps
from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, session, abort)
from db import get_db
from services import (auth_service, event_service, registration_service,
                      report_service)

student_bp = Blueprint('student', __name__, url_prefix='/student')


def student_required(f):
    """Decorator to require an active student account."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'student':
            abort(403)
        db = get_db()
        user = auth_service.get_user_by_id(db, session['user_id'])
        if not user or not user['is_active']:
            session.clear()
            flash('Your account has been deactivated.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@student_bp.route('/dashboard')
@student_required
def dashboard():
    db = get_db()
    stats = report_service.get_student_dashboard_stats(db, session['user_id'])
    return render_template('student/dashboard.html', stats=stats)


@student_bp.route('/events')
@student_required
def events():
    db = get_db()
    search = request.args.get('search', '').strip()
    org_id = request.args.get('org_id', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 12

    events_list, total = event_service.get_published_events(
        db,
        search=search or None,
        org_id=int(org_id) if org_id else None,
        page=page,
        per_page=per_page
    )
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    orgs = db.execute(
        'SELECT * FROM organizations WHERE is_active = 1 ORDER BY name'
    ).fetchall()

    events_with_info = []
    for evt in events_list:
        evt_dict = dict(evt)
        evt_dict['reg_count'] = registration_service.get_registration_count(db, evt['event_id'])
        user_reg = registration_service.get_user_event_registration(
            db, evt['event_id'], session['user_id']
        )
        evt_dict['user_registration'] = user_reg
        events_with_info.append(evt_dict)

    return render_template(
        'student/events.html',
        events=events_with_info,
        organizations=orgs,
        search=search,
        org_id=org_id,
        page=page,
        total_pages=total_pages,
        total=total
    )


@student_bp.route('/events/<int:event_id>')
@student_required
def event_detail(event_id):
    db = get_db()
    event = event_service.get_event_by_id(db, event_id)

    if not event or event['status'] != 'published':
        status_name = event['status'] if event else 'unknown'
        flash(f'Cannot view event: Event is {status_name} and not published. Event is not available.', 'warning')
        return redirect(url_for('student.events'))

    org = auth_service.get_organization_by_id(db, event['organization_id'])
    if not org or not org['is_active']:
        flash('Event is not available.', 'warning')
        return redirect(url_for('student.events'))

    reg_count = registration_service.get_registration_count(db, event_id)
    user_reg = registration_service.get_user_event_registration(
        db, event_id, session['user_id']
    )
    available_slots = max(0, event['capacity'] - reg_count)

    now = datetime.now()
    deadline = registration_service.parse_dt(event['registration_deadline'])
    deadline_passed = bool(deadline and now > deadline)

    return render_template(
        'student/event_detail.html',
        event=event,
        reg_count=reg_count,
        user_registration=user_reg,
        available_slots=available_slots,
        deadline_passed=deadline_passed
    )


@student_bp.route('/events/<int:event_id>/register', methods=['POST'])
@student_required
def event_register(event_id):
    db = get_db()
    event = event_service.get_event_by_id(db, event_id)
    if not event or event['status'] != 'published':
        status_name = event['status'] if event else 'unknown'
        flash(f'Cannot register: Event is {status_name} and not published. Registration is not available.', 'danger')
        return redirect(url_for('student.events'))

    success, message = registration_service.register_for_event(
        db, event_id, session['user_id']
    )

    if success:
        auth_service.log_audit(
            db, session['user_id'], 'event_registration',
            'event', event_id, 'Registered for event'
        )
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('student.event_detail', event_id=event_id))


@student_bp.route('/events/<int:event_id>/cancel', methods=['POST'])
@student_required
def event_cancel(event_id):
    db = get_db()
    success, message = registration_service.cancel_event_registration(
        db, event_id, session['user_id']
    )

    if success:
        auth_service.log_audit(
            db, session['user_id'], 'registration_cancelled',
            'event', event_id, 'Cancelled event registration'
        )
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('student.registrations'))


@student_bp.route('/registrations/<int:registration_id>/cancel', methods=['POST'])
@student_required
def registration_cancel(registration_id):
    db = get_db()
    success, message = registration_service.cancel_registration(
        db, registration_id, session['user_id']
    )

    if success:
        auth_service.log_audit(
            db, session['user_id'], 'registration_cancelled',
            'registration', registration_id, 'Cancelled registration'
        )
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('student.registrations'))


@student_bp.route('/registrations')
@student_required
def registrations():
    db = get_db()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    regs, total = registration_service.get_user_registrations_paginated(
        db, session['user_id'], page=page, per_page=per_page
    )
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    return render_template(
        'student/my_registrations.html',
        registrations=regs,
        page=page,
        total_pages=total_pages,
        total=total
    )


@student_bp.route('/profile', methods=['GET', 'POST'])
@student_required
def profile():
    db = get_db()
    user = auth_service.get_user_by_id(db, session['user_id'])
    if not user:
        abort(404)

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        student_no = request.form.get('student_no', '').strip() or None
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors.append('A valid email address is required.')

        changing_password = bool(new_password)
        if changing_password:
            if not current_password:
                errors.append('Current password is required to set a new password.')
            elif not auth_service.verify_password(user['password_hash'], current_password):
                errors.append('Current password entered is incorrect.')
            if len(new_password) < 8:
                errors.append('New password must be at least 8 characters long.')
            if new_password != confirm_password:
                errors.append('New passwords do not match.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('student/profile.html', user=user,
                                   full_name=full_name, email=email,
                                   student_no=student_no or ''), 200


        existing = db.execute(
            'SELECT user_id FROM users WHERE email = ? AND user_id != ?',
            (email, session['user_id'])
        ).fetchone()
        if existing:
            flash('This email address is already registered to another account.', 'danger')
            return render_template('student/profile.html', user=user,
                                   full_name=full_name, email=email,
                                   student_no=student_no or ''), 200


        if student_no:
            existing_sno = db.execute(
                'SELECT user_id FROM users WHERE student_no = ? AND user_id != ?',
                (student_no, session['user_id'])
            ).fetchone()
            if existing_sno:
                flash('This student number is already registered to another account.', 'danger')
                return render_template('student/profile.html', user=user,
                                       full_name=full_name, email=email,
                                       student_no=student_no), 200

        try:
            auth_service.update_user(db, session['user_id'], student_no, full_name, email)
            if changing_password:
                auth_service.update_user_password(db, session['user_id'], new_password)

            session['full_name'] = full_name
            session['email'] = email

            flash('Your profile has been updated successfully.', 'success')
            return redirect(url_for('student.profile'))
        except Exception:
            flash('An error occurred while updating your profile.', 'danger')

    return render_template(
        'student/profile.html',
        user=user,
        full_name=user['full_name'],
        email=user['email'],
        student_no=user['student_no']
    )

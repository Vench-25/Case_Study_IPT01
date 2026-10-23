"""
Administrator routes for NEUST–TOC Student Event System.
"""
import re
import sqlite3
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from db import get_db
from services import auth_service, report_service

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require an active administrator account."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            abort(403)
        db = get_db()
        user = auth_service.get_user_by_id(db, session['user_id'])
        if not user or not user['is_active']:
            session.clear()
            flash('Your account has been deactivated.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    db = get_db()
    stats = report_service.get_admin_dashboard_stats(db)
    return render_template('admin/dashboard.html', stats=stats)


@admin_bp.route('/users')
@admin_required
def users():
    db = get_db()
    search = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    users_list, total = auth_service.get_all_users(
        db,
        search=search or None,
        role=role_filter or None,
        page=page,
        per_page=per_page
    )
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    return render_template(
        'admin/users.html',
        users=users_list,
        search=search,
        role_filter=role_filter,
        page=page,
        total_pages=total_pages,
        total=total
    )


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@admin_required
def user_new():
    if request.method == 'POST':
        student_no = request.form.get('student_no', '').strip() or None
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'student')

        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors.append('A valid email address is required.')
        if not password or len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        if role not in ('admin', 'officer', 'student'):
            errors.append('Invalid role specified.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/user_form.html', action='new',
                                   student_no=student_no or '',
                                   full_name=full_name,
                                   email=email,
                                   role=role), 200

        db = get_db()
        if auth_service.get_user_by_email(db, email):
            flash('An account with this email already exists.', 'danger')
            return render_template('admin/user_form.html', action='new',
                                   student_no=student_no or '',
                                   full_name=full_name,
                                   email=email,
                                   role=role), 200

        if student_no:
            existing_sno = db.execute(
                'SELECT user_id FROM users WHERE student_no = ?', (student_no,)
            ).fetchone()
            if existing_sno:
                flash('This student number is already registered.', 'danger')
                return render_template('admin/user_form.html', action='new',
                                       student_no=student_no,
                                       full_name=full_name,
                                       email=email,
                                       role=role), 200

        try:
            user_id = auth_service.create_user(db, student_no, full_name, email, password, role)
            auth_service.log_audit(db, session['user_id'], 'user_created',
                                   'user', user_id, f'Created user {full_name} ({role})')
            flash(f'User "{full_name}" created successfully.', 'success')
            return redirect(url_for('admin.users'))
        except Exception:
            flash('An error occurred while creating the user.', 'danger')
            return render_template('admin/user_form.html', action='new',
                                   student_no=student_no or '',
                                   full_name=full_name,
                                   email=email,
                                   role=role), 200

    return render_template('admin/user_form.html', action='new', role='student')


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def user_edit(user_id):
    db = get_db()
    user = auth_service.get_user_by_id(db, user_id)
    if not user:
        abort(404)

    if request.method == 'POST':
        student_no = request.form.get('student_no', '').strip() or None
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        role = request.form.get('role', user['role'])
        new_password = request.form.get('new_password', '').strip()

        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors.append('A valid email address is required.')
        if role not in ('admin', 'officer', 'student'):
            errors.append('Invalid role specified.')
        if new_password and len(new_password) < 8:
            errors.append('Password must be at least 8 characters long.')


        if user_id == session['user_id'] and role != 'admin':
            errors.append('You cannot change your own administrator role.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/user_form.html', action='edit', user=user,
                                   student_no=student_no or '', full_name=full_name,
                                   email=email, role=role), 200


        existing_email = db.execute(
            'SELECT user_id FROM users WHERE email = ? AND user_id != ?',
            (email, user_id)
        ).fetchone()
        if existing_email:
            flash('Another user account with this email already exists.', 'danger')
            return render_template('admin/user_form.html', action='edit', user=user,
                                   student_no=student_no or '', full_name=full_name,
                                   email=email, role=role), 200


        if student_no:
            existing_sno = db.execute(
                'SELECT user_id FROM users WHERE student_no = ? AND user_id != ?',
                (student_no, user_id)
            ).fetchone()
            if existing_sno:
                flash('Another user already has this student number.', 'danger')
                return render_template('admin/user_form.html', action='edit', user=user,
                                       student_no=student_no, full_name=full_name,
                                       email=email, role=role), 200

        try:
            auth_service.update_user(db, user_id, student_no, full_name, email, role)
            if new_password:
                auth_service.update_user_password(db, user_id, new_password)

            auth_service.log_audit(db, session['user_id'], 'user_updated',
                                   'user', user_id, f'Updated user {full_name}')
            flash(f'User "{full_name}" updated successfully.', 'success')
            return redirect(url_for('admin.users'))
        except Exception:
            flash('An error occurred while updating the user.', 'danger')

    return render_template('admin/user_form.html', action='edit', user=user,
                           student_no=user['student_no'], full_name=user['full_name'],
                           email=user['email'], role=user['role'])


@admin_bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@admin_required
def user_deactivate(user_id):
    if user_id == session['user_id']:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('admin.users'))

    db = get_db()
    user = auth_service.get_user_by_id(db, user_id)
    if not user:
        abort(404)

    auth_service.set_user_active(db, user_id, False)
    auth_service.log_audit(db, session['user_id'], 'user_deactivated',
                           'user', user_id, f'Deactivated user {user["full_name"]}')
    flash(f'User "{user["full_name"]}" has been deactivated.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@admin_required
def user_activate(user_id):
    db = get_db()
    user = auth_service.get_user_by_id(db, user_id)
    if not user:
        abort(404)

    auth_service.set_user_active(db, user_id, True)
    auth_service.log_audit(db, session['user_id'], 'user_activated',
                           'user', user_id, f'Activated user {user["full_name"]}')
    flash(f'User "{user["full_name"]}" has been activated.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def user_delete(user_id):
    if user_id == session['user_id']:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))

    db = get_db()
    user = auth_service.get_user_by_id(db, user_id)
    if not user:
        abort(404)
    if user['is_active']:
        flash('Deactivate this account before deleting it.', 'danger')
        return redirect(url_for('admin.users'))

    try:
        db.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        db.execute(
            '''INSERT INTO audit_log (user_id, action, target_type, target_id, details)
               VALUES (?, ?, ?, ?, ?)''',
            (session['user_id'], 'user_deleted', 'user', user_id,
             f'Deleted user {user["full_name"]}')
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        flash(
            f'User "{user["full_name"]}" cannot be deleted because existing records '
            'are linked to this account.',
            'danger'
        )
        return redirect(url_for('admin.users'))

    flash(f'User "{user["full_name"]}" has been permanently deleted.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/organizations')
@admin_required
def organizations():
    db = get_db()
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    orgs, total = auth_service.get_all_organizations(
        db, search=search or None, page=page, per_page=per_page
    )
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    return render_template(
        'admin/organizations.html',
        organizations=orgs,
        search=search,
        page=page,
        total_pages=total_pages,
        total=total
    )


@admin_bp.route('/organizations/<int:organization_id>/delete', methods=['POST'])
@admin_required
def organization_delete(organization_id):
    db = get_db()
    org = auth_service.get_organization_by_id(db, organization_id)
    if not org:
        abort(404)
    if org['is_active']:
        flash('Deactivate this organization before deleting it.', 'danger')
        return redirect(url_for('admin.organizations'))

    try:
        db.execute(
            'DELETE FROM organizations WHERE organization_id = ?',
            (organization_id,)
        )
        db.execute(
            '''INSERT INTO audit_log (user_id, action, target_type, target_id, details)
               VALUES (?, ?, ?, ?, ?)''',
            (session['user_id'], 'organization_deleted', 'organization',
             organization_id, f'Deleted organization {org["name"]}')
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        flash(
            f'Organization "{org["name"]}" cannot be deleted because existing records '
            'are linked to it.',
            'danger'
        )
        return redirect(url_for('admin.organizations'))

    flash(f'Organization "{org["name"]}" has been permanently deleted.', 'success')
    return redirect(url_for('admin.organizations'))


@admin_bp.route('/organizations/new', methods=['GET', 'POST'])
@admin_required
def organization_new():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        contact_email = request.form.get('contact_email', '').strip()

        if not name:
            flash('Organization name is required.', 'danger')
            return render_template('admin/organization_form.html', action='new',
                                   name=name, description=description,
                                   contact_email=contact_email), 200

        db = get_db()
        existing = db.execute(
            'SELECT organization_id FROM organizations WHERE name = ?', (name,)
        ).fetchone()
        if existing:
            flash('An organization with this name already exists.', 'danger')
            return render_template('admin/organization_form.html', action='new',
                                   name=name, description=description,
                                   contact_email=contact_email), 200

        try:
            org_id = auth_service.create_organization(
                db, name, description or None, contact_email or None
            )
            auth_service.log_audit(db, session['user_id'], 'organization_created',
                                   'organization', org_id, f'Created {name}')
            flash(f'Organization "{name}" created successfully.', 'success')
            return redirect(url_for('admin.organizations'))
        except Exception:
            flash('An error occurred while creating the organization.', 'danger')

    return render_template('admin/organization_form.html', action='new')


@admin_bp.route('/organizations/<int:organization_id>/edit', methods=['GET', 'POST'])
@admin_required
def organization_edit(organization_id):
    db = get_db()
    org = auth_service.get_organization_by_id(db, organization_id)
    if not org:
        abort(404)

    if request.method == 'POST':
        action_type = request.form.get('action_type', 'update')

        if action_type == 'toggle_active':
            new_status = 0 if org['is_active'] else 1
            auth_service.set_organization_active(db, organization_id, new_status)
            status_text = 'activated' if new_status else 'deactivated'
            auth_service.log_audit(db, session['user_id'], f'organization_{status_text}',
                                   'organization', organization_id, f'{status_text}: {org["name"]}')
            flash(f'Organization "{org["name"]}" has been {status_text}.', 'success')
            return redirect(url_for('admin.organization_edit', organization_id=organization_id))

        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        contact_email = request.form.get('contact_email', '').strip()

        if not name:
            flash('Organization name is required.', 'danger')
            members = auth_service.get_organization_members(db, organization_id)
            return render_template('admin/organization_form.html', action='edit', org=org,
                                   name=name, description=description,
                                   contact_email=contact_email, members=members), 200

        existing = db.execute(
            'SELECT organization_id FROM organizations WHERE name = ? AND organization_id != ?',
            (name, organization_id)
        ).fetchone()
        if existing:
            flash('Another organization with this name already exists.', 'danger')
            members = auth_service.get_organization_members(db, organization_id)
            return render_template('admin/organization_form.html', action='edit', org=org,
                                   name=name, description=description,
                                   contact_email=contact_email, members=members), 200

        try:
            auth_service.update_organization(
                db, organization_id, name, description or None, contact_email or None
            )
            auth_service.log_audit(db, session['user_id'], 'organization_updated',
                                   'organization', organization_id, f'Updated {name}')
            flash(f'Organization "{name}" updated successfully.', 'success')
            return redirect(url_for('admin.organization_edit', organization_id=organization_id))
        except Exception:
            flash('An error occurred while updating the organization.', 'danger')

    members = auth_service.get_organization_members(db, organization_id)
    return render_template('admin/organization_form.html', action='edit', org=org,
                           name=org['name'], description=org['description'],
                           contact_email=org['contact_email'], members=members)


@admin_bp.route('/organizations/<int:organization_id>/members', methods=['POST'])
@admin_required
def organization_add_member(organization_id):
    db = get_db()
    org = auth_service.get_organization_by_id(db, organization_id)
    if not org:
        abort(404)

    user_email = request.form.get('user_email', '').strip()
    member_role = request.form.get('member_role', 'member')

    if member_role not in ('president', 'officer', 'member'):
        flash('Invalid membership role specified.', 'danger')
        return redirect(url_for('admin.organization_edit', organization_id=organization_id))

    if not user_email:
        flash('Please enter a user email address.', 'danger')
        return redirect(url_for('admin.organization_edit', organization_id=organization_id))

    user = auth_service.get_user_by_email(db, user_email)
    if not user:
        flash(f'No registered user found with email "{user_email}".', 'danger')
        return redirect(url_for('admin.organization_edit', organization_id=organization_id))

    existing = db.execute(
        'SELECT * FROM organization_members WHERE organization_id = ? AND user_id = ?',
        (organization_id, user['user_id'])
    ).fetchone()

    if existing:
        auth_service.update_member_role(db, organization_id, user['user_id'], member_role)
        flash(f'Updated {user["full_name"]}\'s role in {org["name"]} to {member_role}.', 'success')
    else:
        auth_service.add_organization_member(db, organization_id, user['user_id'], member_role)
        flash(f'Added {user["full_name"]} to {org["name"]} as {member_role}.', 'success')


    if member_role in ('officer', 'president') and user['role'] == 'student':
        auth_service.update_user(db, user['user_id'], user['student_no'],
                                user['full_name'], user['email'], 'officer')
        flash(f'Note: Global role for {user["full_name"]} was promoted to officer.', 'info')

    return redirect(url_for('admin.organization_edit', organization_id=organization_id))


@admin_bp.route('/organizations/<int:organization_id>/members/<int:user_id>/remove', methods=['POST'])
@admin_required
def organization_remove_member(organization_id, user_id):
    db = get_db()
    org = auth_service.get_organization_by_id(db, organization_id)
    if not org:
        abort(404)

    user = auth_service.get_user_by_id(db, user_id)
    if not user:
        abort(404)

    auth_service.remove_organization_member(db, organization_id, user_id)
    flash(f'Removed {user["full_name"]} from {org["name"]}.', 'success')
    return redirect(url_for('admin.organization_edit', organization_id=organization_id))


@admin_bp.route('/reports')
@admin_required
def reports():
    db = get_db()
    org_id = request.args.get('org_id', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    reports_data = report_service.get_admin_reports(
        db,
        org_id=int(org_id) if org_id else None,
        date_from=date_from or None,
        date_to=date_to or None
    )

    orgs, _ = auth_service.get_all_organizations(db, per_page=1000)
    return render_template(
        'admin/reports.html',
        reports=reports_data,
        organizations=orgs,
        org_id=org_id,
        date_from=date_from,
        date_to=date_to
    )

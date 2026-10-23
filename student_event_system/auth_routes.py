"""
Authentication routes for NEUST–TOC Student Event System.
"""
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import get_db
from services import auth_service

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Invalid email or password.', 'danger')
            return render_template('login.html', email=email), 200

        db = get_db()
        user = auth_service.get_user_by_email(db, email)


        if not user or not auth_service.verify_password(user['password_hash'], password):
            flash('Invalid email or password.', 'danger')
            return render_template('login.html', email=email), 200

        if not user['is_active']:
            flash('Invalid email or password.', 'danger')
            return render_template('login.html', email=email), 200


        session.clear()
        session['user_id'] = user['user_id']
        session['full_name'] = user['full_name']
        session['email'] = user['email']
        session['role'] = user['role']
        session.permanent = True

        flash(f'Welcome back, {user["full_name"]}!', 'success')

        if user['role'] == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user['role'] == 'officer':
            return redirect(url_for('officer.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))

    return render_template('login.html')


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        student_no = request.form.get('student_no', '').strip() or None
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []

        if not full_name:
            errors.append('Full name is required.')
        if not email:
            errors.append('Email is required.')
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors.append('Please provide a valid email address.')
        if not password:
            errors.append('Password is required.')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('register_account.html',
                                   student_no=student_no or '',
                                   full_name=full_name,
                                   email=email), 200

        db = get_db()


        existing_email = auth_service.get_user_by_email(db, email)
        if existing_email:
            flash('An account with this email already exists.', 'danger')
            return render_template('register_account.html',
                                   student_no=student_no or '',
                                   full_name=full_name,
                                   email=email), 200


        if student_no:
            existing_sno = db.execute(
                'SELECT user_id FROM users WHERE student_no = ?', (student_no,)
            ).fetchone()
            if existing_sno:
                flash('This student number is already registered.', 'danger')
                return render_template('register_account.html',
                                       student_no=student_no,
                                       full_name=full_name,
                                       email=email), 200

        try:

            auth_service.create_user(db, student_no, full_name, email, password, role='student')
            flash('Your student account was created successfully! You may now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception:
            flash('An error occurred during account creation. Please try again.', 'danger')
            return render_template('register_account.html',
                                   student_no=student_no or '',
                                   full_name=full_name,
                                   email=email), 200

    return render_template('register_account.html')

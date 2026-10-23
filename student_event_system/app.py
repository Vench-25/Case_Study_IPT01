"""
Student Organization and Event Registration System for NEUST–TOC
Main Flask Application
"""
import os
import sqlite3
from datetime import datetime
from flask import Flask, g, session, redirect, url_for, render_template
from flask_wtf.csrf import CSRFProtect
from config import Config
from db import get_db, close_db

csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)


    csrf.init_app(app)


    app.teardown_appcontext(close_db)


    @app.context_processor
    def inject_globals():
        user = None
        if 'user_id' in session:
            try:
                db = get_db()
                user = db.execute(
                    'SELECT user_id, student_no, full_name, email, role, is_active FROM users WHERE user_id = ?',
                    (session['user_id'],)
                ).fetchone()
            except Exception:
                user = None
        campus_photo = os.path.join(
            app.static_folder, 'images', 'campus', 'neust-toc-campus.jpg'
        )
        return dict(
            current_user=user,
            now=datetime.now,
            campus_photo_available=os.path.isfile(campus_photo)
        )


    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%b %d, %Y %I:%M %p'):
        if not value:
            return 'TBA'
        if isinstance(value, str):
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%d'):
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.strftime(format)
                except ValueError:
                    continue
            return value
        try:
            return value.strftime(format)
        except Exception:
            return str(value)


    from auth_routes import auth_bp
    from admin_routes import admin_bp
    from officer_routes import officer_bp
    from student_routes import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(officer_bp, url_prefix='/officer')
    app.register_blueprint(student_bp, url_prefix='/student')


    @app.route('/')
    def index():
        if 'user_id' in session:
            role = session.get('role')
            if role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif role == 'officer':
                return redirect(url_for('officer.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        return redirect(url_for('auth.login'))


    @app.route('/health')
    def health():
        return {'status': 'healthy', 'system': 'NEUST-TOC Student Event System'}, 200


    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('errors/500.html'), 500

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

"""
Authentication and user management service.
Handles user queries, password verification, user creation and updates.
"""
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


def get_user_by_email(db, email):
    """Retrieve a user by email address."""
    return db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()


def get_user_by_id(db, user_id):
    """Retrieve a user by user_id."""
    return db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()


def verify_password(stored_hash, password):
    """Verify a password against its hash."""
    return check_password_hash(stored_hash, password)


def create_user(db, student_no, full_name, email, password, role='student'):
    """Create a new user with hashed password. Returns the new user_id."""
    password_hash = generate_password_hash(password)
    cursor = db.execute(
        '''INSERT INTO users (student_no, full_name, email, password_hash, role)
           VALUES (?, ?, ?, ?, ?)''',
        (student_no or None, full_name, email, password_hash, role)
    )
    db.commit()
    return cursor.lastrowid


def update_user(db, user_id, student_no, full_name, email, role=None):
    """Update user details. Does NOT change password."""
    if role:
        db.execute(
            '''UPDATE users SET student_no = ?, full_name = ?, email = ?, role = ?
               WHERE user_id = ?''',
            (student_no or None, full_name, email, role, user_id)
        )
    else:
        db.execute(
            '''UPDATE users SET student_no = ?, full_name = ?, email = ?
               WHERE user_id = ?''',
            (student_no or None, full_name, email, user_id)
        )
    db.commit()


def update_user_password(db, user_id, new_password):
    """Update a user's password (stores hash)."""
    password_hash = generate_password_hash(new_password)
    db.execute(
        'UPDATE users SET password_hash = ? WHERE user_id = ?',
        (password_hash, user_id)
    )
    db.commit()


def set_user_active(db, user_id, is_active):
    """Activate or deactivate a user account."""
    db.execute(
        'UPDATE users SET is_active = ? WHERE user_id = ?',
        (1 if is_active else 0, user_id)
    )
    db.commit()


def get_all_users(db, search=None, role=None, page=1, per_page=20):
    """Retrieve users with optional search and pagination. Returns (users, total_count)."""
    query = 'SELECT * FROM users WHERE 1=1'
    count_query = 'SELECT COUNT(*) FROM users WHERE 1=1'
    params = []

    if search:
        query += ' AND (full_name LIKE ? OR email LIKE ? OR student_no LIKE ?)'
        count_query += ' AND (full_name LIKE ? OR email LIKE ? OR student_no LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])

    if role:
        query += ' AND role = ?'
        count_query += ' AND role = ?'
        params.append(role)

    total = db.execute(count_query, params).fetchone()[0]

    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    offset = (page - 1) * per_page
    params.extend([per_page, offset])

    users = db.execute(query, params).fetchall()
    return users, total


def get_user_organizations(db, user_id):
    """Get all organizations a user belongs to, with their member role."""
    return db.execute(
        '''SELECT o.*, om.member_role
           FROM organizations o
           JOIN organization_members om ON o.organization_id = om.organization_id
           WHERE om.user_id = ? AND o.is_active = 1
           ORDER BY o.name''',
        (user_id,)
    ).fetchall()


def is_officer_of_organization(db, user_id, organization_id):
    """Check if a user is an officer or president of a specific organization."""
    result = db.execute(
        '''SELECT member_role FROM organization_members
           WHERE user_id = ? AND organization_id = ?
           AND member_role IN ('officer', 'president')''',
        (user_id, organization_id)
    ).fetchone()
    return result is not None


def get_officer_organization_ids(db, user_id):
    """Get list of organization IDs where user is officer or president."""
    rows = db.execute(
        '''SELECT organization_id FROM organization_members
           WHERE user_id = ? AND member_role IN ('officer', 'president')''',
        (user_id,)
    ).fetchall()
    return [row['organization_id'] for row in rows]




def get_all_organizations(db, search=None, page=1, per_page=20):
    """Retrieve organizations with optional search and pagination."""
    query = 'SELECT * FROM organizations WHERE 1=1'
    count_query = 'SELECT COUNT(*) FROM organizations WHERE 1=1'
    params = []

    if search:
        query += ' AND (name LIKE ? OR description LIKE ?)'
        count_query += ' AND (name LIKE ? OR description LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param])

    total = db.execute(count_query, params).fetchone()[0]

    query += ' ORDER BY name LIMIT ? OFFSET ?'
    offset = (page - 1) * per_page
    params.extend([per_page, offset])

    orgs = db.execute(query, params).fetchall()
    return orgs, total


def get_organization_by_id(db, organization_id):
    """Retrieve a single organization by ID."""
    return db.execute(
        'SELECT * FROM organizations WHERE organization_id = ?',
        (organization_id,)
    ).fetchone()


def create_organization(db, name, description=None, contact_email=None):
    """Create a new organization. Returns the new organization_id."""
    cursor = db.execute(
        '''INSERT INTO organizations (name, description, contact_email)
           VALUES (?, ?, ?)''',
        (name, description, contact_email)
    )
    db.commit()
    return cursor.lastrowid


def update_organization(db, organization_id, name, description=None, contact_email=None):
    """Update an existing organization."""
    db.execute(
        '''UPDATE organizations SET name = ?, description = ?, contact_email = ?
           WHERE organization_id = ?''',
        (name, description, contact_email, organization_id)
    )
    db.commit()


def set_organization_active(db, organization_id, is_active):
    """Activate or deactivate an organization."""
    db.execute(
        'UPDATE organizations SET is_active = ? WHERE organization_id = ?',
        (1 if is_active else 0, organization_id)
    )
    db.commit()


def get_organization_members(db, organization_id):
    """Get all members of an organization with user details."""
    return db.execute(
        '''SELECT u.user_id, u.full_name, u.email, u.student_no, u.role,
                  om.member_role, om.joined_at
           FROM users u
           JOIN organization_members om ON u.user_id = om.user_id
           WHERE om.organization_id = ?
           ORDER BY
               CASE om.member_role
                   WHEN 'president' THEN 1
                   WHEN 'officer' THEN 2
                   ELSE 3
               END, u.full_name''',
        (organization_id,)
    ).fetchall()


def add_organization_member(db, organization_id, user_id, member_role='member'):
    """Add a user as a member of an organization."""
    db.execute(
        '''INSERT OR IGNORE INTO organization_members (organization_id, user_id, member_role)
           VALUES (?, ?, ?)''',
        (organization_id, user_id, member_role)
    )
    db.commit()


def update_member_role(db, organization_id, user_id, member_role):
    """Update a member's role in an organization."""
    db.execute(
        '''UPDATE organization_members SET member_role = ?
           WHERE organization_id = ? AND user_id = ?''',
        (member_role, organization_id, user_id)
    )
    db.commit()


def remove_organization_member(db, organization_id, user_id):
    """Remove a member from an organization."""
    db.execute(
        'DELETE FROM organization_members WHERE organization_id = ? AND user_id = ?',
        (organization_id, user_id)
    )
    db.commit()


def log_audit(db, user_id, action, target_type=None, target_id=None, details=None):
    """Record an action in the audit log."""
    db.execute(
        '''INSERT INTO audit_log (user_id, action, target_type, target_id, details)
           VALUES (?, ?, ?, ?, ?)''',
        (user_id, action, target_type, target_id, details)
    )
    db.commit()

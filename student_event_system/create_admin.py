"""
Secure initial administrator creation script.
Prompts for admin details interactively — never stores plaintext passwords in code.
"""
import os
import sys
import sqlite3
import getpass
import re
from werkzeug.security import generate_password_hash

def create_admin():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'database', 'event_system.db')

    if not os.path.exists(db_path):
        print("Error: Database not found. Run 'python init_db.py' first.")
        sys.exit(1)

    print("=" * 50)
    print("  Create Administrator Account")
    print("=" * 50)
    print()


    full_name = input("Full name: ").strip()
    if not full_name:
        print("Error: Full name is required.")
        sys.exit(1)

    email = input("Email: ").strip()
    if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        print("Error: A valid email is required.")
        sys.exit(1)

    student_no = input("Student number (optional, press Enter to skip): ").strip() or None

    password = getpass.getpass("Password (min 8 characters): ")
    if len(password) < 8:
        print("Error: Password must be at least 8 characters.")
        sys.exit(1)

    password_confirm = getpass.getpass("Confirm password: ")
    if password != password_confirm:
        print("Error: Passwords do not match.")
        sys.exit(1)

    password_hash = generate_password_hash(password)

    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON')
    try:

        existing = conn.execute('SELECT user_id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            print(f"Error: An account with email '{email}' already exists.")
            sys.exit(1)

        conn.execute(
            '''INSERT INTO users (student_no, full_name, email, password_hash, role, is_active)
               VALUES (?, ?, ?, ?, 'admin', 1)''',
            (student_no, full_name, email, password_hash)
        )
        conn.commit()
        print()
        print("Administrator account created successfully!")
        print(f"  Name:  {full_name}")
        print(f"  Email: {email}")
        print(f"  Role:  admin")
        print()
        print("You can now log in at http://127.0.0.1:5000/login")
    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    create_admin()

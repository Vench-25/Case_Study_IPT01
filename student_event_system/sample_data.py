"""Seed demo accounts for every active organization and 50 students."""
import os
import sqlite3
import sys

from werkzeug.security import generate_password_hash


SAMPLE_PASSWORD = '12345678'
OFFICER_FIRST_NAMES = (
    'Adrian', 'Beatriz', 'Carlo', 'Danica', 'Enzo',
    'Faith', 'Gabriel', 'Hannah', 'Ian', 'Jasmine',
    'Kyle', 'Leah', 'Marco', 'Nina', 'Oliver',
    'Patricia', 'Quentin', 'Rhea', 'Samuel', 'Trisha',
)
OFFICER_LAST_NAMES = (
    'Santos', 'Reyes', 'Cruz', 'Garcia', 'Mendoza',
    'Bautista', 'Flores', 'Gonzales', 'Ramos', 'Aquino',
    'Castillo', 'Navarro', 'Rivera', 'Torres', 'Villanueva',
    'Dizon', 'Mercado', 'Pascual', 'Soriano', 'Valdez',
)
STUDENT_FIRST_NAMES = (
    'Aira', 'Alden', 'Alexa', 'Andre', 'Angela',
    'Anthony', 'Bianca', 'Carl', 'Celine', 'Christian',
    'Clarisse', 'Daniel', 'Ella', 'Erika', 'Francis',
    'Gabrielle', 'Harold', 'Isabelle', 'Jared', 'Joy',
    'Katrina', 'Lance', 'Mae', 'Nathan', 'Paolo',
)
STUDENT_LAST_NAMES = (
    'Abad', 'Alvarez', 'Andrada', 'Angeles', 'Barrera',
    'Bernardo', 'Calderon', 'Castro', 'Domingo', 'Enriquez',
    'Espiritu', 'Fernandez', 'Francisco', 'Hernandez', 'Lazaro',
    'Lopez', 'Manalo', 'Marquez', 'Martinez', 'Ocampo',
    'Ortega', 'Padilla', 'Salazar', 'Santiago', 'Tan',
    'Tolentino', 'Uy', 'Vargas', 'Velasco', 'Zamora',
)


def _get_or_create_user(db, student_no, full_name, email, role):
    existing = db.execute(
        '''SELECT user_id, student_no, full_name, email, role
           FROM users WHERE email = ? OR student_no = ?''',
        (email, student_no)
    ).fetchall()

    if existing:
        if (len(existing) != 1
                or existing[0]['student_no'] != student_no
                or existing[0]['full_name'] != full_name
                or existing[0]['email'] != email
                or existing[0]['role'] != role):
            raise ValueError(
                f'Sample account identity conflicts with existing data: {email}'
            )
        return existing[0]['user_id'], False

    cursor = db.execute(
        '''INSERT INTO users (student_no, full_name, email, password_hash, role)
           VALUES (?, ?, ?, ?, ?)''',
        (student_no, full_name, email, generate_password_hash(SAMPLE_PASSWORD), role)
    )
    return cursor.lastrowid, True


def seed_sample_data(db):
    """Add missing sample accounts without changing existing records."""
    organizations = db.execute(
        '''SELECT organization_id, name FROM organizations
           WHERE is_active = 1 ORDER BY organization_id'''
    ).fetchall()
    if not organizations:
        raise ValueError(
            'Create at least one active organization before seeding sample data.'
        )

    officers_added = 0
    for org in organizations:
        organization_id = org['organization_id']
        for officer_number in range(1, 6):
            name_index = ((organization_id - 1) * 5 + officer_number - 1) % 20
            full_name = (
                f'{OFFICER_FIRST_NAMES[name_index]} '
                f'{OFFICER_LAST_NAMES[name_index]}'
            )
            student_no = f'SAMPLE-O-{organization_id:03d}-{officer_number:02d}'
            email = f'officer.org-{organization_id:03d}.{officer_number:02d}@example.test'
            user_id, created = _get_or_create_user(
                db, student_no, full_name, email, 'officer'
            )
            officers_added += created

            membership = db.execute(
                '''SELECT member_role FROM organization_members
                   WHERE organization_id = ? AND user_id = ?''',
                (organization_id, user_id)
            ).fetchone()
            if membership is None:
                db.execute(
                    '''INSERT INTO organization_members
                       (organization_id, user_id, member_role)
                       VALUES (?, ?, 'officer')''',
                    (organization_id, user_id)
                )
            elif membership['member_role'] != 'officer':
                raise ValueError(
                    f'Sample officer {email} has a conflicting organization role.'
                )

    students_added = 0
    for index in range(50):
        student_number = index + 1
        student_no = f'SAMPLE-2025-{student_number:04d}'
        full_name = (
            f'{STUDENT_FIRST_NAMES[index % len(STUDENT_FIRST_NAMES)]} '
            f'{STUDENT_LAST_NAMES[index // len(STUDENT_FIRST_NAMES)]}'
        )
        email = f'student.sample.{student_number:04d}@example.test'
        _, created = _get_or_create_user(
            db, student_no, full_name, email, 'student'
        )
        students_added += created

    return {
        'organizations': len(organizations),
        'officers_added': officers_added,
        'students_added': students_added,
    }


def main():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'database', 'event_system.db')
    if not os.path.exists(db_path):
        print("Error: Database not found. Run 'python init_db.py' first.", file=sys.stderr)
        return 1

    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    try:
        with db:
            results = seed_sample_data(db)
        print(
            f"Sample data ready for {results['organizations']} organizations: "
            f"{results['officers_added']} officers and "
            f"{results['students_added']} students added."
        )
        print(f'Sample account password: {SAMPLE_PASSWORD}')
        return 0
    except (sqlite3.Error, ValueError) as error:
        print(f'Error creating sample data: {error}', file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == '__main__':
    sys.exit(main())

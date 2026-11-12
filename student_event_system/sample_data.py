"""Replace non-admin accounts with a reproducible 150-user demo roster."""
import os
import sqlite3
import sys

from werkzeug.security import generate_password_hash


SAMPLE_PASSWORD = '12345678'
ORGANIZATION_COUNT = 3
USERS_PER_ORGANIZATION = 50
COHORT_SIZES = (38, 38, 37, 37)
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


def seed_sample_data(db):
    """Replace non-admin accounts with exactly 50 sample users per organization."""
    organizations = db.execute(
        'SELECT organization_id FROM organizations ORDER BY organization_id'
    ).fetchall()
    if len(organizations) != ORGANIZATION_COUNT:
        raise ValueError(
            f'Exactly {ORGANIZATION_COUNT} organizations are required to seed '
            f'{USERS_PER_ORGANIZATION} users per organization; found {len(organizations)}.'
        )

    admins = db.execute(
        '''SELECT user_id FROM users
           WHERE role = 'admin' AND is_active = 1 ORDER BY user_id'''
    ).fetchall()
    if not admins:
        raise ValueError('An active admin account is required before replacing users.')
    admin_id = admins[0]['user_id']

    db.execute(
        '''DELETE FROM attendance
           WHERE registration_id IN (
               SELECT registration_id FROM registrations
               WHERE user_id IN (SELECT user_id FROM users WHERE role != 'admin')
           )'''
    )
    db.execute(
        'DELETE FROM registrations WHERE user_id IN '
        '(SELECT user_id FROM users WHERE role != \'admin\')'
    )
    db.execute(
        'UPDATE events SET created_by = ? WHERE created_by IN '
        '(SELECT user_id FROM users WHERE role != \'admin\')',
        (admin_id,)
    )
    db.execute(
        'UPDATE attendance SET marked_by = ? WHERE marked_by IN '
        '(SELECT user_id FROM users WHERE role != \'admin\')',
        (admin_id,)
    )
    db.execute('DELETE FROM organization_members')
    db.execute("DELETE FROM users WHERE role != 'admin'")

    password_hash = generate_password_hash(SAMPLE_PASSWORD)
    sample_index = 0
    for organization in organizations:
        organization_id = organization['organization_id']
        for member_number in range(USERS_PER_ORGANIZATION):
            first_name = STUDENT_FIRST_NAMES[
                sample_index % len(STUDENT_FIRST_NAMES)
            ]
            last_name = STUDENT_LAST_NAMES[
                sample_index // len(STUDENT_FIRST_NAMES)
            ]
            full_name = f'{first_name} {last_name}'
            email = f'{first_name.lower()}.{last_name.lower()}@gmail.com'

            cohort_start = 0
            for cohort_offset, cohort_size in enumerate(COHORT_SIZES):
                if sample_index < cohort_start + cohort_size:
                    cohort_year = 2023 + cohort_offset
                    cohort_number = sample_index - cohort_start + 1
                    break
                cohort_start += cohort_size
            student_no = f'TAL{cohort_year}-{cohort_number:06d}'

            if member_number == 0:
                member_role = 'president'
                role = 'officer'
            elif member_number < 10:
                member_role = 'officer'
                role = 'officer'
            else:
                member_role = 'member'
                role = 'student'

            cursor = db.execute(
                '''INSERT INTO users
                   (student_no, full_name, email, password_hash, role)
                   VALUES (?, ?, ?, ?, ?)''',
                (student_no, full_name, email, password_hash, role)
            )
            db.execute(
                '''INSERT INTO organization_members
                   (organization_id, user_id, member_role)
                   VALUES (?, ?, ?)''',
                (organization_id, cursor.lastrowid, member_role)
            )
            sample_index += 1

    return {'organizations': len(organizations), 'users_added': sample_index}


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
            f"Sample data ready: {results['users_added']} users across "
            f"{results['organizations']} organizations."
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

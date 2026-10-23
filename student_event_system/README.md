# Student Organization and Event Registration System for NEUST–TOC

A web-based system for managing student organizations, campus events, event registration, attendance tracking, and participant reports at the Nueva Ecija University of Science and Technology – Talavera Off-Campus (NEUST–TOC).

## Features

- **Administrator**: Manage users, organizations, view system-wide reports
- **Organization Officer**: Create/manage events, track registrations, record attendance, export reports
- **Student**: Browse events, register, view history, manage profile

## Interface themes and campus imagery

The application shell supports light, dark, and system color themes. The
selection is stored in the browser and does not change server-side data.

The existing NEUST seal image is located at `static/images/logo.jpg` and is
used without changing its proportions. Its approval/provenance should be
confirmed before public deployment.

No verified NEUST–TOC campus photograph was present in the project. If you
have permission to use an official Talavera Off-Campus photograph, add it as:

```text
static/images/campus/neust-toc-campus.jpg
```

The login page will use that local image when present. Do not use a generic
campus image as a substitute or hotlink an unverified image.

Event imagery is not currently part of the event record or event forms, so
the directory intentionally uses real event details rather than stock
photography. If event-image support is added later, keep approved local
artwork under `static/images/events/` and connect it to an explicit event
field before displaying it.

## Technology Stack

- Python 3 / Flask
- SQLite3
- Bootstrap 5
- Jinja2 Templates
- Flask-WTF (CSRF Protection)

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation & Setup

### 1. Clone or Download the Project

Download or clone the project files to your local machine.

### 2. Open Terminal in Project Directory

Open PowerShell, Command Prompt, or VS Code terminal and navigate to the `student_event_system` folder.

### 3. Create Virtual Environment

```powershell
python -m venv venv
```

### 4. Activate Virtual Environment

**PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

If execution policy blocks this, use Command Prompt instead:

```cmd
venv\Scripts\activate.bat
```

Or set the execution policy:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 5. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 6. Configure Environment Variables

Copy the example environment file:

```powershell
copy .env.example .env
```

Edit `.env` and set a strong SECRET_KEY for production:

```
SECRET_KEY=your-random-secret-key-here
```

> **⚠️ Important:** The default `dev-fallback-key` is only for local development. For any deployment, generate a secure random key.

### 7. Initialize the Database

```powershell
python init_db.py
```

### 8. Create Administrator Account

```powershell
python create_admin.py
```

Follow the prompts to enter admin name, email, and password.

### 8b. (Optional) Seed Demonstration Data

For testing and grading demonstration purposes, you can optionally seed sample accounts, organizations, events, and registrations:

```powershell
python seed_data.py
```

This creates:
- **Admin**: `admin@neust-toc.example.com`
- **Officer**: `officer.miguel@neust-toc.example.com` (Technology and Innovation Society President)
- **Officer**: `officer.patricia@neust-toc.example.com` (Business and Entrepreneurship Circle President, Student Council Officer)
- **Students**: `student.angela@neust-toc.example.com`, `student.joshua@neust-toc.example.com`, and `student.nicole@neust-toc.example.com`

All seeded accounts use the password `Password123!`. Names, organizations, events, and `.example.com` email addresses are fictional demonstration data, not official NEUST records or announcements. Event locations refer generally to the Talavera Off-Campus; confirm real venues and schedules with the campus before using them.

### 9. Start the Development Server

```powershell
python app.py
```

### 10. Open in Browser

Navigate to: [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Usage Guide

### Getting Started

1. Log in with the administrator account you created.
2. Create organizations via **Admin > Organizations**.
3. Create user accounts (officers, students) via **Admin > Users**.
4. To permanently remove an account, deactivate it first in **Admin > Users**, then use the delete action. Accounts linked to organization, event, registration, or attendance records cannot be deleted, preserving system history.
5. To permanently remove an organization, deactivate it first in **Admin > Organizations**, then use the delete action. Organizations linked to membership, event, registration, or attendance records cannot be deleted, preserving system history.
6. Assign users to organizations with appropriate roles (president, officer, member).
7. Officers log in and create events for their organizations.
8. Officers publish events to make them visible to students.
9. Students log in, browse events, and register.
10. Officers manage attendance for their events.
11. Generate and export reports.

### Event Lifecycle

1. **Draft** — Officer creates event (saved as draft)
2. **Published** — Officer publishes event (visible to students, registration opens)
3. **Completed** — Officer marks event complete after it occurs
4. **Cancelled** — Officer cancels event if needed

```
┌───────┐     ┌───────────┐     ┌───────────┐
│ Draft │────▸│ Published │────▸│ Completed │
└───────┘     └─────┬─────┘     └───────────┘
                    │
                    ▼
              ┌───────────┐
              │ Cancelled │
              └───────────┘
```

### Registration Rules

- Students can only register for **published** events
- Registration must be before the **deadline**
- Events have a **maximum capacity**
- Students can cancel registration before event starts
- Cancelled registrations can be **reactivated** (if still eligible)

### Attendance

- Officers record attendance for published or completed events
- Each participant can be marked **present** or **absent**
- Attendance can be corrected after initial marking

## Running Tests

```powershell
pytest tests/ -v
```

To run a specific test file:

```powershell
pytest tests/test_auth.py -v
```

To run with coverage report:

```powershell
pytest tests/ -v --cov=. --cov-report=term-missing
```

## Database Backup

The SQLite database is stored at `database/event_system.db`. To back up:

```powershell
copy database\event_system.db database\event_system_backup.db
```

To reset the database during development:

1. Delete `database/event_system.db`
2. Run `python init_db.py`
3. Run `python create_admin.py`

## Project Structure

```
student_event_system/
├── app.py                      # Application factory and entry point
├── db.py                       # Central database connection utilities (get_db, close_db)
├── config.py                   # Configuration settings
├── schema.sql                  # Database schema
├── init_db.py                  # Database initialization script
├── create_admin.py             # Admin account creation script
├── seed_data.py                # Development demonstration seeding script
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── .env                        # Environment variables (not in version control)
├── README.md                   # This file
│
├── database/                   # SQLite database directory
│   └── event_system.db         # SQLite database file
│
├── services/                   # Business logic layer
│   ├── __init__.py
│   ├── auth_service.py         # Authentication & user management
│   ├── registration_service.py # Event registration logic
│   └── attendance_service.py   # Attendance tracking logic
│
├── routes/                     # Route blueprints
│   ├── __init__.py
│   ├── auth.py                 # Login, logout, register routes
│   ├── admin.py                # Admin dashboard and management
│   ├── officer.py              # Officer event management
│   └── student.py              # Student browsing and registration
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Base layout template
│   ├── auth/                   # Authentication templates
│   │   ├── login.html
│   │   └── register.html
│   ├── admin/                  # Admin panel templates
│   │   ├── dashboard.html
│   │   ├── users.html
│   │   ├── user_form.html
│   │   ├── organizations.html
│   │   └── organization_form.html
│   ├── officer/                # Officer panel templates
│   │   ├── dashboard.html
│   │   ├── events.html
│   │   ├── event_form.html
│   │   ├── event_detail.html
│   │   └── attendance.html
│   └── student/                # Student panel templates
│       ├── dashboard.html
│       ├── events.html
│       ├── event_detail.html
│       └── profile.html
│
├── static/                     # Static assets
│   ├── css/
│   │   ├── style.css           # Existing shared styles
│   │   └── design-system.css   # NEUST–TOC visual system and responsive themes
│   └── js/
│       └── main.js             # Custom JavaScript
│
└── tests/                      # Test suite
    ├── __init__.py
    ├── conftest.py             # Shared test fixtures
    ├── test_auth.py            # Authentication tests
    ├── test_events.py          # Event management tests
    ├── test_registration.py    # Registration tests
    ├── test_attendance.py      # Attendance tests
    └── test_permissions.py     # RBAC and permissions tests
```

## Timezone Policy

All date-times are stored in ISO 8601 format (`YYYY-MM-DD HH:MM:SS`) in local server time. The application does not perform timezone conversions.

## Security Notes

- Passwords are hashed using Werkzeug (PBKDF2)
- CSRF protection on all POST forms
- Parameterized SQL queries (no SQL injection)
- Session-based authentication with HttpOnly cookies
- Role and organization-level authorization checks
- No plaintext passwords stored or displayed

## Known Limitations

- Single-server deployment (SQLite)
- No email notifications
- No file upload for event images
- No QR code attendance (future scope)
- Local time only (no timezone handling)

## Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"

Make sure virtual environment is activated and dependencies are installed:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### "Database not found"

Run `python init_db.py` to initialize the database.

### PowerShell script execution blocked

Use Command Prompt (`venv\Scripts\activate.bat`) or set execution policy:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port 5000 already in use

Change the port in `app.py` or kill the process using port 5000:

```powershell
# Find the process using port 5000
netstat -ano | findstr :5000

# Kill the process by PID
taskkill /PID <PID> /F
```

## License

This project is created for academic purposes at NEUST–TOC.

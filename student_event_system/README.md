# Student Organization and Event Registration System for NEUST–TOC

A web-based system for managing student organizations, campus events, event registration, attendance tracking, and participant reports at the Nueva Ecija University of Science and Technology – Talavera Off-Campus (NEUST–TOC).

[Read the separate project documentation](PROJECT_DOCUMENTATION.md) for the technology overview, system features, and detailed role permissions.

## Features

- **Administrator**: Manage users, organizations, view system-wide reports
- **Organization Officer**: Create/manage events at approved campus venues, prevent overlapping venue bookings, track registrations, record attendance, export reports
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

### 9. Create Organizations and Sample Data

Create exactly three organizations in **Admin > Organizations**, then run:

```powershell
python sample_data.py
```

This replaces all non-admin accounts with 150 demo users: 50 per organization,
each with one president, nine officers, and 40 members. The existing active
administrator account is preserved. Sample student numbers use the
`TAL2023-000001` format (TAL2023 through TAL2026, with a six-digit
sequence per year), and user emails use `firstname.lastname@gmail.com`.
All sample accounts use the password
`12345678`. The replacement removes old memberships and registrations,
preserves events by assigning their creator to the administrator, and keeps
audit history. These are demo-only credentials; change or remove them before
any non-local deployment. Running the script again recreates the same roster.

Administrators can delete an organization only after deactivating it and
removing all of its members. A user must be deactivated and must have no
membership in an active organization or current event registration before
deletion.

### 10. Start the Development Server

```powershell
python app.py
```

### 11. Open in Browser

Navigate to: [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Usage Guide

### Getting Started

1. Log in with the administrator account you created.
2. Create organizations via **Admin > Organizations**.
3. Create user accounts (officers, students) via **Admin > Users**.
4. To permanently remove an account, deactivate it first in **Admin > Users**, then use the delete action. Deleting an account also permanently removes its organization memberships, events it created, registrations, and linked attendance records.
5. To permanently remove an organization, deactivate it first in **Admin > Organizations**, then use the delete action. Deleting an organization also permanently removes its memberships, events, registrations, and attendance records.
6. Assign users to organizations with appropriate roles (president, officer, member).
7. Officers log in and create events for their organizations, selecting a venue from the campus dropdown and entering both start and end times.
8. Officers publish events to make them visible to students.
9. Students log in, browse events, and register.
10. Officers manage attendance for their events.
11. Generate and export reports.

### Event Lifecycle

1. **Draft** — Officer creates event (saved as draft)
2. **Published** — Officer publishes event (visible to students, registration opens)
3. **Completed** — Officer marks event complete after it occurs
4. **Cancelled** — Officer cancels event if needed

The venue list contains LGU Building, Append Building, LAB1, LAB2, LAB3,
Library, and MGT Gymnisium. A new or edited event cannot overlap another
draft or published event at the same venue. A venue becomes available again
at the previous event's end time; cancelled and completed events do not block
new bookings.

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

- Officers can record attendance only while a published event is in progress, from its start time through its end time
- Attendance check-in is unavailable before the event starts and after it ends
- The officer check-in page lists all registered participants in the attendance table
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

## Capstone Documentation

A formal capstone report aligned with the DST capstone requirements is included in the Capstone Documentation section below.

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
│   │   └── style.css           # Shared styles and NEUST–TOC design system
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

---

## Student Organization and Event Registration System

### 1. System overview

The Student Organization and Event Registration System is a Flask web
application for the Nueva Ecija University of Science and Technology –
Talavera Off-Campus (NEUST–TOC). It centralizes organization and event
management, student registration, attendance recording, and operational
reporting.

The system has three application roles:

| Role | Main responsibilities |
|---|---|
| Administrator | Manage user accounts and organizations, assign organization membership roles, and review system-wide dashboard information and reports. |
| Organization officer | Manage events for organizations where the user is a president or officer, monitor registrants, record attendance, and review or export event reports. |
| Student | Create and manage a student account, browse published events, register or cancel a registration, and review personal registrations and attendance history. |

This document describes behavior represented in the current source code and
database schema. It does not imply that planned features or operational
recommendations are already implemented.

### 2. Scope

#### Included

- Student account registration, login, logout, and profile updates.
- Administrator-managed user and organization records.
- Organization membership with president, officer, and member roles.
- Event creation, editing while in draft, publication, cancellation, and
  completion.
- Student event discovery, registration, registration cancellation, and
  reactivation of a cancelled registration when eligible.
- Participant lists and attendance recording as present or absent.
- Administrator and officer dashboards, event reports, and formatted Excel
  exports for event participants.
- Database audit-log records for selected administrative actions.

#### Outside the current system

- Payments or paid-event processing.
- Email, SMS, or push notifications.
- External identity providers or single sign-on.
- Dedicated mobile applications.
- Advanced analytics, event-image management, or online check-in hardware.
- Automated database migration, multi-node deployment, and database
  replication.

### 3. System architecture and components

The application follows a small layered architecture:

```text
Browser
  └── Flask routes and Jinja2 templates
        ├── Authentication and role checks
        ├── Service modules (business rules and queries)
        └── SQLite database
```

#### Application components

| Component | Responsibility |
|---|---|
| `app.py` | Creates the Flask application, enables CSRF protection, registers route blueprints, dispatches the home page by session role, provides `/health`, and defines error pages and a date-formatting template filter. |
| `config.py` | Loads environment settings, sets the Flask secret key and database location, enables CSRF, configures session-cookie flags, and limits request body size. |
| `db.py` | Opens one SQLite connection per Flask request context, returns rows by column name, enables SQLite foreign-key enforcement, and closes the connection after the request. |
| `schema.sql` | Declares database tables, constraints, foreign keys, and indexes. |
| `init_db.py` | Creates the database directory and applies the schema without replacing existing tables. |
| `auth_routes.py` | Handles login, logout, and public student account registration. |
| `admin_routes.py` | Provides administrator-only user, organization, membership, dashboard, and reporting pages. |
| `officer_routes.py` | Provides officer-only event management, participant, attendance, and reporting pages. |
| `student_routes.py` | Provides student-only event discovery, registration, profile, and registration-history pages. |
| `services/auth_service.py` | User lookup and management, password hashing and verification, organization membership queries, and organization/user listing. |
| `services/event_service.py` | Event creation, updates, status updates, and filtered/paginated event queries. |
| `services/registration_service.py` | Registration, cancellation, reactivation, participant listings, and registration counts. |
| `services/attendance_service.py` | Attendance recording and correction, attendance listings, and summary counts. |
| `services/report_service.py` | Dashboard statistics, event report data, and formatted report generation. |
| `templates/` | Server-rendered pages, shared interface components, and error pages, organized by user role. |
| `static/` | Stylesheets, JavaScript, and local images. Theme preference is a browser-side presentation setting. |
| `tests/` | Pytest fixtures and tests covering authentication, events, permissions, registration, attendance, and sample data. |

#### Request and data flow

1. A browser submits a request to a Flask route.
2. The route checks the current session and required role; officer actions
   are further scoped to organizations where the user has president or
   officer membership.
3. The route calls a service function for business rules and database work.
4. `db.py` provides the request-scoped SQLite connection. Parameterized SQL
   is used for database values.
5. The route returns a Jinja-rendered page, redirect, error page, or Excel
   report attachment.

### 4. Functional requirements

The requirements below document supported application behavior.

#### FR-01: Account access

- A visitor can create a student account with a name, email, password, and
  optional student number.
- Email is required and checked for a basic email format; email addresses
  and non-empty student numbers must be unique.
- Passwords must be at least eight characters and are stored as password
  hashes.
- Users can log in with email and password and are redirected to a
  role-appropriate dashboard.
- Inactive accounts cannot log in. Logout clears the active session.
- A student can update their profile and change their password by providing
  the current password and confirming a new password.

#### FR-02: User and organization administration

- Administrators can search, filter, and paginate users; create and edit
  users; change roles; activate or deactivate accounts; and delete accounts.
- Administrators can create, edit, activate/deactivate, and delete
  organizations.
- Administrators can add users to an organization with the membership role
  `president`, `officer`, or `member`, and remove memberships.
- Administrators can view dashboard totals and recent activity.
- Referential constraints protect related records. Administrative deletion
  workflows handle related records according to the application routes;
  deletion is not equivalent to deactivation.

#### FR-03: Event management

- A president or officer can create events for an organization where they
  hold an eligible membership.
- A newly created event starts in `draft` status.
- Event details include title, description, a venue selected from the campus
  list, start and required end times, registration deadline, and positive
  capacity. The venue options are LGU Building, Append Building, LAB1, LAB2,
  LAB3, Library, and MGT Gymnisium.
- Creation and editing reject overlapping times at the same venue when the
  other event is a draft or published event. Time ranges are treated as
  half-open, so a venue may be reused at the exact end time of its preceding
  event. Cancelled and completed events do not reserve a venue.
- Officers can edit draft events and publish, cancel, or complete events.
- Students can discover published events belonging to active organizations.
- Event and organization searches/filters and paginated lists are supported
  where provided by the relevant listing pages.

#### FR-04: Registration

- A student can register only for a published event whose organizing
  organization is active.
- Registration is rejected when the deadline has passed, capacity has been
  reached, or the student already has an active registration.
- A student can cancel their own registration while the event remains
  published and has not started.
- A previously cancelled registration can be reactivated when the event is
  still eligible and has capacity.
- A unique database constraint permits only one registration row per
  student/event pair; reactivation updates that row rather than creating a
  duplicate.
- Students can view their registrations and their current status.

#### FR-05: Attendance

- An officer with access to the event's organization can view participants
  and record each active registration as `present` or `absent`.
- Attendance can be marked only while a published event is in progress,
  between its scheduled start and end times.
- An existing attendance mark can be corrected; the most recent mark and
  marking user are stored.
- Attendance summaries report registered, present, absent, and unmarked
  counts.
- Cancelled registrations are not eligible for attendance marking.

#### FR-06: Reports

- Administrator dashboards provide user, organization, event, and active
  registration totals, recent audit activity, and a short list of upcoming
  published events.
- Officer dashboards summarize the officer's organizations, events, drafts,
  active registrations, and recent events.
- Student dashboards show registration totals, attended events, active
  registrations, and upcoming registered events.
- Officers can review event reports and download participant data as a
  formatted Excel workbook.
- Reports are operational summaries; the system does not implement advanced
  analytics.

### 5. Roles and authorization

| Capability | Visitor | Student | Officer/president | Administrator |
|---|---:|---:|---:|---:|
| Register a student account | Yes | — | — | — |
| Browse published events | No | Yes | Yes, through officer pages | Through administrative pages |
| Register/cancel own event registration | No | Yes | No | No |
| Manage own profile | No | Yes | Student profile is role-restricted | No |
| Manage events | No | No | For eligible organizations | Admin access is focused on system management and reporting |
| View participants/mark attendance | No | No | For eligible organizations | Not an officer workflow |
| Manage users and organizations | No | No | No | Yes |
| View role-specific dashboard | No | Yes | Yes | Yes |

All role-specific routes require an active authenticated account. A logged-in
user with the wrong role receives a forbidden response. Officer access to
event operations is additionally checked against organization membership;
being an officer in one organization does not grant management access to
another organization's events.

### 6. Database schema

The database is SQLite, stored by default at `database/event_system.db`.
Foreign-key enforcement is enabled on application connections. The schema
uses primary keys, `UNIQUE` constraints, `CHECK` constraints, and indexes to
support integrity and common lookups.

#### Entity relationships

```text
users ──< organization_members >── organizations
users ──< events >── organizations
users ──< registrations >── events
registrations ── 0..1 attendance
users ──< attendance (marked_by)
users ──< audit_log (nullable actor)
```

- A user may belong to many organizations; an organization may have many
  members.
- An organization can own many events; each event has one organization and
  one creating user.
- A user can register for many events; each registration belongs to one user
  and one event. The event/user pair is unique.
- A registration can have at most one attendance record.
- Audit entries may retain their record if the actor user is deleted; the
  actor reference becomes `NULL`.

#### Tables and fields

##### `users`

| Field | Type / rule | Meaning |
|---|---|---|
| `user_id` | Integer primary key, auto-increment | User identifier |
| `student_no` | Text, unique, nullable | Optional student number |
| `full_name` | Text, required | User's displayed name |
| `email` | Text, required, unique | Login email |
| `password_hash` | Text, required | Hashed password; plaintext is not stored |
| `role` | Text, required; `admin`, `officer`, or `student` | Application role |
| `is_active` | Integer, default `1`; only `0` or `1` | Account activation state |
| `created_at` | Local-time text timestamp, generated by SQLite | Account creation time |

##### `organizations`

| Field | Type / rule | Meaning |
|---|---|---|
| `organization_id` | Integer primary key, auto-increment | Organization identifier |
| `name` | Text, required, unique | Organization name |
| `description` | Text, nullable | Organization description |
| `contact_email` | Text, nullable | Contact address |
| `is_active` | Integer, default `1`; only `0` or `1` | Organization activation state |
| `created_at` | Local-time text timestamp, generated by SQLite | Creation time |

##### `organization_members`

| Field | Type / rule | Meaning |
|---|---|---|
| `organization_id` | Required foreign key to `organizations` | Organization |
| `user_id` | Required foreign key to `users` | Member |
| `member_role` | Required; `president`, `officer`, or `member`; default `member` | Organization-specific role |
| `joined_at` | Local-time text timestamp, generated by SQLite | Membership creation time |

The composite primary key is (`organization_id`, `user_id`), preventing
duplicate membership rows.

##### `events`

| Field | Type / rule | Meaning |
|---|---|---|
| `event_id` | Integer primary key, auto-increment | Event identifier |
| `organization_id` | Required foreign key to `organizations` | Owning organization |
| `created_by` | Required foreign key to `users` | Event creator |
| `title` | Text, required | Event title |
| `description` | Text, required | Event details |
| `venue` | Text, required | Event location |
| `start_at` | Text, required | Event start date/time |
| `end_at` | Text, nullable for existing database records | Required by event creation and editing forms |
| `registration_deadline` | Text, required | Registration cutoff |
| `capacity` | Integer, required and greater than zero | Maximum active registrants |
| `status` | Text, default `draft`; `draft`, `published`, `cancelled`, or `completed` | Event lifecycle state |
| `created_at` | Local-time text timestamp, generated by SQLite | Creation time |
| `updated_at` | Text, nullable | Most recent update time |

##### `registrations`

| Field | Type / rule | Meaning |
|---|---|---|
| `registration_id` | Integer primary key, auto-increment | Registration identifier |
| `event_id` | Required foreign key to `events` | Registered event |
| `user_id` | Required foreign key to `users` | Registering student |
| `registered_at` | Local-time text timestamp, generated by SQLite | Registration or reactivation time |
| `status` | Text, default `registered`; `registered` or `cancelled` | Registration state |

The (`event_id`, `user_id`) pair is unique.

##### `attendance`

| Field | Type / rule | Meaning |
|---|---|---|
| `attendance_id` | Integer primary key, auto-increment | Attendance identifier |
| `registration_id` | Required, unique foreign key to `registrations` | Registration being marked |
| `marked_by` | Required foreign key to `users` | Officer who recorded the mark |
| `attendance_status` | Required; `present` or `absent` | Attendance result |
| `marked_at` | Local-time text timestamp, generated by SQLite | Last marking time |

The unique `registration_id` permits one current attendance mark per
registration. Updating a mark replaces its status, marker, and timestamp;
there is no separate history of prior corrections.

##### `audit_log`

| Field | Type / rule | Meaning |
|---|---|---|
| `log_id` | Integer primary key, auto-increment | Audit entry identifier |
| `user_id` | Nullable foreign key to `users`; set to `NULL` when deleted | Acting user |
| `action` | Text, required | Action label |
| `target_type` | Text, nullable | Type of affected record |
| `target_id` | Integer, nullable | Identifier of affected record |
| `details` | Text, nullable | Additional action details |
| `created_at` | Local-time text timestamp, generated by SQLite | Audit entry time |

The application records selected administrative operations. The table
should not be interpreted as a complete immutable log of every system
action.

#### Indexes

Indexes are defined for user email, role, and student number; membership
lookups by user and organization; event lookups by organization, status, and
start time; registration lookups by event, user, and status; attendance by
registration; and audit entries by user and action.

#### Deletion behavior

Most foreign keys use `ON DELETE RESTRICT` to prevent orphaned related data.
The audit-log actor foreign key uses `ON DELETE SET NULL`. Application
administrative workflows must account for relationships before removing a
user or organization. Back up the database before performing destructive
administrative actions.

### 7. Event and registration lifecycle

#### Event lifecycle

```text
Draft ── publish ──> Published ── complete ──> Completed
                         └──── cancel ───────> Cancelled
```

An event is created as a draft. Published events from active organizations
are discoverable by students. Draft event details can be edited. The
database permits only the four listed status values; transition actions are
handled by officer routes.

#### Registration lifecycle

```text
No registration ── register ──> Registered
                                      │
                                      └── cancel ──> Cancelled
                                                         │
                                  re-register if eligible ┘
```

Capacity counts active (`registered`) records. Cancelling a registration
frees capacity; reactivation is subject to the same event availability and
capacity checks as a new registration.

### 8. Route reference

The authentication routes are at the application root. Role-specific
blueprints use the prefixes shown below.

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/` | Public/session-aware | Redirects to the logged-in role's dashboard or login |
| GET | `/health` | Public | Basic application health response |
| GET, POST | `/login` | Public | Sign in |
| POST | `/logout` | Session | Sign out |
| GET, POST | `/register` | Public | Create a student account |
| GET | `/admin/dashboard` | Administrator | System summary |
| GET | `/admin/users` | Administrator | Search/filter/paginate users |
| GET, POST | `/admin/users/new` | Administrator | Create a user |
| GET, POST | `/admin/users/<user_id>/edit` | Administrator | Edit a user |
| POST | `/admin/users/<user_id>/activate` | Administrator | Activate account |
| POST | `/admin/users/<user_id>/deactivate` | Administrator | Deactivate account |
| POST | `/admin/users/<user_id>/delete` | Administrator | Delete account |
| GET | `/admin/organizations` | Administrator | List organizations |
| GET, POST | `/admin/organizations/new` | Administrator | Create organization |
| GET, POST | `/admin/organizations/<organization_id>/edit` | Administrator | Edit organization |
| POST | `/admin/organizations/<organization_id>/members` | Administrator | Add or update membership |
| POST | `/admin/organizations/<organization_id>/members/<user_id>/remove` | Administrator | Remove membership |
| POST | `/admin/organizations/<organization_id>/delete` | Administrator | Delete organization |
| GET | `/admin/reports` | Administrator | View system reports |
| GET | `/officer/dashboard` | Officer/president | Organization-specific summary |
| GET | `/officer/events` | Officer/president | List and filter eligible organization events |
| GET, POST | `/officer/events/new` | Officer/president | Create draft event |
| GET, POST | `/officer/events/<event_id>/edit` | Officer/president | Edit a draft event |
| POST | `/officer/events/<event_id>/publish` | Officer/president | Publish event |
| POST | `/officer/events/<event_id>/cancel` | Officer/president | Cancel event |
| POST | `/officer/events/<event_id>/complete` | Officer/president | Complete event |
| GET | `/officer/events/<event_id>/participants` | Officer/president | View event registrations |
| GET, POST | `/officer/events/<event_id>/attendance` | Officer/president | View or update attendance |
| GET | `/officer/events/<event_id>/report` | Officer/president | View event report |
| GET | `/officer/events/<event_id>/export.xlsx` | Officer/president | Download formatted participant Excel report |
| GET | `/officer/reports` | Officer/president | View organization reports |
| GET | `/student/dashboard` | Student | Student summary |
| GET | `/student/events` | Student | Browse published events |
| GET | `/student/events/<event_id>` | Student | View event details |
| POST | `/student/events/<event_id>/register` | Student | Register for an event |
| POST | `/student/events/<event_id>/cancel` | Student | Cancel registration by event |
| POST | `/student/registrations/<registration_id>/cancel` | Student | Cancel own registration |
| GET | `/student/registrations` | Student | View registration history |
| GET, POST | `/student/profile` | Student | View or update profile |

Mutating routes use POST requests and the application enables Flask-WTF
CSRF protection. This table is a route overview, not an external API
contract.

### 9. Non-functional requirements and quality attributes

The following describes the current baseline and deployment expectations.
Items marked as recommendations are not represented as automated guarantees
in the application.

| Quality attribute | Requirement / current evidence |
|---|---|
| Security — authentication | Password hashes are generated and checked with Werkzeug security helpers. Inactive users are rejected at login and active-account checks are applied to protected role routes. |
| Security — authorization | Routes enforce role access; officer event access is scoped to eligible organization membership. |
| Security — request integrity | Flask-WTF CSRF protection is enabled. Session cookies are HTTP-only and use `SameSite=Lax`. `SESSION_COOKIE_SECURE` is configurable and defaults to false for local development. |
| Security — configuration | Set a strong, private `SECRET_KEY` through the environment for deployment. The fallback key in configuration is development-only and must not be used in production. Serve the application over HTTPS and enable the secure-cookie setting in HTTPS deployments. |
| Data integrity | Foreign keys, unique constraints, enumerated `CHECK` constraints, positive event capacity, and parameterized SQL protect common data invariants. |
| Performance | Frequently used lookup fields have indexes, and large user/event/registration listings use pagination. SQLite is intended for the current single-application deployment scale; production capacity must be load-tested. |
| Usability | Role-specific dashboards and pages organize tasks by user type; shared templates, flash messages, pagination, and formatted dates support the user workflow. |
| Maintainability | Routes, business services, templates, schema, and tests are separated into dedicated modules/directories. |
| Portability | The application uses Python, Flask, and SQLite and is intended to run locally or on a compatible Python host. The database is a local file and needs explicit backup/restore procedures. |
| Reliability | Request-scoped connections are closed at request teardown; the app provides 403, 404, and 500 pages and a basic health endpoint. |
| Privacy | User, registration, attendance, and contact data are stored locally in the configured SQLite database. Restrict access to the host and database file and follow institutional retention and privacy policies. |

#### Operational security and reliability recommendations

- Do not deploy Flask's development server or `debug=True` as a production
  service; use a production WSGI server and appropriate reverse proxy.
- Keep secrets out of source control and restrict permissions on `.env` and
  the database file.
- Configure HTTPS, secure cookies, backups, monitoring, and recovery testing
  before a public or institutional deployment.
- Replace or remove demo accounts and credentials created by `sample_data.py`
  before deployment.
- Confirm permission/provenance for the local logo and any campus imagery
  used in the interface.
- Validate backup restoration as well as backup creation.
- Define retention, access, and disclosure rules for student records and
  exported Excel report files.

### 10. Technology stack and configuration

| Layer | Technology |
|---|---|
| Server-side application | Python 3, Flask |
| Database | SQLite 3 |
| Rendering | Jinja2 server-rendered HTML |
| Styling/interface | HTML, CSS, Bootstrap-based templates, local JavaScript |
| Request protection | Flask-WTF CSRF |
| Password security | Werkzeug password hashing and verification |
| Tests | pytest |

Dependencies and pinned versions are listed in `requirements.txt`.

#### Environment settings

| Setting | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Signs Flask sessions and CSRF tokens | Development fallback; replace for deployment |
| `SESSION_COOKIE_SECURE` | Marks session cookie as HTTPS-only | `False` |

The database path is defined in `config.py` as `database/event_system.db`.
The maximum accepted request size is 16 MiB. CSRF protection is enabled by
default. `SESSION_COOKIE_HTTPONLY` is enabled and `SESSION_COOKIE_SAMESITE`
is `Lax`.

### 11. Setup and operation

Run commands from the `student_event_system` directory.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set a private `SECRET_KEY` in the environment (or in an untracked local
`.env` file), then initialize the database and create an administrator:

```powershell
python init_db.py
python create_admin.py
python app.py
```

Open `http://127.0.0.1:5000` for local development. Create organizations
through the administrator interface, then create accounts and assign
organization memberships. Optional sample data can be generated with
`python sample_data.py`; its documented demo password is `12345678` and is
not suitable for deployment.

#### Backup

The SQLite database is `database/event_system.db`. Stop the application or
use a consistent SQLite backup method before copying the file. Store backups
in a protected location and periodically verify restoration. Do not commit
database backups containing personal data.

#### Tests

Run the test suite from the application directory:

```powershell
pytest tests/ -v
```

The tests are organized around authentication, event management,
permissions, registration, attendance, and sample-data behavior.

### 12. Known limitations and future considerations

- SQLite is a file-based database; concurrent write throughput and
  horizontal scaling are limited compared with a client/server database.
- The project has schema initialization but no versioned database migration
  framework. Schema changes need a deliberate backup and migration plan.
- There is no email verification, password reset flow, or multi-factor
  authentication.
- No notification delivery, online payment, external calendar integration,
  or bulk event import is included.
- Attendance records represent the latest mark; changes do not preserve a
  correction history.
- The audit log is selective rather than a complete record of every read or
  write.
- Date/time values are stored as text and use the server's local time; the
  application does not provide timezone selection or conversion.
- The health endpoint confirms application response but does not check
  database connectivity or dependencies.
- No formal service-level, load, accessibility, disaster-recovery, or
  penetration-test guarantee is made by the application code.

Potential future work includes database migrations, automated backup and
restore, stronger account recovery and authentication controls, notification
delivery, explicit timezone handling, broader audit coverage, and additional
automated accessibility and load testing.

### 13. Source references

- `README.md` — installation instructions and end-user workflow.
- `schema.sql` — authoritative database definitions and constraints.
- `app.py`, `config.py`, and `db.py` — application setup, configuration, and
  database connection behavior.
- `*_routes.py` — route and authorization behavior.
- `services/` — business rules and database query logic.
- `tests/` — automated checks for key application workflows.

---

## Design and Development of Student Organization and Event Registration System for NEUST–TOC

### 1. Title and Topic Presentation

#### Proposed Capstone Topics

1. Design and Development of Student Organization and Event Registration System for NEUST–TOC
2. Design and Development of Web-Based Event Management and Attendance Monitoring System for Student Organizations

#### Selected Title
Design and Development of Student Organization and Event Registration System for NEUST–TOC

#### Problem to be Solved
The Nueva Ecija University of Science and Technology – Talavera Off-Campus (NEUST–TOC) currently lacks a centralized and organized system for managing student organizations, event announcements, participant registration, attendance tracking, and report generation. Most of these processes are handled manually or through fragmented communication methods, which often lead to:

- lost or inconsistent event information
- difficulty monitoring who has registered or attended
- duplicate or unauthorized participation
- delayed reporting and decision-making for officers and administrators
- limited visibility for students regarding available events

The proposed system addresses these problems by providing a secure, database-driven web platform that automates core processes and improves transparency, accountability, and efficiency.

#### Role of the Database in the Solution
The database is a core component of the system because it stores all critical information such as user profiles, organization membership, event details, registrations, attendance records, and audit logs. By using a structured database, the system can maintain data integrity, enforce access rules, support faster retrieval, and generate accurate reports for administrators, officers, and students.

---

### 2. Proposal Defense Requirements

#### A. Title
Design and Development of Student Organization and Event Registration System for NEUST–TOC

#### B. Problems Identified in the Current Process
The current process of managing student organizational events and attendance is often inefficient because it depends on manually coordinating between officers, students, and administrators. Data can be duplicated, difficult to verify, and not easily accessible in real time.

#### C. Objectives of the Study
The project aims to:

1. design and develop a web-based system for managing student organizations and campus events;
2. provide a centralized platform for event creation, publication, and registration;
3. enable officers to monitor event participants and record attendance;
4. allow students to browse events, register, and view their own registration history;
5. provide administrators with tools to manage users, organizations, and reports;
6. improve accountability through secure access control and audit logging; and
7. ensure the system uses a reliable database to store, retrieve, and manage data effectively.

#### D. Scope and Limitation / System Features

##### Scope
The system covers the following functions:

- user registration and authentication
- role-based access for admin, officer, and student
- organization management
- event creation, publication, cancellation, and completion
- campus venue selection and prevention of overlapping event bookings
- student event registration and cancellation
- attendance marking with present/absent status
- report generation by officers and administrators
- optional account activation/deactivation and audit trail tracking

##### Limitation
The system is designed for a university setting and focuses on internal campus event management. It does not include online payment processing, external payment gateways, or complex analytics beyond basic operational reporting.

#### E. Technology to be Used

- Language: Python
- Framework: Flask
- Database: SQLite
- Frontend: HTML, CSS, Bootstrap 5, Jinja2 Templates
- Security: Flask-WTF for CSRF protection and password hashing for secure credential storage
- Development Environment: VS Code, Python 3.8+

#### F. Possible Entities and Attributes

##### Users
- user_id
- student_no
- full_name
- email
- password_hash
- role
- is_active
- created_at

##### Organizations
- organization_id
- name
- description
- contact_email
- is_active
- created_at

##### Organization Members
- organization_id
- user_id
- member_role
- joined_at

##### Events
- event_id
- organization_id
- created_by
- title
- description
- venue (selected from the campus venue list)
- start_at
- end_at (required by the event form)
- registration_deadline
- capacity
- status
- created_at
- updated_at

##### Registrations
- registration_id
- event_id
- user_id
- registered_at
- status

##### Attendance
- attendance_id
- registration_id
- marked_by
- attendance_status
- marked_at

##### Audit Log
- log_id
- user_id
- action
- target_type
- target_id
- details
- created_at

#### G. Use Case
The system supports different user roles, where each role performs specific actions:

- Admin manages users and organizations and views reports.
- Officer creates and manages organization events, monitors registrations, and records attendance.
- Student browses published events, registers for events, and views personal event history.

#### H. Sample User Interface Flow

1. User opens the login page.
2. User enters email and password.
3. If valid, the system redirects the user to the appropriate dashboard.
4. Officer clicks “Create Event,” enters event details, and saves as a draft.
5. Officer publishes the event to make it available to students.
6. Student browses published events and registers before the deadline.
7. Officer marks attendance for each participant as present or absent.
8. Admin generates or reviews system-wide reports.

---

### 3. Related Review of Literature (RRL)

Student organizations in higher education require digital tools to manage routine operational activities such as event scheduling, registration, and attendance monitoring. Traditional record-keeping methods are often time-consuming and prone to error. A web-based management system helps centralize and streamline these processes, making it easier for organizations to coordinate events efficiently.

According to common practices in information systems implementation, systems that use role-based access control provide better data security and accountability. This is important in a campus environment where there are different classes of users with varying access needs. A secure system should distinguish between administrators, organization officers, and students so that each user can access only the functions relevant to their role.

A well-designed event registration system also improves decision-making by ensuring that all data is stored in a consistent, searchable database. The use of relational database design allows organizations to manage user information, event details, registrations, and attendance records systematically. This leads to better reporting, reduced duplication, and improved operational efficiency.

In summary, the literature supports the development of an automated, web-based event management system that improves campus activity coordination while maintaining data integrity and user accountability.

---

### 4. Methodology

The project follows an Agile-inspired system development approach with iterative phases. This allows the system to be developed in manageable stages while supporting feedback and improvements based on functionality and testing.

#### Phase 1: Planning and Requirement Analysis
- identified stakeholders and roles
- defined core user needs for admin, officer, and student
- specified functional requirements and business rules

#### Phase 2: System Design
- designed use cases and user workflows
- modeled data entities and relationships
- planned the user interface and dashboards
- prepared database schema and core architecture

#### Phase 3: Development
- built the Flask application and database interaction layer
- implemented login, registration, role-based dashboards, and event management features
- created modules for registration, attendance, and reporting

#### Phase 4: Testing and Validation
- verified login and registration flows
- checked role restrictions and system permissions
- validated event lifecycle and registration rules
- ensured report generation and attendance tracking work correctly

#### Phase 5: Deployment and Maintenance
- deployed locally as a web application
- monitored for system reliability and data consistency
- ensured future updates can be added without affecting core operations

---

### 5. System Architecture and Functional Modules

#### 5.1 User Roles

##### Administrator
- manages users and organizations
- approves or deactivates accounts
- reviews system-wide reports
- monitors overall activity

##### Organization Officer
- creates events
- updates or publishes events
- manages event registrations
- records attendance
- exports or views event reports

##### Student
- logs in and registers for events
- cancels registration if allowed
- views registration history
- updates profile information

#### 5.2 Main Functional Modules

- Authentication Module
- User Management Module
- Organization Management Module
- Event Management Module
- Registration Module
- Attendance Management Module
- Reporting Module
- Audit Log Module

---

### 6. Database Design and Development

The database design follows the Database Life Cycle to ensure data is properly planned, built, tested, and maintained.

#### 6.1 Database Life Cycle

1. Requirement Definition
   - identify all system entities and their business rules
2. Conceptual Design
   - define entities, attributes, and relationships
3. Logical Design
   - normalize data and organize tables to reduce redundancy
4. Physical Design
   - implement tables in SQLite with constraints and indexes
5. Implementation
   - create database schema and populate initial records
6. Testing and Maintenance
   - validate integrity, referential rules, and application usage

#### 6.2 Database Schema Summary
The project uses SQLite with several primary and related tables.

##### Entity Relationships
- One user may belong to many organization memberships.
- One organization has many events.
- One event has many registrations.
- One registration may have one attendance record.
- One user may generate multiple audit log entries.

##### ERD Representation (Textual)

```text
USERS 1 ───< ORGANIZATION_MEMBERS >── 1 ORGANIZATIONS
  │                                       │
  │                                       └──< EVENTS
  │                                              │
  │                                              └──< REGISTRATIONS >── 1 USERS
  │                                                        │
  │                                                        └── 1 ATTENDANCE
  │
  └──< AUDIT_LOG
```

#### 6.3 Database Normalization
The schema is designed to reduce redundancy and improve data consistency by separating data into related tables. The system maintains first normal form (1NF) and second normal form (2NF) principles for core business entities and aims for third normal form (3NF) in many key relationships.

---

### 7. Use Case Diagram

The application supports three major actors:

- Admin
- Officer
- Student

#### Use Case Narrative

##### Admin Use Cases
- log in
- manage users
- manage organizations
- view reports
- deactivate or reactivate records

##### Officer Use Cases
- log in
- create event
- update event status
- publish and cancel events
- view registrations
- mark attendance
- generate attendance reports

##### Student Use Cases
- register account
- log in
- browse events
- register for an event
- cancel registration
- view personal dashboard and registration history

#### ASCII Use Case Diagram

```text
+------------------+        +------------------+
|      Admin       |        |     Officer      |
+------------------+        +------------------+
| login            |        | login            |
| manage users     |        | create event     |
| manage orgs      |        | publish event    |
| view reports     |        | track registration|
+------------------+        | mark attendance  |
                             +------------------+
                                      |
                                      |
                                      v
                              +------------------+
                              |      Student     |
                              +------------------+
                              | register account |
                              | browse events    |
                              | register event   |
                              | view history     |
                              +------------------+
```

---

### 8. Context Diagram

The system interacts with three main categories of users and stores data in the central database.

```text
                     +--------------------------+
                     |  Student Organization    |
                     |  and Event Registration  |
                     |         System           |
                     +--------------------------+
                              ^      ^      ^
                              |      |      |
                  +-----------+      |      +-----------+
                  |                  |                  |
                  v                  v                  v
        +----------------+   +----------------+   +----------------+
        | Admin          |   | Officer        |   | Student        |
        | - manage users |   | - create      |   | - browse       |
        | - manage orgs  |   |   events       |   |   events       |
        | - reports      |   | - attendance   |   | - register     |
        +----------------+   +----------------+   +----------------+
                                  |
                                  |
                                  v
                        +----------------------------+
                        | SQLite Database            |
                        | users, organizations,     |
                        | events, registrations,     |
                        | attendance, audit_log     |
                        +----------------------------+
```

---

### 9. Data Flow Diagram (Gane and Sarson)

The system handles event management as a continuous flow of information between users, processes, and storage.

```text
[Student] -- browse event --> [Event Browser Process] -- event data --> [Database]
      |                                                           |
      |-- register for event --> [Registration Process] -----------|
      |                                                           |
      |-- view profile/history --> [Student Dashboard Process] ------|

[Officer] -- create/publish event --> [Event Management Process] -- data --> [Database]
      |                                                           |
      |-- mark attendance --> [Attendance Process] ----------------|

[Admin] -- manage users/organizations --> [Admin Process] -- data --> [Database]
```

This diagram shows the movement of data from user input to system processing and final storage in the database, and then back to the user in the form of dashboards, reports, and confirmation notices.

---

### 10. Sample User Flow and Interface Description

#### Login and Dashboard
The login screen requires a valid email and password. After authentication, the user is redirected to a dashboard based on role.

#### Admin Dashboard
The admin dashboard gives access to:
- user records
- organization records
- reports
- account activation/deactivation actions

#### Officer Dashboard
The officer dashboard includes:
- event creation and status updates
- list of organization events
- registration overview
- attendance marking tools

#### Student Dashboard
The student dashboard includes:
- upcoming events
- registration history
- event details and deadlines
- profile management

---

### 11. Security and Data Integrity Considerations

The system includes several security and integrity safeguards:

- role-based access control
- password hashing
- CSRF protection through Flask-WTF
- active/inactive account restrictions
- unique constraints for email and student numbers
- foreign key enforcement for related tables
- audit logging for sensitive actions

These mechanisms protect both user information and organizational records while helping maintain the trustworthiness of the system.

---

### 12. Evaluation Criteria Based on ISO/IEC 2010

#### A. Evaluation by IT Consultants

1. Functional Suitability
   - Are the required functions complete, correct, and useful?
   - Does the system meet the expected business process requirements?

2. Performance Efficiency
   - Does the system respond quickly during login, search, registration, and report generation?
   - Are operations efficient for typical usage?

3. Compatibility
   - Does the system work with different browsers and user roles?
   - Does it support the expected environment without conflict?

4. Usability
   - Is the interface easy to understand and navigate?
   - Are forms and actions intuitive for end-users?

5. Security
   - Are authentication, authorization, and data protection adequate?
   - Are private records properly restricted?

6. Maintainability
   - Is the code organized and easy to extend?
   - Can future enhancements be implemented without major disruption?

#### B. Evaluation by End-Users

1. Functional Suitability
   - Users can complete event-related tasks without confusion.

2. Performance Efficiency
   - System operations are timely and responsive.

3. Compatibility
   - Features work properly on available devices and browsers.

4. Usability
   - The interface is easy to understand and visually manageable.

---

### 13. Conclusion

The Student Organization and Event Registration System for NEUST–TOC is a practical solution designed to address the inefficiencies of manual event and attendance management in a university campus environment. The system integrates database-driven record management with role-based access, event lifecycle tracking, attendance monitoring, and report generation.

By providing separate functionalities for administrators, officers, and students, the system improves transparency, accountability, and operational efficiency. Its design is aligned with modern web application principles and supports future scalability for campus organizations and student events.

---

### 14. References

1. C. M. Beaulieu, Database Implementation. New York: Addison-Wesley, 2010.
2. D. J. A. Power, Decision Support Systems and Data-Driven Decision Making. New York: Wiley, 2014.
3. R. T. Fielding, Architectural Styles and the Design of Network-based Software Architectures. University of California, Irvine, 2000.
4. ISO/IEC 25010:2011, Systems and software engineering — Systems and software Quality Requirements and Evaluation (SQuaRE) — System and software quality models.
5. Flask Documentation, https://flask.palletsprojects.com/
6. SQLite Documentation, https://www.sqlite.org/docs.html

---

### 15. Appendix: Summary of the Implemented System

The current project implementation includes the following major components:

- Flask-based web application
- SQLite database for persistent storage
- admin, officer, and student role-based access
- organization and event management
- registration and attendance handling
- customizable templates and Bootstrap front-end
- basic report and audit features

This documentation reflects the design and scope aligned with the DST capstone requirements outlined in the provided project specification.

---

## License

This project is created for academic purposes at NEUST–TOC.

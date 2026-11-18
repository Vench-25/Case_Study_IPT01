# Project Documentation

## Student Organization and Event Registration System

The Student Organization and Event Registration System is a web application for
NEUST–TOC. It supports the administration of student accounts and organizations,
the planning of organization events, student registration, attendance tracking,
and event reporting.

This guide describes the application as implemented in this project. For setup
and installation instructions, see [README.md](README.md).

## How the application works

The application uses a server-rendered web architecture:

1. A user's browser sends a request to the Flask application.
2. A route in the authentication, administrator, officer, or student route
   group handles the request and checks the user's permissions.
3. Service modules apply the business rules and read or update the SQLite
   database.
4. Flask renders a Jinja2 HTML page or returns a generated Excel download.

The main data relationships are users and organizations, organization
memberships, events, registrations, attendance records, and audit-log entries.
The database schema enforces unique user emails, one registration per
student/event, and one attendance record per registration.

## Technologies used

| Technology | How it is used |
|---|---|
| **Python 3** | Implements the application, request handlers, service logic, database operations, date validation, and report generation. |
| **Flask 3.1** | Runs the web application, handles HTTP requests and sessions, registers route blueprints, and renders pages. |
| **Flask Blueprints** | Organize routes into authentication, administrator, officer, and student areas. |
| **Jinja2** | Renders HTML pages on the server and reuses shared layouts and page components. |
| **SQLite 3** | Stores account, organization, event, registration, attendance, and audit data in `database/event_system.db`. Python's built-in `sqlite3` module connects to it. |
| **Flask-WTF** | Enables CSRF protection for state-changing form submissions. |
| **Werkzeug** | Hashes passwords when accounts are created or changed and verifies them at login. Passwords are not stored as plain text. |
| **python-dotenv** | Loads configuration values, such as `SECRET_KEY`, from the environment or a local `.env` file. |
| **HTML, CSS, and JavaScript** | Build the browser interface. Custom styles and scripts are in `static/css/style.css` and `static/js/main.js`. |
| **Bootstrap 5.3 and Bootstrap Icons** | Provide the responsive layout and interface components/icons, loaded from a CDN by the shared template. |
| **pytest** | Listed as a development/test dependency for running the project's automated tests. |

The application uses local server time for event dates; it does not convert
between time zones. The interface also includes system, light, and dark theme
preferences stored in the browser.

## System features

### Accounts and sign-in

- Users can sign in and sign out.
- The public account form creates student accounts as organization members.
- Administrators create accounts by choosing an active organization and
  membership role. Administrator accounts are provisioned separately.
- Student account creation requires a name, valid email, password of at least
  eight characters, and matching password confirmation. Student number is
  optional.
- The account access role is derived from organization membership: `member`
  maps to student access, while any `officer` or `president` membership grants
  officer access.
- Inactive accounts cannot sign in or continue using protected pages.
- Password changes require a minimum of eight characters. Students must supply
  their current password when changing it through their profile.

### Organization management

- Administrators can create, search, edit, activate, deactivate, and delete
  organizations.
- An organization has a name, optional description, optional contact email,
  active status, and members.
- Administrators assign organization memberships and set each membership to
  `president`, `officer`, or `member`.
- An organization must be deactivated before it can be permanently deleted.

### Event management

- Officers and presidents create events for organizations where they hold an
  eligible membership. An event includes its title, description, venue, start
  and end times, registration deadline, and capacity.
- New events start as **drafts**. Organization presidents approve and publish
  drafts. Officers can edit or delete drafts, cancel published events, and
  mark published events completed; only presidents can edit published events.
- Students can browse, view, and register for published events only when they
  belong to the event's organization. Their event directory, dashboard, and
  registration history are limited to their current active organizations.
- Event lists support search and organization filters; officer lists also
  support status filters.
- The available campus venues are LGU Building, Append Building, LAB1, LAB2,
  LAB3, Library, and MGT Gymnisium.
- A draft or published event blocks an overlapping booking at the same venue.
  Cancelled and completed events do not block later bookings.
- The event end time must be after its start time, and the registration deadline
  cannot be later than the event start. Event start, end, and registration
  deadline must all be in the future.
- Published events are marked completed when the application next processes a
  request after their end time.

### Registration and attendance

- Students may register only for published events from active organizations
  they belong to.
- Registration closes at the event's registration deadline and stops when the
  event reaches capacity.
- A student cannot have duplicate registrations for the same event. A
  previously cancelled registration can be reactivated if registration is still
  allowed and capacity remains.
- Students can cancel their registration while the event is published and has
  not started.
- Officers can view event participants and mark active registrants as present
  or absent only while a published event is in progress, between its
  scheduled start and end times. Existing attendance marks can be updated
  during this window.
- Attendance summaries show registered, present, absent, and unmarked counts.

### Dashboards and reports

- Administrator, officer, and student dashboards show role-specific counts and
  recent or upcoming activity.
- Administrators can review event reports across organizations and filter by
  organization and event date.
- Officers can review reports for their organizations and filter by
  organization and date range.
- An officer can open a report for one event and download a formatted Excel
  workbook containing participant details, registration status and time,
  attendance status, event details, and attendance summary metrics. The
  filename uses the event title and ends in `_participants_reports.xlsx`.
- Selected administrative and event actions are written to the audit log.

## Role-based access

The application uses **organization membership roles** (`president`, `officer`,
`member`) as the source for non-administrator account access. Membership as an
officer or president grants officer access; otherwise, a non-administrator has
student access. Administrator access remains separate. Organization membership
also determines which organizations an officer may manage.

| Access role | Access |
|---|---|
| **Administrator** | Accesses the administrator area and is also accepted by officer routes. On individual event actions, administrators bypass the officer organization-membership check. |
| **Officer** | Accesses officer tools, but can manage events only for organizations where they are a `president` or `officer`. |
| **Student** | Accesses student tools for published events and registrations from their current organization memberships, and can update their profile. |
| **Visitor** | Can access sign-in and student registration pages; protected dashboards and features require a signed-in active account. |

An organization membership with the role `member` does **not** grant event
management rights. If a user has officer or president membership in any
organization, the account receives officer access; that access is reduced to
student access only after all such memberships are removed or changed.

### Administrator functions

Administrators can:

- **View the administrator dashboard:** review user and organization totals,
  active counts, event and registration totals, recent audit activity, and
  upcoming published events.
- **Manage user accounts:** search and filter users; create accounts with a
  required organization and membership role; edit names, email, student number,
  and optionally password; activate or deactivate accounts; permanently delete
  inactive accounts. Organization membership roles are changed through
  organization management.
- **Manage organizations:** search and list organizations; create and edit
  organization details; activate or deactivate an organization; add members,
  change their membership role, and remove them; permanently delete inactive
  organizations.
- **View system-wide reports:** filter event attendance and registration
  summaries by organization and date.
- **Use officer functions:** visit officer pages and manage individual events
  without an organization membership check. Officer dashboards, event lists,
  and aggregate officer reports are still queried using organization
  memberships.

Administrators cannot deactivate or delete their own account. An account must
be deactivated before deletion, and an organization must be deactivated before
deletion. Permanent deletion removes related memberships, events,
registrations, and attendance records.

### Officer functions

Officers can:

- **View the officer dashboard:** see counts of their organization's events,
  upcoming published events, active registrations, draft events, and recent
  events.
- **Manage eligible organization events:** list and filter events; create
  drafts; edit or delete draft event details; cancel published events; mark
  published events completed.
- **Approve and publish events:** organization presidents can review drafts and
  publish them for members. Only presidents can edit published event details.
- **View participants:** inspect registration and attendance information for
  an event in an organization they are authorized to manage.
- **Manage attendance:** mark or update present/absent status for registered
  participants when the event is published or completed.
- **View and export reports:** open event reports, download formatted Excel
  participant reports, and view organization reports filtered by organization
  or date.

The membership role `member` is not sufficient for these event-management
actions. The account must have officer access derived from an eligible
organization membership. An `officer` membership cannot publish drafts;
publishing requires the `president` membership role. Administrators may also
use these officer routes.

### Student functions

Students can:

- **View the student dashboard:** see their active and total registrations,
  attended-event count, and upcoming registered events.
- **Browse events:** search and filter published events from current
  organization memberships, view event details, remaining capacity, and
  registration availability. Event details from other organizations are not
  accessible.
- **Register for events:** register or reactivate their own cancelled
  registration for a member organization if the event is eligible, the
  deadline has not passed, and capacity remains.
- **Manage registrations:** view registration history from current member
  organizations and cancel their own registration before the event starts.
- **Manage their profile:** update their name, email, and student number, and
  change their password after confirming the current password.

Students cannot create or manage events, access administrator or officer
reports, mark attendance, or manage other users' registrations.

## Main application areas

- `auth_routes.py` — sign-in, sign-out, and student registration.
- `admin_routes.py` — administrator dashboard, account management,
  organization management, and system reports.
- `officer_routes.py` — officer dashboards, event management, attendance, and
  reports.
- `student_routes.py` — student dashboard, event browsing, registrations, and
  profile management.
- `services/` — business rules for authentication, events, registrations,
  attendance, and reports.
- `schema.sql` — database tables, constraints, and indexes.
- `templates/` — Jinja2 pages grouped by role, plus shared components.
- `static/` — custom styles, JavaScript, and image assets.

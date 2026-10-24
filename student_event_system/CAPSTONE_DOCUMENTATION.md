# Design and Development of Student Organization and Event Registration System for NEUST–TOC

## 1. Title and Topic Presentation

### Proposed Capstone Topics

1. Design and Development of Student Organization and Event Registration System for NEUST–TOC
2. Design and Development of Web-Based Event Management and Attendance Monitoring System for Student Organizations

### Selected Title
Design and Development of Student Organization and Event Registration System for NEUST–TOC

### Problem to be Solved
The Nueva Ecija University of Science and Technology – Talavera Off-Campus (NEUST–TOC) currently lacks a centralized and organized system for managing student organizations, event announcements, participant registration, attendance tracking, and report generation. Most of these processes are handled manually or through fragmented communication methods, which often lead to:

- lost or inconsistent event information
- difficulty monitoring who has registered or attended
- duplicate or unauthorized participation
- delayed reporting and decision-making for officers and administrators
- limited visibility for students regarding available events

The proposed system addresses these problems by providing a secure, database-driven web platform that automates core processes and improves transparency, accountability, and efficiency.

### Role of the Database in the Solution
The database is a core component of the system because it stores all critical information such as user profiles, organization membership, event details, registrations, attendance records, and audit logs. By using a structured database, the system can maintain data integrity, enforce access rules, support faster retrieval, and generate accurate reports for administrators, officers, and students.

---

## 2. Proposal Defense Requirements

### A. Title
Design and Development of Student Organization and Event Registration System for NEUST–TOC

### B. Problems Identified in the Current Process
The current process of managing student organizational events and attendance is often inefficient because it depends on manually coordinating between officers, students, and administrators. Data can be duplicated, difficult to verify, and not easily accessible in real time.

### C. Objectives of the Study
The project aims to:

1. design and develop a web-based system for managing student organizations and campus events;
2. provide a centralized platform for event creation, publication, and registration;
3. enable officers to monitor event participants and record attendance;
4. allow students to browse events, register, and view their own registration history;
5. provide administrators with tools to manage users, organizations, and reports;
6. improve accountability through secure access control and audit logging; and
7. ensure the system uses a reliable database to store, retrieve, and manage data effectively.

### D. Scope and Limitation / System Features

#### Scope
The system covers the following functions:

- user registration and authentication
- role-based access for admin, officer, and student
- organization management
- event creation, publication, cancellation, and completion
- student event registration and cancellation
- attendance marking with present/absent status
- report generation by officers and administrators
- optional account activation/deactivation and audit trail tracking

#### Limitation
The system is designed for a university setting and focuses on internal campus event management. It does not include online payment processing, external payment gateways, or complex analytics beyond basic operational reporting.

### E. Technology to be Used

- Language: Python
- Framework: Flask
- Database: SQLite
- Frontend: HTML, CSS, Bootstrap 5, Jinja2 Templates
- Security: Flask-WTF for CSRF protection and password hashing for secure credential storage
- Development Environment: VS Code, Python 3.8+ 

### F. Possible Entities and Attributes

#### Users
- user_id
- student_no
- full_name
- email
- password_hash
- role
- is_active
- created_at

#### Organizations
- organization_id
- name
- description
- contact_email
- is_active
- created_at

#### Organization Members
- organization_id
- user_id
- member_role
- joined_at

#### Events
- event_id
- organization_id
- created_by
- title
- description
- venue
- start_at
- end_at
- registration_deadline
- capacity
- status
- created_at
- updated_at

#### Registrations
- registration_id
- event_id
- user_id
- registered_at
- status

#### Attendance
- attendance_id
- registration_id
- marked_by
- attendance_status
- marked_at

#### Audit Log
- log_id
- user_id
- action
- target_type
- target_id
- details
- created_at

### G. Use Case
The system supports different user roles, where each role performs specific actions:

- Admin manages users and organizations and views reports.
- Officer creates and manages organization events, monitors registrations, and records attendance.
- Student browses published events, registers for events, and views personal event history.

### H. Sample User Interface Flow

1. User opens the login page.
2. User enters email and password.
3. If valid, the system redirects the user to the appropriate dashboard.
4. Officer clicks “Create Event,” enters event details, and saves as a draft.
5. Officer publishes the event to make it available to students.
6. Student browses published events and registers before the deadline.
7. Officer marks attendance for each participant as present or absent.
8. Admin generates or reviews system-wide reports.

---

## 3. Related Review of Literature (RRL)

Student organizations in higher education require digital tools to manage routine operational activities such as event scheduling, registration, and attendance monitoring. Traditional record-keeping methods are often time-consuming and prone to error. A web-based management system helps centralize and streamline these processes, making it easier for organizations to coordinate events efficiently.

According to common practices in information systems implementation, systems that use role-based access control provide better data security and accountability. This is important in a campus environment where there are different classes of users with varying access needs. A secure system should distinguish between administrators, organization officers, and students so that each user can access only the functions relevant to their role.

A well-designed event registration system also improves decision-making by ensuring that all data is stored in a consistent, searchable database. The use of relational database design allows organizations to manage user information, event details, registrations, and attendance records systematically. This leads to better reporting, reduced duplication, and improved operational efficiency.

In summary, the literature supports the development of an automated, web-based event management system that improves campus activity coordination while maintaining data integrity and user accountability.

---

## 4. Methodology

The project follows an Agile-inspired system development approach with iterative phases. This allows the system to be developed in manageable stages while supporting feedback and improvements based on functionality and testing.

### Phase 1: Planning and Requirement Analysis
- identified stakeholders and roles
- defined core user needs for admin, officer, and student
- specified functional requirements and business rules

### Phase 2: System Design
- designed use cases and user workflows
- modeled data entities and relationships
- planned the user interface and dashboards
- prepared database schema and core architecture

### Phase 3: Development
- built the Flask application and database interaction layer
- implemented login, registration, role-based dashboards, and event management features
- created modules for registration, attendance, and reporting

### Phase 4: Testing and Validation
- verified login and registration flows
- checked role restrictions and system permissions
- validated event lifecycle and registration rules
- ensured report generation and attendance tracking work correctly

### Phase 5: Deployment and Maintenance
- deployed locally as a web application
- monitored for system reliability and data consistency
- ensured future updates can be added without affecting core operations

---

## 5. System Architecture and Functional Modules

### 5.1 User Roles

#### Administrator
- manages users and organizations
- approves or deactivates accounts
- reviews system-wide reports
- monitors overall activity

#### Organization Officer
- creates events
- updates or publishes events
- manages event registrations
- records attendance
- exports or views event reports

#### Student
- logs in and registers for events
- cancels registration if allowed
- views registration history
- updates profile information

### 5.2 Main Functional Modules

- Authentication Module
- User Management Module
- Organization Management Module
- Event Management Module
- Registration Module
- Attendance Management Module
- Reporting Module
- Audit Log Module

---

## 6. Database Design and Development

The database design follows the Database Life Cycle to ensure data is properly planned, built, tested, and maintained.

### 6.1 Database Life Cycle

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

### 6.2 Database Schema Summary
The project uses SQLite with several primary and related tables.

#### Entity Relationships
- One user may belong to many organization memberships.
- One organization has many events.
- One event has many registrations.
- One registration may have one attendance record.
- One user may generate multiple audit log entries.

#### ERD Representation (Textual)

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

### 6.3 Database Normalization
The schema is designed to reduce redundancy and improve data consistency by separating data into related tables. The system maintains first normal form (1NF) and second normal form (2NF) principles for core business entities and aims for third normal form (3NF) in many key relationships.

---

## 7. Use Case Diagram

The application supports three major actors:

- Admin
- Officer
- Student

### Use Case Narrative

#### Admin Use Cases
- log in
- manage users
- manage organizations
- view reports
- deactivate or reactivate records

#### Officer Use Cases
- log in
- create event
- update event status
- publish and cancel events
- view registrations
- mark attendance
- generate attendance reports

#### Student Use Cases
- register account
- log in
- browse events
- register for an event
- cancel registration
- view personal dashboard and registration history

### ASCII Use Case Diagram

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

## 8. Context Diagram

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

## 9. Data Flow Diagram (Gane and Sarson)

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

## 10. Sample User Flow and Interface Description

### Login and Dashboard
The login screen requires a valid email and password. After authentication, the user is redirected to a dashboard based on role.

### Admin Dashboard
The admin dashboard gives access to:
- user records
- organization records
- reports
- account activation/deactivation actions

### Officer Dashboard
The officer dashboard includes:
- event creation and status updates
- list of organization events
- registration overview
- attendance marking tools

### Student Dashboard
The student dashboard includes:
- upcoming events
- registration history
- event details and deadlines
- profile management

---

## 11. Security and Data Integrity Considerations

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

## 12. Evaluation Criteria Based on ISO/IEC 2010

### A. Evaluation by IT Consultants

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

### B. Evaluation by End-Users

1. Functional Suitability
   - Users can complete event-related tasks without confusion.

2. Performance Efficiency
   - System operations are timely and responsive.

3. Compatibility
   - Features work properly on available devices and browsers.

4. Usability
   - The interface is easy to understand and visually manageable.

---

## 13. Conclusion

The Student Organization and Event Registration System for NEUST–TOC is a practical solution designed to address the inefficiencies of manual event and attendance management in a university campus environment. The system integrates database-driven record management with role-based access, event lifecycle tracking, attendance monitoring, and report generation.

By providing separate functionalities for administrators, officers, and students, the system improves transparency, accountability, and operational efficiency. Its design is aligned with modern web application principles and supports future scalability for campus organizations and student events.

---

## 14. References

1. C. M. Beaulieu, Database Implementation. New York: Addison-Wesley, 2010.
2. D. J. A. Power, Decision Support Systems and Data-Driven Decision Making. New York: Wiley, 2014.
3. R. T. Fielding, Architectural Styles and the Design of Network-based Software Architectures. University of California, Irvine, 2000.
4. ISO/IEC 25010:2011, Systems and software engineering — Systems and software Quality Requirements and Evaluation (SQuaRE) — System and software quality models.
5. Flask Documentation, https://flask.palletsprojects.com/
6. SQLite Documentation, https://www.sqlite.org/docs.html

---

## 15. Appendix: Summary of the Implemented System

The current project implementation includes the following major components:

- Flask-based web application
- SQLite database for persistent storage
- admin, officer, and student role-based access
- organization and event management
- registration and attendance handling
- customizable templates and Bootstrap front-end
- basic report and audit features

This documentation reflects the design and scope aligned with the DST capstone requirements outlined in the provided project specification.

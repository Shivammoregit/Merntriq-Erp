# Mentriq360 Module and Phase Plan

This plan maps the ER/user-flow diagram into executable modules.

## Phase 1: Authentication and Role Routing

Backend:

- `accounts.User`
- `accounts.UserRole`
- JWT token obtain and refresh
- Current user endpoint

Frontend:

- Login screen
- Token storage
- Role-aware app shell

Outcome:

- Admin, teacher, student, and parent users enter different workspaces after login.

## Phase 2: Admin Master Data

Backend:

- `Campus`
- `AcademicSession`
- `ClassSection`
- `Student`
- `StudentGuardian`

Frontend:

- Admin dashboard
- Campus setup
- Academic session setup
- Class and teacher assignment
- Student admission form
- Guardian contact details

Outcome:

- Student records are created once and reused by attendance, fees, reports, and student dashboards.

## Phase 3: Attendance Flow

Backend:

- `AttendanceRecord`
- Role-scoped teacher access
- Bulk attendance upsert

Frontend:

- Teacher class selector
- Student roster
- Present, absent, and on-duty states
- Save attendance in one request

Outcome:

- Daily attendance is stored and immediately visible to admin reports and linked students.

## Phase 4: Fees and Payments

Backend:

- `FeeAssignment`
- `Payment`
- Fee status refresh rules
- Overpayment prevention

Frontend:

- Fee assignment form
- Payment entry modal
- Payment history
- Outstanding balance summary

Outcome:

- Admin users can assign fees, collect payments, and track dues.

## Phase 5: Student and Parent Visibility

Backend:

- Student-scoped querysets
- Student, attendance, fee, and payment read access
- Parent-scoped querysets through `StudentGuardian`

Frontend:

- Student profile
- Attendance summary
- Fee status and payment history
- Family portal view for linked students

Outcome:

- Students view only their own records. Parents view only records linked through guardian relationships.

## Phase 7: Operational Services

Backend:

- `StaffProfile`
- `TimetableSlot`
- `LibraryBook`
- `LibraryLoan`
- `TransportRoute`
- `TransportVehicle`
- `StudentTransportAssignment`
- `HostelRoom`
- `HostelAllocation`

Frontend:

- Operations workspace
- Staff profile table and quick-create form
- Timetable slot management
- Library catalog and loan visibility
- Transport route and vehicle management
- Hostel room and allocation visibility

Outcome:

- Campus admins manage operational services while teachers, students, and parents receive scoped read access.

## Phase 6: Reports and Audit

Backend:

- `/api/v1/reports/summary/`
- `AuditEvent`
- Login and write-action audit records

Frontend:

- Dashboard analytics
- Attendance by section
- Fee status counts
- Recent payments
- Audit event table

Outcome:

- Admin users can monitor operational status and trace important write activity.

## Future ERP Expansion

Recommended next modules:

- Academic calendar conflict detection
- Certificate and transfer certificate workflows
- Notifications and parent messaging delivery providers
- Inventory and procurement
- Payroll and HR

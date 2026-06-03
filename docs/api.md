# Mentriq360 API Reference

Base URL: `/api/v1/`

## Authentication

- `POST /auth/token/` - login and receive access/refresh tokens
- `POST /auth/token/refresh/` - refresh access token
- `GET /auth/me/` - current user
- `GET/POST /auth/users/` - admin user management
- `GET/PATCH/DELETE /auth/users/{id}/` - admin user detail

For campus-isolated databases, send `X-Campus-Code: {campus_code}` with login and subsequent API requests. The code must be configured in `CAMPUS_DATABASE_URLS` or the campus catalog `database_alias`.

## Academic Setup

- `GET/POST /campuses/`
- `GET/PATCH/DELETE /campuses/{id}/`
- `GET/POST /academic-sessions/`
- `GET/PATCH/DELETE /academic-sessions/{id}/`
- `GET/POST /sections/`
- `GET/PATCH/DELETE /sections/{id}/`

## Students and Guardians

- `GET/POST /students/`
- `GET/PATCH/DELETE /students/{id}/`
- `GET/POST /student-guardians/`
- `GET/PATCH/DELETE /student-guardians/{id}/`

Parents use the same authenticated API and are scoped through `StudentGuardian` links to their linked student records.

Useful filters:

- `/students/?campus={id}`
- `/students/?section={id}`
- `/students/?status=active`

## Attendance

- `GET/POST /attendance-records/`
- `GET/PATCH/DELETE /attendance-records/{id}/`
- `POST /attendance-records/bulk-upsert/`

Bulk attendance body:

```json
{
  "section": 1,
  "date": "2026-05-14",
  "records": [
    { "student": 1, "status": "present" },
    { "student": 2, "status": "absent" },
    { "student": 3, "status": "on_duty" }
  ]
}
```

Student attendance statuses are `present`, `absent`, and `on_duty`. Attendance write operations are locked outside today and the previous 3 days.

Useful filters:

- `/attendance-records/?section={id}`
- `/attendance-records/?date=2026-05-14`
- `/attendance-records/?status=present`

## Fees and Payments

- `GET/POST /fee-assignments/`
- `GET/PATCH/DELETE /fee-assignments/{id}/`
- `GET/POST /payments/`
- `GET/PATCH/DELETE /payments/{id}/`

Useful filters:

- `/fee-assignments/?status=pending`
- `/payments/?paid_on=2026-05-14`
- `/payments/?payment_method=online`

## Operations

- `GET/POST /staff-profiles/`
- `GET/PATCH/DELETE /staff-profiles/{id}/`
- `GET/POST /timetable-slots/`
- `GET/PATCH/DELETE /timetable-slots/{id}/`
- `GET/POST /library-books/`
- `GET/PATCH/DELETE /library-books/{id}/`
- `GET/POST /library-loans/`
- `GET/PATCH/DELETE /library-loans/{id}/`
- `GET/POST /transport-routes/`
- `GET/PATCH/DELETE /transport-routes/{id}/`
- `GET/POST /transport-vehicles/`
- `GET/PATCH/DELETE /transport-vehicles/{id}/`
- `GET/POST /student-transport-assignments/`
- `GET/PATCH/DELETE /student-transport-assignments/{id}/`
- `GET/POST /hostel-rooms/`
- `GET/PATCH/DELETE /hostel-rooms/{id}/`
- `GET/POST /hostel-allocations/`
- `GET/PATCH/DELETE /hostel-allocations/{id}/`

Admins manage operational records. Teachers, students, and parents receive read-only scoped views where the record is connected to their class or linked student.

## Reports and Audit

- `GET /reports/summary/`
- `GET /audit-events/`
- `GET /audit-events/{id}/`

Audit events are admin-only. Parent users receive `403` for audit endpoints and read only records linked through guardian relationships.

## Notifications and Support

- `GET/POST /announcements/`
- `GET/PATCH /announcements/{id}/`
- `GET/POST /support-tickets/`
- `GET/PATCH /support-tickets/{id}/`

Announcements are visible by audience. Any authenticated user can raise a support ticket; super admins can view open tickets from all users.

## Health and Schema

- `GET /health/`
- `GET /api/schema/`
- `GET /api/docs/`

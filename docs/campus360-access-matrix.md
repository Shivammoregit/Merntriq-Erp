# MentriQ Campus360 Access Matrix

This matrix defines the ERP software modules, responsible team, and role access used by the ERP UI.

## Roles

| Role | Access | Responsibility |
| --- | --- | --- |
| Super Admin | Full institution access | Creates campuses, controls global settings, audits activity, and resolves support issues. |
| Campus Admin | Campus-scoped management | Manages students, staff, fees, attendance settings, reports, and campus operations. |
| Teacher | Assigned class operations | Marks attendance, uploads homework/resources, records marks, and reviews learner progress. |
| Student | Own record view | Views personal attendance, work, results, fees, resources, admit cards, and notices. |
| Parent / Guardian | Linked student view | Views linked student attendance, fees, homework, results, transport, hostel, and notices. |

## Permission Levels

| Level | Meaning |
| --- | --- |
| Manage | Create, update, approve, configure, export, and review records within scope. |
| Use | Operate daily workflows for assigned classes or responsibility area. |
| View | Read-only access to linked or own records. |
| No access | Module is hidden from the permitted default view for that role. |

## Modules

| # | Module | Owner | Main responsibility |
| --- | --- | --- | --- |
| 1 | Admission & Registration | Admissions office | Capture applications, verify documents, approve admissions, and assign classes. |
| 2 | Student Information System (SIS) | Student records team | Maintain accurate student, guardian, academic, medical, and document records. |
| 3 | Parent / Guardian Portal | Student services team | Maintain parent access to verified linked student records and school communication. |
| 4 | Staff / Employee Management | HR and administration | Maintain staff records, assign roles, manage salary structure, and track leave. |
| 5 | Attendance Management | Operations team | Track attendance, connect capture devices, review reports, and alert absences. |
| 6 | Fees Management | Finance team | Create fee structures, collect payments, issue receipts, and monitor dues. |
| 7 | Examination Management | Examination cell | Plan exams, issue admit cards, collect marks, and process results. |
| 8 | Result & Report Card | Academic team | Publish report cards, calculate scores, and share progress with learners. |
| 9 | Certificate & TC Module | Administration office | Generate certificates, print marksheets, and manage digital signature approvals. |
| 10 | Homework & Assignment | Teachers | Publish homework, collect submissions, attach files, and remind learners before deadlines. |
| 11 | Timetable Management | Academic scheduler | Create class and teacher timetables and reduce clashes with auto scheduling. |
| 12 | Library Management | Library team | Track books, issue and return materials, calculate fines, and support barcode scanning. |
| 13 | Transport Management | Transport team | Manage routes, driver information, GPS tracking, and transport fee records. |
| 14 | Hostel Management | Hostel team | Allocate rooms, manage hostel fees, and track student check-in/out. |
| 15 | Inventory Management | Store and inventory team | Track assets, lab equipment, purchases, and stock movement. |
| 16 | Communication Module | Communication team | Send alerts, publish announcements, notify students, and coordinate school messages. |
| 17 | Online Learning Module | Academic digital learning team | Upload materials, share videos, run quizzes, and support online exams. |
| 18 | Analytics & Reports | Leadership and reporting team | Review attendance, finance, academics, and staff performance reports. |
| 19 | Director Dashboard | Director and management | Monitor institution health, finance, staff productivity, and admission trends. |
| 20 | Security & Access Control | IT security team | Control access, apply permissions, protect data, and monitor activity logs. |

The source of truth for the live UI is `web/src/lib/campus360-modules.ts`.

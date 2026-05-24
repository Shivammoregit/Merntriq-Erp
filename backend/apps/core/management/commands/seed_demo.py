from datetime import date, time, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User, UserRole
from apps.core.models import (
    AcademicSession,
    AdmitCard,
    Announcement,
    AssignedWork,
    ApprovalRequest,
    AttendanceDevice,
    AttendanceRecord,
    AttendanceStatus,
    AuditAction,
    AuditEvent,
    Campus,
    CampusMemberRole,
    CampusMembership,
    ClassSection,
    FeeAssignment,
    LearningResource,
    Payment,
    PaymentMethod,
    ResultRecord,
    StaffAttendanceRecord,
    Student,
    StudentGuardian,
    SupportTicket,
    SupportTicketStatus,
)


DEMO_PASSWORD = "Mentriq@123"
BASE_DEMO_ACCOUNT_ORDER = (
    "super_admin",
    "admin",
    "branch_admin",
    "academic_admin",
    "finance_admin",
    "teacher",
    "branch_teacher",
    "parent",
    "student",
)
BASE_DEMO_ACCOUNT_NOTES = {
    "super_admin": "Full access to all campuses and support issues",
    "admin": "Mentriq360 Main Campus IT admin",
    "branch_admin": "Mentriq360 North Campus IT admin",
    "academic_admin": "Academic records and exam workflows",
    "finance_admin": "Fees and payment workflows",
    "teacher": "Main Campus assigned class access",
    "branch_teacher": "North Campus assigned class access",
    "parent": "Read-only family portal for linked learners",
    "student": "Own learner profile only",
}
ADDITIONAL_DEMO_ACCOUNTS = (
    {
        "key": "admission_admin",
        "username": "admission.admin",
        "email": "admission.admin@mentriq360.local",
        "first_name": "Ritika",
        "last_name": "Admission",
        "role": UserRole.ADMIN,
        "campus": "main",
        "membership_role": CampusMemberRole.ACADEMIC_ADMIN,
        "note": "Admission and registration form approval responsibility",
    },
    {
        "key": "student_records_admin",
        "username": "student.records",
        "email": "student.records@mentriq360.local",
        "first_name": "Manav",
        "last_name": "Records",
        "role": UserRole.ADMIN,
        "campus": "main",
        "membership_role": CampusMemberRole.ACADEMIC_ADMIN,
        "note": "Student information, guardian, medical, and document records",
    },
    {
        "key": "hr_admin",
        "username": "hr.admin",
        "email": "hr.admin@mentriq360.local",
        "first_name": "Tanya",
        "last_name": "Human",
        "role": UserRole.ADMIN,
        "campus": "main",
        "membership_role": CampusMemberRole.IT_ADMIN,
        "can_manage_users": True,
        "note": "Staff registration, employee roles, salary, and leave setup",
    },
    {
        "key": "exam_admin",
        "username": "exam.admin",
        "email": "exam.admin@mentriq360.local",
        "first_name": "Raghav",
        "last_name": "Exam",
        "role": UserRole.ADMIN,
        "campus": "main",
        "membership_role": CampusMemberRole.ACADEMIC_ADMIN,
        "note": "Exam schedules, marks entry, report cards, and admit cards",
    },
    {
        "key": "certificate_admin",
        "username": "certificate.admin",
        "email": "certificate.admin@mentriq360.local",
        "first_name": "Sara",
        "last_name": "Certificate",
        "role": UserRole.ADMIN,
        "campus": "main",
        "membership_role": CampusMemberRole.ACADEMIC_ADMIN,
        "note": "Transfer certificates, bonafide, character, and marksheet printing",
    },
    {
        "key": "library_admin",
        "username": "library.admin",
        "email": "library.admin@mentriq360.local",
        "first_name": "Om",
        "last_name": "Library",
        "role": UserRole.ADMIN,
        "campus": "main",
        "membership_role": CampusMemberRole.ACADEMIC_ADMIN,
        "note": "Book catalog, issue-return workflow, fines, and barcode records",
    },
    {
        "key": "transport_admin",
        "username": "transport.admin",
        "email": "transport.admin@mentriq360.local",
        "first_name": "Neel",
        "last_name": "Transport",
        "role": UserRole.ADMIN,
        "campus": "north",
        "membership_role": CampusMemberRole.IT_ADMIN,
        "can_configure_attendance": True,
        "note": "Bus routes, drivers, GPS tracking, and transport fee coordination",
    },
    {
        "key": "hostel_admin",
        "username": "hostel.admin",
        "email": "hostel.admin@mentriq360.local",
        "first_name": "Ira",
        "last_name": "Hostel",
        "role": UserRole.ADMIN,
        "campus": "north",
        "membership_role": CampusMemberRole.IT_ADMIN,
        "note": "Hostel rooms, check-in/out records, and hostel fee monitoring",
    },
    {
        "key": "inventory_admin",
        "username": "inventory.admin",
        "email": "inventory.admin@mentriq360.local",
        "first_name": "Dhruv",
        "last_name": "Inventory",
        "role": UserRole.ADMIN,
        "campus": "main",
        "membership_role": CampusMemberRole.IT_ADMIN,
        "note": "Asset tracking, lab equipment, purchase records, and stock review",
    },
    {
        "key": "communication_admin",
        "username": "communication.admin",
        "email": "communication.admin@mentriq360.local",
        "first_name": "Pia",
        "last_name": "Communication",
        "role": UserRole.ADMIN,
        "campus": "main",
        "membership_role": CampusMemberRole.ACADEMIC_ADMIN,
        "note": "SMS alerts, email notices, announcements, and parent messaging",
    },
    {
        "key": "teacher_english",
        "username": "teacher.english",
        "email": "teacher.english@mentriq360.local",
        "first_name": "Asha",
        "last_name": "English",
        "role": UserRole.TEACHER,
        "campus": "main",
        "note": "English homework, reading journals, attendance, and result updates",
    },
    {
        "key": "teacher_maths",
        "username": "teacher.maths",
        "email": "teacher.maths@mentriq360.local",
        "first_name": "Naveen",
        "last_name": "Maths",
        "role": UserRole.TEACHER,
        "campus": "main",
        "note": "Mathematics assignments, marks entry, and learner progress review",
    },
    {
        "key": "teacher_science",
        "username": "teacher.science",
        "email": "teacher.science@mentriq360.local",
        "first_name": "Kiran",
        "last_name": "Science",
        "role": UserRole.TEACHER,
        "campus": "main",
        "note": "Science resources, practical work, homework, and attendance",
    },
    {
        "key": "teacher_social",
        "username": "teacher.social",
        "email": "teacher.social@mentriq360.local",
        "first_name": "Rehan",
        "last_name": "Social",
        "role": UserRole.TEACHER,
        "campus": "north",
        "note": "Social science worksheets, map assignments, and class records",
    },
    {
        "key": "teacher_hindi",
        "username": "teacher.hindi",
        "email": "teacher.hindi@mentriq360.local",
        "first_name": "Meenal",
        "last_name": "Hindi",
        "role": UserRole.TEACHER,
        "campus": "main",
        "note": "Hindi lessons, assignments, and student assessment updates",
    },
    {
        "key": "teacher_computer",
        "username": "teacher.computer",
        "email": "teacher.computer@mentriq360.local",
        "first_name": "Arvind",
        "last_name": "Computer",
        "role": UserRole.TEACHER,
        "campus": "north",
        "note": "Computer lab resources, online quizzes, and digital work review",
    },
    {
        "key": "teacher_sports",
        "username": "teacher.sports",
        "email": "teacher.sports@mentriq360.local",
        "first_name": "Zoya",
        "last_name": "Sports",
        "role": UserRole.TEACHER,
        "campus": "main",
        "note": "Sports attendance, activity records, and student participation",
    },
    {
        "key": "teacher_art",
        "username": "teacher.art",
        "email": "teacher.art@mentriq360.local",
        "first_name": "Lavanya",
        "last_name": "Art",
        "role": UserRole.TEACHER,
        "campus": "main",
        "note": "Art assignments, project submissions, and activity evaluation",
    },
    {
        "key": "teacher_music",
        "username": "teacher.music",
        "email": "teacher.music@mentriq360.local",
        "first_name": "Vivaan",
        "last_name": "Music",
        "role": UserRole.TEACHER,
        "campus": "north",
        "note": "Music practice schedules, resources, and activity progress",
    },
    {
        "key": "teacher_primary",
        "username": "teacher.primary",
        "email": "teacher.primary@mentriq360.local",
        "first_name": "Myra",
        "last_name": "Primary",
        "role": UserRole.TEACHER,
        "campus": "main",
        "note": "Primary class attendance, notices, homework, and report remarks",
    },
    {
        "key": "teacher_exam",
        "username": "teacher.exam",
        "email": "teacher.exam@mentriq360.local",
        "first_name": "Samir",
        "last_name": "Examiner",
        "role": UserRole.TEACHER,
        "campus": "main",
        "note": "Internal marks, result drafts, and exam duty support",
    },
    {
        "key": "teacher_library",
        "username": "teacher.library",
        "email": "teacher.library@mentriq360.local",
        "first_name": "Leena",
        "last_name": "Library",
        "role": UserRole.TEACHER,
        "campus": "north",
        "note": "Reading lists, library periods, and student resource guidance",
    },
    {
        "key": "student_aarav",
        "username": "student.aarav",
        "email": "student.aarav@mentriq360.local",
        "first_name": "Aarav",
        "last_name": "Mehta",
        "role": UserRole.STUDENT,
        "campus": "main",
        "note": "Learner view for attendance, homework, fee dues, and report cards",
    },
    {
        "key": "student_diyaa",
        "username": "student.diyaa",
        "email": "student.diyaa@mentriq360.local",
        "first_name": "Diyaa",
        "last_name": "Shah",
        "role": UserRole.STUDENT,
        "campus": "main",
        "note": "Learner view for course resources, assignments, and results",
    },
    {
        "key": "student_kabir",
        "username": "student.kabir",
        "email": "student.kabir@mentriq360.local",
        "first_name": "Kabir",
        "last_name": "Sethi",
        "role": UserRole.STUDENT,
        "campus": "main",
        "note": "Learner view for admit card, notices, and academic history",
    },
    {
        "key": "student_isha",
        "username": "student.isha",
        "email": "student.isha@mentriq360.local",
        "first_name": "Isha",
        "last_name": "Nair",
        "role": UserRole.STUDENT,
        "campus": "main",
        "note": "Learner view for progress tracking and assignment submissions",
    },
    {
        "key": "student_mira",
        "username": "student.mira",
        "email": "student.mira@mentriq360.local",
        "first_name": "Mira",
        "last_name": "Das",
        "role": UserRole.STUDENT,
        "campus": "north",
        "note": "North campus learner view for attendance and academic updates",
    },
    {
        "key": "student_arjun",
        "username": "student.arjun",
        "email": "student.arjun@mentriq360.local",
        "first_name": "Arjun",
        "last_name": "Pillai",
        "role": UserRole.STUDENT,
        "campus": "north",
        "note": "North campus learner view for assignments, fees, and results",
    },
    {
        "key": "student_tara",
        "username": "student.tara",
        "email": "student.tara@mentriq360.local",
        "first_name": "Tara",
        "last_name": "Bajaj",
        "role": UserRole.STUDENT,
        "campus": "main",
        "note": "Student profile, documents, LMS resources, and school notices",
    },
    {
        "key": "student_ved",
        "username": "student.ved",
        "email": "student.ved@mentriq360.local",
        "first_name": "Ved",
        "last_name": "Raman",
        "role": UserRole.STUDENT,
        "campus": "north",
        "note": "Student dashboard, timetable, homework, and online payment view",
    },
    {
        "key": "student_zara",
        "username": "student.zara",
        "email": "student.zara@mentriq360.local",
        "first_name": "Zara",
        "last_name": "Khan",
        "role": UserRole.STUDENT,
        "campus": "main",
        "note": "Student access for marks, announcements, and registered courses",
    },
    {
        "key": "student_om",
        "username": "student.om",
        "email": "student.om@mentriq360.local",
        "first_name": "Om",
        "last_name": "Joshi",
        "role": UserRole.STUDENT,
        "campus": "north",
        "note": "Student access for attendance, documents, and admit card view",
    },
    {
        "key": "parent_aarav",
        "username": "parent.aarav",
        "email": "parent.aarav@mentriq360.local",
        "first_name": "Nitin",
        "last_name": "Mehta",
        "role": UserRole.PARENT,
        "campus": "main",
        "note": "Parent view for learner attendance, fees, results, and notices",
    },
    {
        "key": "parent_diyaa",
        "username": "parent.diyaa",
        "email": "parent.diyaa@mentriq360.local",
        "first_name": "Rhea",
        "last_name": "Shah",
        "role": UserRole.PARENT,
        "campus": "main",
        "note": "Guardian view for progress tracking and school communication",
    },
    {
        "key": "parent_kabir",
        "username": "parent.kabir",
        "email": "parent.kabir@mentriq360.local",
        "first_name": "Vikram",
        "last_name": "Sethi",
        "role": UserRole.PARENT,
        "campus": "main",
        "note": "Guardian view for fee receipts, attendance, and report cards",
    },
    {
        "key": "parent_isha",
        "username": "parent.isha",
        "email": "parent.isha@mentriq360.local",
        "first_name": "Deepa",
        "last_name": "Nair",
        "role": UserRole.PARENT,
        "campus": "main",
        "note": "Parent access for assignments, school notices, and results",
    },
    {
        "key": "parent_mira",
        "username": "parent.mira",
        "email": "parent.mira@mentriq360.local",
        "first_name": "Pranav",
        "last_name": "Das",
        "role": UserRole.PARENT,
        "campus": "north",
        "note": "North campus parent access for linked learner monitoring",
    },
    {
        "key": "parent_arjun",
        "username": "parent.arjun",
        "email": "parent.arjun@mentriq360.local",
        "first_name": "Maya",
        "last_name": "Pillai",
        "role": UserRole.PARENT,
        "campus": "north",
        "note": "Guardian access for attendance, homework, and payment history",
    },
    {
        "key": "parent_tara",
        "username": "parent.tara",
        "email": "parent.tara@mentriq360.local",
        "first_name": "Kunal",
        "last_name": "Bajaj",
        "role": UserRole.PARENT,
        "campus": "main",
        "note": "Parent dashboard for notices, performance, and fee visibility",
    },
    {
        "key": "parent_ved",
        "username": "parent.ved",
        "email": "parent.ved@mentriq360.local",
        "first_name": "Anita",
        "last_name": "Raman",
        "role": UserRole.PARENT,
        "campus": "north",
        "note": "Parent portal for school notifications and student progress",
    },
    {
        "key": "parent_zara",
        "username": "parent.zara",
        "email": "parent.zara@mentriq360.local",
        "first_name": "Farah",
        "last_name": "Khan",
        "role": UserRole.PARENT,
        "campus": "main",
        "note": "Family portal for linked student communication and reports",
    },
)
DEMO_ACCOUNT_ORDER = BASE_DEMO_ACCOUNT_ORDER + tuple(account["key"] for account in ADDITIONAL_DEMO_ACCOUNTS)
DEMO_ACCOUNT_NOTES = {
    **BASE_DEMO_ACCOUNT_NOTES,
    **{account["key"]: account["note"] for account in ADDITIONAL_DEMO_ACCOUNTS},
}


class Command(BaseCommand):
    help = "Create connected demo users and ERP data for each Mentriq360 module."

    def handle(self, *args, **options):
        with transaction.atomic():
            self.reset_demo_records()
            users = self.create_users()
            campuses, sessions, sections = self.create_academic_structure(users)
            devices = self.create_campus_controls(campuses, users)
            students = self.create_students(campuses, sections, users["student"], users["parent"])
            self.create_attendance(students, sections, devices, users)
            self.create_fees(students, users)
            self.create_academic_records(students, sections, users)
            self.create_audit_events(users, campuses)
            self.create_notifications_and_support(users, campuses)

        self.stdout.write(self.style.SUCCESS("Connected demo ERP data is ready."))
        self.stdout.write("Login accounts:")
        for key in DEMO_ACCOUNT_ORDER:
            user = users[key]
            self.stdout.write(f"  {key}: {user.username} / {DEMO_PASSWORD}")
        credentials_path = self.write_demo_credentials_file(users)
        self.stdout.write(f"Demo credential file updated: {credentials_path}")

    def write_demo_credentials_file(self, users):
        credentials_path = Path(settings.BASE_DIR).resolve().parent / "docs" / "demo-credentials.txt"
        credentials_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "Mentriq360 demo credentials",
            "",
            "Generated/updated by: python manage.py seed_demo",
            "Scope: local development and demo environments only.",
            "Production passwords are hashed by Django and cannot be exported as plaintext.",
            "",
            f"Shared demo password: {DEMO_PASSWORD}",
            "",
            "User ID | Password | Role / scope",
            "--- | --- | ---",
        ]
        for key in DEMO_ACCOUNT_ORDER:
            user = users[key]
            lines.append(f"{user.username} | {DEMO_PASSWORD} | {DEMO_ACCOUNT_NOTES[key]}")
        credentials_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return credentials_path

    def reset_demo_records(self):
        Student.objects.filter(
            admission_number__in=[
                "ADM-2026-001",
                "ADM-2026-002",
                "ADM-2026-003",
                "ADM-2026-004",
                "ADM-2026-005",
                "ADM-2026-006",
            ]
        ).delete()
        StaffAttendanceRecord.objects.filter(
            staff_user__username__in=[
                "admin",
                "it.admin",
                "branchadmin",
                "north.admin",
                "academicadmin",
                "academic.admin",
                "financeadmin",
                "finance.admin",
                "teacher",
                "teacher.meera",
                "northteacher",
                "teacher.dev",
            ]
        ).delete()

    def create_users(self):
        specs = {
            "super_admin": {
                "username": "super.admin",
                "email": "superadmin@mentriq360.local",
                "first_name": "System",
                "last_name": "Owner",
                "role": UserRole.SUPER_ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
            "admin": {
                "username": "it.admin",
                "email": "admin@mentriq360.local",
                "first_name": "Aarav",
                "last_name": "Sharma",
                "role": UserRole.ADMIN,
                "is_staff": True,
            },
            "branch_admin": {
                "username": "north.admin",
                "email": "branchadmin@mentriq360.local",
                "first_name": "Kavya",
                "last_name": "Menon",
                "role": UserRole.ADMIN,
                "is_staff": True,
            },
            "academic_admin": {
                "username": "academic.admin",
                "email": "academic.admin@mentriq360.local",
                "first_name": "Nisha",
                "last_name": "Verma",
                "role": UserRole.ADMIN,
                "is_staff": True,
            },
            "finance_admin": {
                "username": "finance.admin",
                "email": "finance.admin@mentriq360.local",
                "first_name": "Kabir",
                "last_name": "Bose",
                "role": UserRole.ADMIN,
                "is_staff": True,
            },
            "teacher": {
                "username": "teacher.meera",
                "email": "teacher@mentriq360.local",
                "first_name": "Meera",
                "last_name": "Iyer",
                "role": UserRole.TEACHER,
            },
            "branch_teacher": {
                "username": "teacher.dev",
                "email": "north.teacher@mentriq360.local",
                "first_name": "Dev",
                "last_name": "Narang",
                "role": UserRole.TEACHER,
            },
            "parent": {
                "username": "parent.rohan",
                "email": "parent@mentriq360.local",
                "first_name": "Rohan",
                "last_name": "Kapoor",
                "role": UserRole.PARENT,
            },
            "student": {
                "username": "student.anaya",
                "email": "student@mentriq360.local",
                "first_name": "Anaya",
                "last_name": "Kapoor",
                "role": UserRole.STUDENT,
            },
        }
        for account in ADDITIONAL_DEMO_ACCOUNTS:
            specs[account["key"]] = {
                "username": account["username"],
                "email": account["email"],
                "first_name": account["first_name"],
                "last_name": account["last_name"],
                "role": account["role"],
                "is_staff": account["role"] == UserRole.ADMIN,
            }

        users = {}
        for key, defaults in specs.items():
            user, _ = User.objects.update_or_create(
                username=defaults["username"],
                defaults={**defaults, "is_active": True},
            )
            user.set_password(DEMO_PASSWORD)
            user.save()
            users[key] = user
        return users

    def create_academic_structure(self, users):
        campus_specs = {
            "main": ("M360-MAIN", "Mentriq360 Main Campus", "Knowledge Park, Bengaluru"),
            "north": ("M360-NORTH", "Mentriq360 North Campus", "North Avenue, Bengaluru"),
        }
        campuses = {}
        sessions = {}
        for key, (code, name, address) in campus_specs.items():
            campus, _ = Campus.objects.update_or_create(
                code=code,
                defaults={"name": name, "address": address},
            )
            session, _ = AcademicSession.objects.update_or_create(
                campus=campus,
                name="2026-27",
                defaults={
                    "start_date": date(2026, 4, 1),
                    "end_date": date(2027, 3, 31),
                    "is_active": True,
                },
            )
            campuses[key] = campus
            sessions[key] = session

        section_specs = {
            "main_5a": (campuses["main"], sessions["main"], "Grade 5", "A", users["teacher"]),
            "main_6b": (campuses["main"], sessions["main"], "Grade 6", "B", users["teacher"]),
            "north_6b": (campuses["north"], sessions["north"], "Grade 6", "B", users["branch_teacher"]),
        }
        sections = {}
        for key, (campus, session, grade, section_name, teacher) in section_specs.items():
            section, _ = ClassSection.objects.update_or_create(
                campus=campus,
                session=session,
                grade_name=grade,
                section_name=section_name,
                defaults={"class_teacher": teacher},
            )
            sections[key] = section
        return campuses, sessions, sections

    def create_campus_controls(self, campuses, users):
        memberships = [
            (campuses["main"], users["admin"], CampusMemberRole.IT_ADMIN, True, True),
            (campuses["main"], users["academic_admin"], CampusMemberRole.ACADEMIC_ADMIN, True, False),
            (campuses["main"], users["finance_admin"], CampusMemberRole.FINANCE_ADMIN, True, False),
            (campuses["main"], users["teacher"], CampusMemberRole.TEACHER, False, False),
            (campuses["main"], users["parent"], CampusMemberRole.SUPPORT, False, False),
            (campuses["main"], users["student"], CampusMemberRole.SUPPORT, False, False),
            (campuses["north"], users["branch_admin"], CampusMemberRole.IT_ADMIN, True, True),
            (campuses["north"], users["branch_teacher"], CampusMemberRole.TEACHER, False, False),
        ]
        default_membership_role = {
            UserRole.ADMIN: CampusMemberRole.IT_ADMIN,
            UserRole.TEACHER: CampusMemberRole.TEACHER,
            UserRole.PARENT: CampusMemberRole.SUPPORT,
            UserRole.STUDENT: CampusMemberRole.SUPPORT,
        }
        for account in ADDITIONAL_DEMO_ACCOUNTS:
            user = users[account["key"]]
            membership_role = account.get("membership_role", default_membership_role.get(user.role, CampusMemberRole.SUPPORT))
            memberships.append(
                (
                    campuses[account.get("campus", "main")],
                    user,
                    membership_role,
                    account.get("can_manage_users", user.role == UserRole.ADMIN and membership_role == CampusMemberRole.IT_ADMIN),
                    account.get("can_configure_attendance", user.role == UserRole.ADMIN and membership_role == CampusMemberRole.IT_ADMIN),
                )
            )
        for campus, user, role, can_manage_users, can_configure_attendance in memberships:
            CampusMembership.objects.update_or_create(
                campus=campus,
                user=user,
                role=role,
                defaults={
                    "is_primary": role == CampusMemberRole.IT_ADMIN,
                    "can_manage_users": can_manage_users,
                    "can_configure_attendance": can_configure_attendance,
                },
            )

        attendance_hardware_defaults = {
            "server_required": True,
            "use_domain_name": True,
            "domain_name": "device.nialabs.in",
            "server_ip": "192.168.000.109",
            "server_port": 7743,
            "heartbeat_seconds": 3,
            "server_approval_required": False,
            "local_port": 5005,
            "baud_rate": 38400,
            "rs485_function": "software",
        }

        device_specs = {
            "main_face": {
                "device_code": "M360-FACE-MAIN-01",
                "campus": campuses["main"],
                "name": "Main Gate Face Terminal",
                "device_type": "face_recognition",
                "location": "Main gate",
                "provider": "Nialabs attendance terminal",
                "device_numeric_id": 1,
                "configured_by": users["admin"],
                **attendance_hardware_defaults,
            },
            "main_card": {
                "device_code": "M360-CARD-MAIN-02",
                "campus": campuses["main"],
                "name": "Library Card Scanner",
                "device_type": "card_scan",
                "location": "Library entry",
                "provider": "RFID attendance reader",
                "device_numeric_id": 2,
                "configured_by": users["admin"],
                **attendance_hardware_defaults,
            },
            "main_finger": {
                "device_code": "M360-FINGER-STAFF-01",
                "campus": campuses["main"],
                "name": "Staff Room Fingerprint",
                "device_type": "fingerprint",
                "location": "Staff room",
                "provider": "Biometric attendance unit",
                "device_numeric_id": 3,
                "configured_by": users["admin"],
                "is_enabled_for_students": False,
                "is_enabled_for_staff": True,
                **attendance_hardware_defaults,
            },
            "north_face": {
                "device_code": "M360-NORTH-FACE-01",
                "campus": campuses["north"],
                "name": "North Gate Face Terminal",
                "device_type": "face_recognition",
                "location": "North campus gate",
                "provider": "Nialabs attendance terminal",
                "device_numeric_id": 4,
                "configured_by": users["branch_admin"],
                **attendance_hardware_defaults,
            },
        }
        devices = {}
        for key, spec in device_specs.items():
            code = spec.pop("device_code")
            device, _ = AttendanceDevice.objects.update_or_create(
                device_code=code,
                defaults={
                    "status": "active",
                    "is_enabled_for_students": spec.pop("is_enabled_for_students", True),
                    "is_enabled_for_staff": spec.pop("is_enabled_for_staff", True),
                    "last_seen_at": timezone.now(),
                    **spec,
                },
            )
            devices[key] = device

        staff_records = [
            (campuses["main"], users["teacher"], devices["main_face"], "present", time(8, 5), None),
            (campuses["main"], users["academic_admin"], devices["main_finger"], "late", time(8, 22), "Department review"),
            (campuses["main"], users["finance_admin"], devices["main_finger"], "present", time(7, 55), None),
            (campuses["north"], users["branch_teacher"], devices["north_face"], "present", time(8, 2), None),
        ]
        for campus, staff_user, device, status_value, clock_in, notes in staff_records:
            StaffAttendanceRecord.objects.update_or_create(
                campus=campus,
                staff_user=staff_user,
                date=timezone.localdate(),
                defaults={
                    "clock_in": clock_in,
                    "clock_out": None,
                    "status": status_value,
                    "capture_method": device.device_type,
                    "device": device,
                    "marked_by": users["admin"] if campus == campuses["main"] else users["branch_admin"],
                    "source_reference": f"demo-staff-{staff_user.username}",
                    "confidence_score": Decimal("98.40"),
                    "notes": notes or "",
                },
            )

        approvals = [
            (campuses["main"], "Student", "ADM-2026-002", "Verify new student profile", "pending", users["teacher"]),
            (campuses["main"], "AttendanceDevice", "M360-CARD-MAIN-02", "Approve library card scanner", "approved", users["academic_admin"]),
            (campuses["north"], "FeeAssignment", "NORTH-FEE-REVIEW", "Review transport fee waiver request", "rejected", users["branch_teacher"]),
        ]
        for campus, entity_type, entity_id, title, status_value, requester in approvals:
            ApprovalRequest.objects.update_or_create(
                campus=campus,
                entity_type=entity_type,
                entity_id=entity_id,
                title=title,
                defaults={
                    "description": f"Demo workflow item for {title.lower()}.",
                    "payload": {"module": entity_type, "demo": True},
                    "requested_by": requester,
                    "status": status_value,
                    "reviewed_by": users["admin"] if status_value != "pending" else None,
                    "decided_at": timezone.now() if status_value != "pending" else None,
                    "decision_note": "Demo decision" if status_value != "pending" else "",
                },
            )
        return devices

    def create_students(self, campuses, sections, student_user, parent_user):
        specs = [
            ("ADM-2026-001", "Anaya", "Kapoor", date(2015, 7, 18), campuses["main"], sections["main_5a"], student_user, "Rohan Kapoor", "Priya Kapoor", "anaya.kapoor@gmail.com", "9876543210", "A+", "Indiranagar, Bengaluru"),
            ("ADM-2026-002", "Vihaan", "Rao", date(2015, 11, 3), campuses["main"], sections["main_5a"], None, "Sandeep Rao", "Lakshmi Rao", "vihaan.rao@gmail.com", "9876543211", "O+", "HSR Layout, Bengaluru"),
            ("ADM-2026-003", "Isha", "Nair", date(2016, 1, 25), campuses["main"], sections["main_5a"], None, "Arun Nair", "Deepa Nair", "isha.nair@gmail.com", "9876543212", "B+", "Jayanagar, Bengaluru"),
            ("ADM-2026-004", "Kabir", "Sethi", date(2014, 9, 14), campuses["main"], sections["main_6b"], None, "Vikram Sethi", "Neha Sethi", "kabir.sethi@gmail.com", "9876543213", "AB+", "Whitefield, Bengaluru"),
            ("ADM-2026-005", "Mira", "Das", date(2014, 12, 9), campuses["north"], sections["north_6b"], None, "Pranav Das", "Shreya Das", "mira.das@gmail.com", "9876543214", "O-", "Yelahanka, Bengaluru"),
            ("ADM-2026-006", "Arjun", "Pillai", date(2014, 5, 30), campuses["north"], sections["north_6b"], None, "Suresh Pillai", "Maya Pillai", "arjun.pillai@gmail.com", "9876543215", "B-", "Hebbal, Bengaluru"),
        ]
        students = []
        for admission_number, first_name, last_name, dob, campus, section, linked_user, father_name, mother_name, email, phone, blood_group, address in specs:
            student, _ = Student.objects.update_or_create(
                admission_number=admission_number,
                defaults={
                    "campus": campus,
                    "section": section,
                    "user": linked_user,
                    "first_name": first_name,
                    "last_name": last_name,
                    "date_of_birth": dob,
                    "father_name": father_name,
                    "mother_name": mother_name,
                    "contact_email": email,
                    "phone_number": phone,
                    "alternate_phone_number": "",
                    "address": address,
                    "blood_group": blood_group,
                    "medical_notes": "No known concerns.",
                    "status": "active",
                },
            )
            students.append(student)
        for student in students[:2]:
            StudentGuardian.objects.update_or_create(
                student=student,
                guardian=parent_user,
                defaults={"relationship": "Parent"},
            )
        return students

    def create_attendance(self, students, sections, devices, users):
        today = timezone.localdate()
        status_cycle = [
            AttendanceStatus.PRESENT,
            AttendanceStatus.PRESENT,
            AttendanceStatus.ABSENT,
            AttendanceStatus.ON_DUTY,
        ]
        for day_offset in range(5):
            attendance_date = today - timedelta(days=day_offset)
            for index, student in enumerate(students):
                device = devices["north_face"] if student.campus.code == "M360-NORTH" else devices["main_face"]
                status_value = status_cycle[(day_offset + index) % len(status_cycle)]
                AttendanceRecord.objects.update_or_create(
                    student=student,
                    date=attendance_date,
                    defaults={
                        "section": student.section,
                        "status": status_value,
                        "marked_by": users["branch_teacher"] if student.section == sections["north_6b"] else users["teacher"],
                        "capture_method": device.device_type if day_offset % 2 == 0 else "manual",
                        "device": device if day_offset % 2 == 0 else None,
                        "source_reference": f"demo-att-{student.admission_number}-{attendance_date}",
                        "confidence_score": Decimal("97.25") if day_offset % 2 == 0 else None,
                    },
                )

    def create_fees(self, students, users):
        fee_specs = [
            ("Term 1 Tuition Fee", Decimal("12000.00"), timezone.localdate() + timedelta(days=20), Decimal("12000.00"), PaymentMethod.ONLINE),
            ("Transport Fee", Decimal("6000.00"), timezone.localdate() + timedelta(days=10), Decimal("2500.00"), PaymentMethod.CASH),
            ("Science Lab Fee", Decimal("3500.00"), timezone.localdate() - timedelta(days=8), Decimal("0.00"), PaymentMethod.CARD),
            ("Activity Fee", Decimal("2200.00"), timezone.localdate() + timedelta(days=30), Decimal("0.00"), PaymentMethod.BANK),
        ]
        for index, student in enumerate(students):
            title, amount, due_date, paid, method = fee_specs[index % len(fee_specs)]
            fee, _ = FeeAssignment.objects.update_or_create(
                student=student,
                title=title,
                defaults={"amount": amount, "due_date": due_date},
            )
            if paid > 0:
                Payment.objects.update_or_create(
                    fee_assignment=fee,
                    reference_number=f"DEMO-PAY-{student.admission_number}",
                    defaults={
                        "amount_paid": paid,
                        "paid_on": timezone.localdate() - timedelta(days=index % 3),
                        "payment_method": method,
                        "collected_by": users["finance_admin"],
                    },
                )
            fee.refresh_status()

    def create_academic_records(self, students, sections, users):
        work_specs = [
            (sections["main_5a"], "Fractions Practice Worksheet", "Mathematics", "Complete exercises 1 to 12 and submit before the next class.", 4, "published"),
            (sections["main_5a"], "Water Cycle Diagram", "Science", "Draw and label evaporation, condensation, precipitation, and collection.", 7, "published"),
            (sections["main_6b"], "English Reading Journal", "English", "Summarise chapter 3 and list new vocabulary words.", 5, "draft"),
            (sections["north_6b"], "Map Skills Assignment", "Social Science", "Mark major Indian rivers and mountain ranges on the worksheet.", 6, "published"),
        ]
        for section, title, subject, description, due_in_days, status_value in work_specs:
            AssignedWork.objects.update_or_create(
                section=section,
                title=title,
                defaults={
                    "assigned_by": users["branch_teacher"] if section == sections["north_6b"] else users["teacher"],
                    "subject": subject,
                    "description": description,
                    "due_date": timezone.localdate() + timedelta(days=due_in_days),
                    "status": status_value,
                },
            )

        resource_specs = [
            (sections["main_5a"], "Chapter 4 Class Notes", "Science", "notes", "Class notes for the water cycle and weather patterns."),
            (sections["main_5a"], "Math Formula Sheet", "Mathematics", "reference", "Quick reference sheet for fractions, decimals, and percentages."),
            (sections["main_6b"], "English Grammar Revision", "English", "assignment_help", "Practice material for tenses and sentence structure."),
            (sections["north_6b"], "Social Science Map Pack", "Social Science", "reference", "Printable map practice pack for classroom revision."),
        ]
        for section, title, subject, resource_type, description in resource_specs:
            LearningResource.objects.update_or_create(
                section=section,
                title=title,
                defaults={
                    "uploaded_by": users["branch_teacher"] if section == sections["north_6b"] else users["teacher"],
                    "subject": subject,
                    "resource_type": resource_type,
                    "description": description,
                    "file_url": f"https://example.com/resources/{title.lower().replace(' ', '-')}.pdf",
                    "published_on": timezone.localdate(),
                },
            )

        result_specs = [
            ("Unit Test 1", "Mathematics", Decimal("88"), Decimal("100"), "A"),
            ("Unit Test 1", "Science", Decimal("91"), Decimal("100"), "A+"),
            ("Unit Test 1", "English", Decimal("82"), Decimal("100"), "A"),
        ]
        for student_index, student in enumerate(students):
            for exam_name, subject, score, max_score, grade in result_specs:
                adjusted_score = max(Decimal("45"), score - Decimal(student_index * 3))
                ResultRecord.objects.update_or_create(
                    student=student,
                    exam_name=exam_name,
                    subject=subject,
                    defaults={
                        "recorded_by": users["branch_teacher"] if student.campus.code == "M360-NORTH" else users["teacher"],
                        "score": adjusted_score,
                        "max_score": max_score,
                        "grade": grade,
                        "remarks": "Connected demo record for academic reporting.",
                        "published_on": timezone.localdate(),
                    },
                )

        for index, student in enumerate(students, start=1):
            AdmitCard.objects.update_or_create(
                student=student,
                exam_name="Mid Term Examination 2026",
                defaults={
                    "issued_by": users["academic_admin"],
                    "roll_number": f"M360-{student.section.grade_name.replace(' ', '')}{student.section.section_name}-{index:03d}",
                    "exam_date": timezone.localdate() + timedelta(days=20),
                    "reporting_time": time(8, 30),
                    "venue": "Block A - Room 205" if student.campus.code == "M360-MAIN" else "North Campus - Hall 2",
                    "instructions": "Carry school ID, admit card, and required stationery.",
                    "status": "issued",
                    "issued_on": timezone.localdate(),
                },
            )

    def create_audit_events(self, users, campuses):
        events = [
            (users["admin"], AuditAction.CREATE, "Student", "ADM-2026-001", "Created linked demo student profile", campuses["main"]),
            (users["teacher"], AuditAction.UPDATE, "AttendanceRecord", "Grade 5-A", "Bulk attendance updated for Grade 5-A", campuses["main"]),
            (users["finance_admin"], AuditAction.CREATE, "Payment", "DEMO-PAY-ADM-2026-001", "Recorded full tuition payment", campuses["main"]),
            (users["academic_admin"], AuditAction.CREATE, "AdmitCard", "Mid Term Examination 2026", "Issued mid-term admit cards", campuses["main"]),
            (users["branch_admin"], AuditAction.CREATE, "AttendanceDevice", "M360-NORTH-FACE-01", "Configured north campus face terminal", campuses["north"]),
        ]
        for actor, action, entity_type, entity_id, summary, campus in events:
            AuditEvent.objects.update_or_create(
                actor=actor,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                defaults={
                    "summary": summary,
                    "ip_address": "127.0.0.1",
                    "metadata": {"campus": campus.code, "demo": True},
                },
            )

    def create_notifications_and_support(self, users, campuses):
        announcements = [
            (
                users["admin"],
                "Daily ERP announcement",
                "Attendance, homework, fee receipts, and learner records should be reviewed before the end of day.",
                "all",
            ),
            (
                users["academic_admin"],
                "Academic records update",
                "Teachers should publish assigned work and resources for active sections before 4 PM.",
                "staff",
            ),
            (
                users["finance_admin"],
                "Fee desk timing",
                "Students and parents can contact the office for receipts and payment clarification between 10 AM and 2 PM.",
                "learners",
            ),
        ]
        for created_by, title, message, audience in announcements:
            Announcement.objects.update_or_create(
                title=title,
                defaults={
                    "message": message,
                    "audience": audience,
                    "created_by": created_by,
                    "is_active": True,
                    "publish_on": timezone.now(),
                },
            )

        tickets = [
            (
                campuses["main"],
                users["teacher"],
                "Attendance device sync issue",
                "Main gate face terminal has delayed sync for Grade 5-A attendance.",
                "attendance",
                "high",
                SupportTicketStatus.OPEN,
                "",
            ),
            (
                campuses["main"],
                users["student"],
                "Unable to download admit card",
                "The learner portal shows the admit card, but download is not opening.",
                "student_portal",
                "urgent",
                SupportTicketStatus.OPEN,
                "",
            ),
            (
                campuses["main"],
                users["parent"],
                "Fee receipt correction",
                "Receipt spelling correction requested for the last online payment.",
                "fees",
                "normal",
                SupportTicketStatus.RESOLVED,
                "Corrected receipt has been shared with the parent.",
            ),
        ]
        for campus, created_by, subject, message, category, priority, status_value, response_note in tickets:
            SupportTicket.objects.update_or_create(
                created_by=created_by,
                subject=subject,
                defaults={
                    "campus": campus,
                    "message": message,
                    "category": category,
                    "priority": priority,
                    "status": status_value,
                    "response_note": response_note,
                    "reviewed_by": users["super_admin"] if status_value == SupportTicketStatus.RESOLVED else None,
                    "resolved_at": timezone.now() if status_value == SupportTicketStatus.RESOLVED else None,
                },
            )

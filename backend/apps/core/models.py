from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone


class AuditModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Campus(AuditModel):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True)
    logo_url = models.TextField(blank=True)
    logo_alt_text = models.CharField(max_length=160, blank=True)
    database_alias = models.CharField(
        max_length=64,
        blank=True,
        help_text="Optional Django database alias used when this campus is isolated in its own database.",
    )
    database_name = models.CharField(
        max_length=128,
        blank=True,
        help_text="Optional physical database name for operator reference.",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class AcademicSession(AuditModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="sessions")
    name = models.CharField(max_length=120)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return f"{self.campus.code} {self.name}"


class ClassSection(AuditModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="sections")
    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    grade_name = models.CharField(max_length=50)
    section_name = models.CharField(max_length=20)
    class_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_sections",
    )

    class Meta:
        ordering = ["grade_name", "section_name"]
        unique_together = ("session", "grade_name", "section_name")

    def __str__(self) -> str:
        return f"{self.grade_name}-{self.section_name}"

    def clean(self) -> None:
        if self.session_id and self.campus_id and self.session.campus_id != self.campus_id:
            raise ValidationError({"session": "Session must belong to the selected campus."})


class TeacherSubjectAllocation(AuditModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="teacher_subject_allocations")
    section = models.ForeignKey(ClassSection, on_delete=models.CASCADE, related_name="subject_allocations")
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subject_allocations",
    )
    subject = models.CharField(max_length=80)
    weekly_periods = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(60)])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["campus__name", "section__grade_name", "section__section_name", "subject"]
        unique_together = ("section", "teacher", "subject")
        indexes = [
            models.Index(fields=["teacher", "is_active"]),
            models.Index(fields=["campus", "subject"]),
        ]

    def __str__(self) -> str:
        return f"{self.teacher} - {self.section} - {self.subject}"

    def clean(self) -> None:
        self.subject = (self.subject or "").strip()
        if self.section_id and self.campus_id and self.section.campus_id != self.campus_id:
            raise ValidationError({"section": "Section must belong to the selected campus."})
        if self.teacher_id and getattr(self.teacher, "role", None) != "teacher":
            raise ValidationError({"teacher": "Subject allocation must be assigned to a teacher user."})
        if not self.subject:
            raise ValidationError({"subject": "Subject is required."})


class StudentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ALUMNI = "alumni", "Alumni"


class AttendanceStatus(models.TextChoices):
    PRESENT = "present", "Present"
    ABSENT = "absent", "Absent"
    ON_DUTY = "on_duty", "On Duty"


class FeeStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PARTIAL = "partial", "Partial"
    PAID = "paid", "Paid"
    OVERDUE = "overdue", "Overdue"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Cash"
    CARD = "card", "Card"
    BANK = "bank", "Bank"
    ONLINE = "online", "Online"


class CampusMemberRole(models.TextChoices):
    IT_ADMIN = "it_admin", "IT Admin"
    ACADEMIC_ADMIN = "academic_admin", "Academic Admin"
    FINANCE_ADMIN = "finance_admin", "Finance Admin"
    HR_ADMIN = "hr_admin", "HR Admin"
    TEACHER = "teacher", "Teacher"
    SUPPORT = "support", "Support"


class AttendanceCaptureMethod(models.TextChoices):
    MANUAL = "manual", "Manual"
    FACE_RECOGNITION = "face_recognition", "Face Recognition"
    FINGERPRINT = "fingerprint", "Fingerprint"
    CARD_SCAN = "card_scan", "Card Scan"


class DeviceStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    MAINTENANCE = "maintenance", "Maintenance"


class RS485Function(models.TextChoices):
    SOFTWARE = "software", "Software"
    HARDWARE = "hardware", "Hardware"
    DISABLED = "disabled", "Disabled"


class StaffAttendanceStatus(models.TextChoices):
    PRESENT = "present", "Present"
    ABSENT = "absent", "Absent"
    LATE = "late", "Late"
    HALF_DAY = "half_day", "Half Day"
    ON_LEAVE = "on_leave", "On Leave"


class StaffEmploymentType(models.TextChoices):
    FULL_TIME = "full_time", "Full time"
    PART_TIME = "part_time", "Part time"
    CONTRACT = "contract", "Contract"


class StaffProfileStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    EXITED = "exited", "Exited"


class Weekday(models.IntegerChoices):
    MONDAY = 1, "Monday"
    TUESDAY = 2, "Tuesday"
    WEDNESDAY = 3, "Wednesday"
    THURSDAY = 4, "Thursday"
    FRIDAY = 5, "Friday"
    SATURDAY = 6, "Saturday"
    SUNDAY = 7, "Sunday"


class LibraryBookStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    LOST = "lost", "Lost"


class LibraryLoanStatus(models.TextChoices):
    ISSUED = "issued", "Issued"
    RETURNED = "returned", "Returned"
    OVERDUE = "overdue", "Overdue"


class ApprovalStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class AnnouncementAudience(models.TextChoices):
    ALL = "all", "All users"
    ADMINS = "admins", "Admins"
    STAFF = "staff", "Teachers and staff"
    LEARNERS = "learners", "Students and parents"


class SupportTicketStatus(models.TextChoices):
    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In Progress"
    RESOLVED = "resolved", "Resolved"


class SupportTicketPriority(models.TextChoices):
    NORMAL = "normal", "Normal"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class AuditAction(models.TextChoices):
    CREATE = "create", "Create"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    LOGIN = "login", "Login"
    EXPORT = "export", "Export"


class AcademicWorkStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    CLOSED = "closed", "Closed"


class ResourceType(models.TextChoices):
    NOTES = "notes", "Notes"
    SYLLABUS = "syllabus", "Syllabus"
    ASSIGNMENT_HELP = "assignment_help", "Assignment Help"
    REFERENCE = "reference", "Reference"


class AdmitCardStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ISSUED = "issued", "Issued"
    BLOCKED = "blocked", "Blocked"


class AuditEvent(AuditModel):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    action = models.CharField(max_length=20, choices=AuditAction.choices)
    entity_type = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=80, blank=True)
    summary = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["actor", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} {self.entity_type} {self.entity_id}".strip()


class CampusMembership(AuditModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="campus_memberships",
    )
    role = models.CharField(max_length=32, choices=CampusMemberRole.choices)
    is_primary = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    can_configure_attendance = models.BooleanField(default=False)

    class Meta:
        ordering = ["campus__name", "user__username", "role"]
        unique_together = ("campus", "user", "role")
        indexes = [
            models.Index(fields=["campus", "role"]),
            models.Index(fields=["user", "is_primary"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.campus} ({self.role})"


class AttendanceDevice(AuditModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="attendance_devices")
    name = models.CharField(max_length=120)
    device_code = models.CharField(max_length=60, unique=True)
    device_type = models.CharField(max_length=32, choices=AttendanceCaptureMethod.choices)
    location = models.CharField(max_length=160, blank=True)
    provider = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=DeviceStatus.choices, default=DeviceStatus.ACTIVE)
    is_enabled_for_students = models.BooleanField(default=True)
    is_enabled_for_staff = models.BooleanField(default=True)
    server_required = models.BooleanField(default=True)
    use_domain_name = models.BooleanField(default=True)
    domain_name = models.CharField(max_length=180, blank=True, default="device.nialabs.in")
    server_ip = models.CharField(max_length=45, blank=True, default="192.168.000.109")
    server_port = models.PositiveIntegerField(default=7743, validators=[MinValueValidator(1), MaxValueValidator(65535)])
    heartbeat_seconds = models.PositiveIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(3600)])
    server_approval_required = models.BooleanField(default=False)
    device_numeric_id = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(999999)])
    local_port = models.PositiveIntegerField(default=5005, validators=[MinValueValidator(1), MaxValueValidator(65535)])
    baud_rate = models.PositiveIntegerField(default=38400, validators=[MinValueValidator(1200), MaxValueValidator(921600)])
    rs485_function = models.CharField(max_length=32, choices=RS485Function.choices, default=RS485Function.SOFTWARE)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    configured_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_devices_configured",
    )

    class Meta:
        ordering = ["campus__name", "name"]
        indexes = [
            models.Index(fields=["campus", "device_type"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.device_code})"


class Student(AuditModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="students")
    section = models.ForeignKey(ClassSection, on_delete=models.CASCADE, related_name="students")
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profile",
    )
    admission_number = models.CharField(max_length=40, unique=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80, blank=True)
    date_of_birth = models.DateField()
    father_name = models.CharField(max_length=120, blank=True)
    mother_name = models.CharField(max_length=120, blank=True)
    contact_email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    alternate_phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    blood_group = models.CharField(max_length=8, blank=True)
    medical_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=StudentStatus.choices, default=StudentStatus.ACTIVE)

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self) -> str:
        return self.full_name

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def clean(self) -> None:
        if self.section_id and self.campus_id and self.section.campus_id != self.campus_id:
            raise ValidationError({"section": "Section must belong to the selected campus."})
        if self.user_id and getattr(self.user, "role", None) != "student":
            raise ValidationError({"user": "Linked login user must have the student role."})


class StudentGuardian(AuditModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="guardianships")
    guardian = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_links",
    )
    relationship = models.CharField(max_length=40, default="Guardian")

    class Meta:
        unique_together = ("student", "guardian")

    def __str__(self) -> str:
        return f"{self.guardian.username} -> {self.student.full_name}"


class AttendanceRecord(AuditModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_records")
    section = models.ForeignKey(ClassSection, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField()
    subject = models.CharField(max_length=80, blank=True, default="")
    status = models.CharField(max_length=20, choices=AttendanceStatus.choices)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_marked",
    )
    capture_method = models.CharField(
        max_length=32,
        choices=AttendanceCaptureMethod.choices,
        default=AttendanceCaptureMethod.MANUAL,
    )
    device = models.ForeignKey(
        AttendanceDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_attendance_records",
    )
    source_reference = models.CharField(max_length=120, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["-date", "student__first_name"]
        unique_together = ("student", "date", "subject")
        indexes = [
            models.Index(fields=["section", "date", "subject"]),
        ]

    def __str__(self) -> str:
        return f"{self.student.full_name} {self.date} {self.status}"

    def clean(self) -> None:
        self.subject = (self.subject or "").strip()
        if self.student_id and self.section_id and self.student.section_id != self.section_id:
            raise ValidationError({"section": "Attendance section must match the student's assigned section."})
        if self.device_id and self.student_id and self.device.campus_id != self.student.campus_id:
            raise ValidationError({"device": "Attendance device must belong to the student's campus."})


class StaffAttendanceRecord(AuditModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="staff_attendance_records")
    staff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_attendance_records",
    )
    date = models.DateField()
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=StaffAttendanceStatus.choices,
        default=StaffAttendanceStatus.PRESENT,
    )
    capture_method = models.CharField(
        max_length=32,
        choices=AttendanceCaptureMethod.choices,
        default=AttendanceCaptureMethod.MANUAL,
    )
    device = models.ForeignKey(
        AttendanceDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_attendance_records",
    )
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_attendance_marked",
    )
    source_reference = models.CharField(max_length=120, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-date", "staff_user__username"]
        unique_together = ("staff_user", "date")
        indexes = [
            models.Index(fields=["campus", "date"]),
            models.Index(fields=["staff_user", "date"]),
        ]

    def __str__(self) -> str:
        return f"{self.staff_user} {self.date} {self.status}"

    def clean(self) -> None:
        if self.device_id and self.campus_id and self.device.campus_id != self.campus_id:
            raise ValidationError({"device": "Attendance device must belong to the selected campus."})
        if self.staff_user_id and getattr(self.staff_user, "role", None) in {"student", "parent"}:
            raise ValidationError({"staff_user": "Staff attendance cannot be recorded for student or parent users."})


class StaffProfile(AuditModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="staff_profiles")
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )
    employee_code = models.CharField(max_length=40, unique=True)
    designation = models.CharField(max_length=120)
    department = models.CharField(max_length=120, blank=True)
    employment_type = models.CharField(
        max_length=20,
        choices=StaffEmploymentType.choices,
        default=StaffEmploymentType.FULL_TIME,
    )
    joining_date = models.DateField()
    qualification = models.CharField(max_length=180, blank=True)
    emergency_contact = models.CharField(max_length=40, blank=True)
    status = models.CharField(
        max_length=20,
        choices=StaffProfileStatus.choices,
        default=StaffProfileStatus.ACTIVE,
    )

    class Meta:
        ordering = ["campus__name", "employee_code"]
        indexes = [
            models.Index(fields=["campus", "status"]),
            models.Index(fields=["department"]),
        ]

    def __str__(self) -> str:
        return f"{self.employee_code} - {self.user}"

    def clean(self) -> None:
        if self.user_id and getattr(self.user, "role", None) in {"student", "parent"}:
            raise ValidationError({"user": "Staff profile users must be administrators or teachers."})


class TimetableSlot(AuditModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="timetable_slots")
    section = models.ForeignKey(ClassSection, on_delete=models.CASCADE, related_name="timetable_slots")
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timetable_slots",
    )
    subject = models.CharField(max_length=80)
    day_of_week = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=80, blank=True)
    effective_from = models.DateField(default=timezone.localdate)
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["day_of_week", "start_time", "section__grade_name", "section__section_name"]
        unique_together = ("section", "day_of_week", "start_time")
        indexes = [
            models.Index(fields=["campus", "day_of_week"]),
            models.Index(fields=["teacher", "day_of_week"]),
        ]

    def __str__(self) -> str:
        return f"{self.section} {self.get_day_of_week_display()} {self.start_time} {self.subject}"

    def clean(self) -> None:
        self.subject = (self.subject or "").strip()
        if self.section_id and self.campus_id and self.section.campus_id != self.campus_id:
            raise ValidationError({"section": "Section must belong to the selected campus."})
        if self.teacher_id and getattr(self.teacher, "role", None) != "teacher":
            raise ValidationError({"teacher": "Timetable teacher must be a teacher user."})
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError({"end_time": "End time must be after start time."})
        if self.effective_to and self.effective_from and self.effective_to < self.effective_from:
            raise ValidationError({"effective_to": "End date must be on or after the effective from date."})
        if not self.subject:
            raise ValidationError({"subject": "Subject is required."})


class LibraryBook(AuditModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="library_books")
    accession_number = models.CharField(max_length=60, unique=True)
    title = models.CharField(max_length=180)
    author = models.CharField(max_length=160, blank=True)
    isbn = models.CharField(max_length=40, blank=True)
    category = models.CharField(max_length=80, blank=True)
    total_copies = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    available_copies = models.PositiveIntegerField(default=1)
    shelf_location = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=LibraryBookStatus.choices, default=LibraryBookStatus.ACTIVE)

    class Meta:
        ordering = ["title", "accession_number"]
        indexes = [
            models.Index(fields=["campus", "status"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.accession_number})"

    def clean(self) -> None:
        if self.available_copies > self.total_copies:
            raise ValidationError({"available_copies": "Available copies cannot exceed total copies."})


class LibraryLoan(AuditModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="library_loans")
    book = models.ForeignKey(LibraryBook, on_delete=models.CASCADE, related_name="loans")
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="library_loans",
    )
    staff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="library_loans",
    )
    issued_on = models.DateField(default=timezone.localdate)
    due_on = models.DateField()
    returned_on = models.DateField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=LibraryLoanStatus.choices, default=LibraryLoanStatus.ISSUED)

    class Meta:
        ordering = ["status", "due_on", "-issued_on"]
        indexes = [
            models.Index(fields=["campus", "status"]),
            models.Index(fields=["student", "status"]),
            models.Index(fields=["staff_user", "status"]),
        ]

    def __str__(self) -> str:
        borrower = self.student.full_name if self.student_id else self.staff_user
        return f"{self.book.title} -> {borrower}"

    def clean(self) -> None:
        if bool(self.student_id) == bool(self.staff_user_id):
            raise ValidationError({"student": "Select exactly one borrower: student or staff user."})
        if self.book_id and self.campus_id and self.book.campus_id != self.campus_id:
            raise ValidationError({"book": "Book must belong to the selected campus."})
        if self.student_id and self.campus_id and self.student.campus_id != self.campus_id:
            raise ValidationError({"student": "Student must belong to the selected campus."})
        if self.staff_user_id and getattr(self.staff_user, "role", None) == "student":
            raise ValidationError({"staff_user": "Use the student borrower field for student users."})
        if self.due_on and self.issued_on and self.due_on < self.issued_on:
            raise ValidationError({"due_on": "Due date must be on or after issue date."})
        if self.returned_on and self.issued_on and self.returned_on < self.issued_on:
            raise ValidationError({"returned_on": "Return date must be on or after issue date."})
        if self.fine_amount < Decimal("0"):
            raise ValidationError({"fine_amount": "Fine amount cannot be negative."})


class TransportRoute(AuditModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="transport_routes")
    name = models.CharField(max_length=120)
    route_code = models.CharField(max_length=40, unique=True)
    start_point = models.CharField(max_length=120)
    end_point = models.CharField(max_length=120)
    stops = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["campus__name", "route_code"]
        indexes = [
            models.Index(fields=["campus", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.route_code} - {self.name}"


class TransportVehicle(AuditModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="transport_vehicles")
    route = models.ForeignKey(
        TransportRoute,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicles",
    )
    vehicle_number = models.CharField(max_length=40, unique=True)
    driver_name = models.CharField(max_length=120)
    driver_phone = models.CharField(max_length=40, blank=True)
    capacity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    gps_device_id = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["campus__name", "vehicle_number"]
        indexes = [
            models.Index(fields=["campus", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.vehicle_number

    def clean(self) -> None:
        if self.route_id and self.campus_id and self.route.campus_id != self.campus_id:
            raise ValidationError({"route": "Route must belong to the selected campus."})


class StudentTransportAssignment(AuditModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="transport_assignments")
    route = models.ForeignKey(TransportRoute, on_delete=models.CASCADE, related_name="student_assignments")
    vehicle = models.ForeignKey(
        TransportVehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_assignments",
    )
    pickup_stop = models.CharField(max_length=120)
    drop_stop = models.CharField(max_length=120)
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["student__first_name", "start_date"]
        unique_together = ("student", "route", "start_date")
        indexes = [
            models.Index(fields=["route", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.student.full_name} - {self.route.route_code}"

    def clean(self) -> None:
        if self.student_id and self.route_id and self.student.campus_id != self.route.campus_id:
            raise ValidationError({"route": "Route must belong to the student's campus."})
        if self.vehicle_id and self.route_id and self.vehicle.campus_id != self.route.campus_id:
            raise ValidationError({"vehicle": "Vehicle must belong to the route campus."})
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date must be on or after start date."})
        if self.fee_amount < Decimal("0"):
            raise ValidationError({"fee_amount": "Transport fee cannot be negative."})


class HostelRoom(AuditModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="hostel_rooms")
    hostel_name = models.CharField(max_length=120)
    room_number = models.CharField(max_length=40)
    floor = models.CharField(max_length=40, blank=True)
    capacity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["campus__name", "hostel_name", "room_number"]
        unique_together = ("campus", "hostel_name", "room_number")
        indexes = [
            models.Index(fields=["campus", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.hostel_name} {self.room_number}"


class HostelAllocation(AuditModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="hostel_allocations")
    room = models.ForeignKey(HostelRoom, on_delete=models.CASCADE, related_name="allocations")
    bed_number = models.CharField(max_length=40)
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["student__first_name", "start_date"]
        unique_together = ("room", "bed_number", "start_date")
        indexes = [
            models.Index(fields=["room", "is_active"]),
            models.Index(fields=["student", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.student.full_name} - {self.room} Bed {self.bed_number}"

    def clean(self) -> None:
        if self.student_id and self.room_id and self.student.campus_id != self.room.campus_id:
            raise ValidationError({"room": "Hostel room must belong to the student's campus."})
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date must be on or after start date."})
        if self.fee_amount < Decimal("0"):
            raise ValidationError({"fee_amount": "Hostel fee cannot be negative."})


class AssignedWork(AuditModel):
    section = models.ForeignKey(ClassSection, on_delete=models.CASCADE, related_name="assigned_work")
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_work_created",
    )
    title = models.CharField(max_length=160)
    subject = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=AcademicWorkStatus.choices,
        default=AcademicWorkStatus.PUBLISHED,
    )

    class Meta:
        ordering = ["due_date", "subject", "title"]

    def __str__(self) -> str:
        return f"{self.subject} - {self.title}"


class LearningResource(AuditModel):
    section = models.ForeignKey(ClassSection, on_delete=models.CASCADE, related_name="learning_resources")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="learning_resources_uploaded",
    )
    title = models.CharField(max_length=160)
    subject = models.CharField(max_length=80)
    resource_type = models.CharField(max_length=32, choices=ResourceType.choices, default=ResourceType.NOTES)
    description = models.TextField(blank=True)
    file_url = models.URLField(blank=True)
    published_on = models.DateField(default=timezone.localdate)

    class Meta:
        ordering = ["-published_on", "subject", "title"]

    def __str__(self) -> str:
        return f"{self.subject} - {self.title}"


class ResultRecord(AuditModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="result_records")
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="results_recorded",
    )
    exam_name = models.CharField(max_length=120)
    subject = models.CharField(max_length=80)
    score = models.DecimalField(max_digits=6, decimal_places=2)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    grade = models.CharField(max_length=12, blank=True)
    remarks = models.TextField(blank=True)
    published_on = models.DateField(default=timezone.localdate)

    class Meta:
        ordering = ["-published_on", "exam_name", "subject"]
        unique_together = ("student", "exam_name", "subject")

    def __str__(self) -> str:
        return f"{self.student.full_name} - {self.exam_name} - {self.subject}"

    def clean(self) -> None:
        if self.score < Decimal("0"):
            raise ValidationError({"score": "Score cannot be negative."})
        if self.max_score <= Decimal("0"):
            raise ValidationError({"max_score": "Max score must be greater than zero."})
        if self.score > self.max_score:
            raise ValidationError({"score": "Score cannot exceed max score."})


class AdmitCard(AuditModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="admit_cards")
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admit_cards_issued",
    )
    exam_name = models.CharField(max_length=120)
    roll_number = models.CharField(max_length=40)
    exam_date = models.DateField()
    reporting_time = models.TimeField()
    venue = models.CharField(max_length=160)
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=AdmitCardStatus.choices, default=AdmitCardStatus.ISSUED)
    issued_on = models.DateField(default=timezone.localdate)

    class Meta:
        ordering = ["-exam_date", "exam_name"]
        unique_together = ("student", "exam_name")

    def __str__(self) -> str:
        return f"{self.student.full_name} - {self.exam_name}"


class FeeAssignment(AuditModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="fee_assignments")
    title = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=FeeStatus.choices, default=FeeStatus.PENDING)

    class Meta:
        ordering = ["due_date"]

    def __str__(self) -> str:
        return f"{self.student.full_name} - {self.title}"

    def refresh_status(self) -> None:
        total_paid = self.payments.aggregate(total=Sum("amount_paid")).get("total") or Decimal("0")
        if total_paid >= self.amount:
            self.status = FeeStatus.PAID
        elif total_paid > 0:
            self.status = FeeStatus.PARTIAL
        elif self.due_date < timezone.localdate():
            self.status = FeeStatus.OVERDUE
        else:
            self.status = FeeStatus.PENDING
        self.save(update_fields=["status", "updated_at"])

    def clean(self) -> None:
        if self.amount <= Decimal("0"):
            raise ValidationError({"amount": "Fee amount must be greater than zero."})


class Payment(AuditModel):
    fee_assignment = models.ForeignKey(
        FeeAssignment,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    paid_on = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    reference_number = models.CharField(max_length=60, blank=True)
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments_collected",
    )

    class Meta:
        ordering = ["-paid_on", "-created_at"]

    def __str__(self) -> str:
        return f"{self.fee_assignment} - {self.amount_paid}"

    def clean(self) -> None:
        if self.amount_paid <= Decimal("0"):
            raise ValidationError({"amount_paid": "Payment amount must be greater than zero."})
        if self.fee_assignment_id:
            existing_total = (
                self.fee_assignment.payments.exclude(pk=self.pk)
                .aggregate(total=Sum("amount_paid"))
                .get("total")
                or Decimal("0")
            )
            if existing_total + self.amount_paid > self.fee_assignment.amount:
                raise ValidationError({"amount_paid": "Payment cannot exceed the fee outstanding amount."})

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():
            super().save(*args, **kwargs)
            self.fee_assignment.refresh_status()


class ApprovalRequest(AuditModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="approval_requests")
    title = models.CharField(max_length=160)
    entity_type = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approval_requests_created",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approval_requests_reviewed",
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.TextField(blank=True)

    class Meta:
        ordering = ["status", "-created_at"]
        indexes = [
            models.Index(fields=["campus", "status"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.status})"

    def decide(self, *, status_value: str, reviewer, note: str = "") -> None:
        if status_value not in {ApprovalStatus.APPROVED, ApprovalStatus.REJECTED}:
            raise ValidationError({"status": "Decision must be approved or rejected."})
        self.status = status_value
        self.reviewed_by = reviewer
        self.decided_at = timezone.now()
        self.decision_note = note
        self.save(update_fields=["status", "reviewed_by", "decided_at", "decision_note", "updated_at"])


class Announcement(AuditModel):
    title = models.CharField(max_length=160)
    message = models.TextField()
    audience = models.CharField(
        max_length=20,
        choices=AnnouncementAudience.choices,
        default=AnnouncementAudience.ALL,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="announcements_created",
    )
    is_active = models.BooleanField(default=True)
    publish_on = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-publish_on", "-created_at"]
        indexes = [
            models.Index(fields=["audience", "is_active"]),
            models.Index(fields=["publish_on"]),
        ]

    def __str__(self) -> str:
        return self.title


class SupportTicket(AuditModel):
    campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_tickets",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_tickets_created",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_tickets_reviewed",
    )
    subject = models.CharField(max_length=160)
    message = models.TextField()
    category = models.CharField(max_length=40, default="general")
    priority = models.CharField(
        max_length=20,
        choices=SupportTicketPriority.choices,
        default=SupportTicketPriority.NORMAL,
    )
    status = models.CharField(
        max_length=20,
        choices=SupportTicketStatus.choices,
        default=SupportTicketStatus.OPEN,
    )
    response_note = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["status", "-created_at"]
        indexes = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["created_by", "created_at"]),
            models.Index(fields=["campus", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.subject} ({self.status})"

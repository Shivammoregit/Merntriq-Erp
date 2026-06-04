from rest_framework import serializers
from django.db.models import Sum

from apps.accounts.models import UserRole

from .attendance_rules import ensure_attendance_date_is_editable
from .models import (
    AcademicSession,
    AdmitCard,
    AILog,
    AssignedWork,
    ApprovalRequest,
    Announcement,
    AttendanceDevice,
    AttendanceRecord,
    AuditEvent,
    Campus,
    CampusMembership,
    ClassSection,
    Document,
    FeeAssignment,
    HostelAllocation,
    HostelRoom,
    LibraryBook,
    LibraryLoan,
    LearningResource,
    MessageTemplate,
    OutboundMessage,
    Payment,
    PaymentTransaction,
    PlatformSetting,
    ResultRecord,
    SalaryRecord,
    StaffAttendanceRecord,
    StaffProfile,
    Student,
    StudentGuardian,
    StudentTransportAssignment,
    SupportTicket,
    TeacherSubjectAllocation,
    TimetableSlot,
    TransportRoute,
    TransportVehicle,
)


class CampusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = (
            "id",
            "name",
            "code",
            "address",
            "contact_email",
            "contact_phone",
            "logo_url",
            "logo_alt_text",
            "banner_url",
            "status",
            "subscription_plan",
            "subscription_status",
            "monthly_subscription_amount",
            "billing_due_date",
            "academic_year_label",
            "enabled_modules",
            "payment_gateway_settings",
            "messaging_settings",
            "attendance_hardware_settings",
            "created_by",
            "database_alias",
            "database_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_by", "created_at", "updated_at")

    def validate_logo_url(self, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            return ""
        allowed_prefixes = ("https://", "http://", "data:image/png;", "data:image/jpeg;", "data:image/webp;", "data:image/svg+xml;")
        if not cleaned.startswith(allowed_prefixes):
            raise serializers.ValidationError("Use an http(s) URL or an uploaded PNG, JPG, WEBP, or SVG logo.")
        if len(cleaned) > 750_000:
            raise serializers.ValidationError("Logo is too large. Use an image below 500 KB.")
        return cleaned

    def validate_banner_url(self, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            return ""
        allowed_prefixes = ("https://", "http://", "data:image/png;", "data:image/jpeg;", "data:image/webp;")
        if not cleaned.startswith(allowed_prefixes):
            raise serializers.ValidationError("Use an http(s) URL or an uploaded PNG, JPG, or WEBP banner.")
        if len(cleaned) > 1_500_000:
            raise serializers.ValidationError("Banner is too large. Use an image below 1 MB.")
        return cleaned


class CampusMembershipSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    user_name = serializers.SerializerMethodField()
    user_role = serializers.CharField(source="user.role", read_only=True)

    class Meta:
        model = CampusMembership
        fields = (
            "id",
            "campus",
            "campus_name",
            "user",
            "user_name",
            "user_role",
            "role",
            "is_primary",
            "can_manage_users",
            "can_configure_attendance",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_user_name(self, obj: CampusMembership) -> str:
        return obj.user.get_full_name() or obj.user.username


class AttendanceDeviceSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    configured_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceDevice
        fields = (
            "id",
            "campus",
            "campus_name",
            "name",
            "device_code",
            "device_type",
            "location",
            "provider",
            "status",
            "is_enabled_for_students",
            "is_enabled_for_staff",
            "server_required",
            "use_domain_name",
            "domain_name",
            "server_ip",
            "server_port",
            "heartbeat_seconds",
            "server_approval_required",
            "device_numeric_id",
            "local_port",
            "baud_rate",
            "rs485_function",
            "last_seen_at",
            "configured_by",
            "configured_by_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("configured_by", "created_at", "updated_at")

    def get_configured_by_name(self, obj: AttendanceDevice) -> str:
        if not obj.configured_by:
            return ""
        return obj.configured_by.get_full_name() or obj.configured_by.username

    def validate(self, attrs):
        instance = self.instance
        default_domain_name = AttendanceDevice._meta.get_field("domain_name").default
        default_server_ip = AttendanceDevice._meta.get_field("server_ip").default
        server_required = attrs.get("server_required", getattr(instance, "server_required", True))
        use_domain_name = attrs.get("use_domain_name", getattr(instance, "use_domain_name", True))
        domain_name = attrs.get("domain_name", getattr(instance, "domain_name", default_domain_name)).strip()
        server_ip = attrs.get("server_ip", getattr(instance, "server_ip", default_server_ip)).strip()

        if server_required and use_domain_name and not domain_name:
            raise serializers.ValidationError({"domain_name": "Domain name is required when domain mode is enabled."})
        if server_required and not use_domain_name and not server_ip:
            raise serializers.ValidationError({"server_ip": "Server IP is required when domain mode is disabled."})
        attrs["domain_name"] = domain_name
        attrs["server_ip"] = server_ip
        return attrs


class AcademicSessionSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)

    class Meta:
        model = AcademicSession
        fields = (
            "id",
            "campus",
            "campus_name",
            "name",
            "start_date",
            "end_date",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class ClassSectionSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    class_teacher_name = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = ClassSection
        fields = (
            "id",
            "campus",
            "campus_name",
            "session",
            "grade_name",
            "section_name",
            "label",
            "class_teacher",
            "class_teacher_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_label(self, obj: ClassSection) -> str:
        return f"{obj.grade_name} - {obj.section_name}"

    def get_class_teacher_name(self, obj: ClassSection) -> str:
        if not obj.class_teacher:
            return ""
        return obj.class_teacher.get_full_name() or obj.class_teacher.username

    def validate(self, attrs):
        session = attrs.get("session", getattr(self.instance, "session", None))
        campus = attrs.get("campus", getattr(self.instance, "campus", None))
        if session and campus and session.campus_id != campus.id:
            raise serializers.ValidationError({"session": "Session must belong to the selected campus."})
        return attrs


class TeacherSubjectAllocationSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    section_label = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = TeacherSubjectAllocation
        fields = (
            "id",
            "campus",
            "campus_name",
            "section",
            "section_label",
            "teacher",
            "teacher_name",
            "subject",
            "weekly_periods",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_section_label(self, obj: TeacherSubjectAllocation) -> str:
        return f"{obj.section.grade_name} - {obj.section.section_name}"

    def get_teacher_name(self, obj: TeacherSubjectAllocation) -> str:
        return obj.teacher.get_full_name() or obj.teacher.username

    def validate_subject(self, value: str) -> str:
        subject = (value or "").strip()
        if not subject:
            raise serializers.ValidationError("Subject is required.")
        return subject

    def validate(self, attrs):
        campus = attrs.get("campus", getattr(self.instance, "campus", None))
        section = attrs.get("section", getattr(self.instance, "section", None))
        teacher = attrs.get("teacher", getattr(self.instance, "teacher", None))
        if campus and section and section.campus_id != campus.id:
            raise serializers.ValidationError({"section": "Section must belong to the selected campus."})
        if teacher and teacher.role != UserRole.TEACHER:
            raise serializers.ValidationError({"teacher": "Select a user with the teacher role."})
        return attrs


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    section_label = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = (
            "id",
            "campus",
            "campus_name",
            "section",
            "section_label",
            "user",
            "user_name",
            "admission_number",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "father_name",
            "mother_name",
            "contact_email",
            "phone_number",
            "alternate_phone_number",
            "address",
            "blood_group",
            "medical_notes",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_section_label(self, obj: Student) -> str:
        return f"{obj.section.grade_name} - {obj.section.section_name}"

    def get_user_name(self, obj: Student) -> str:
        if not obj.user:
            return ""
        return obj.user.get_full_name() or obj.user.username

    def validate(self, attrs):
        campus = attrs.get("campus", getattr(self.instance, "campus", None))
        section = attrs.get("section", getattr(self.instance, "section", None))
        user = attrs.get("user", getattr(self.instance, "user", None))
        if campus and section and section.campus_id != campus.id:
            raise serializers.ValidationError({"section": "Section must belong to the selected campus."})
        if user and user.role != UserRole.STUDENT:
            raise serializers.ValidationError({"user": "Linked login user must have the student role."})
        return attrs


class StudentGuardianSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    guardian_name = serializers.CharField(source="guardian.get_full_name", read_only=True)

    class Meta:
        model = StudentGuardian
        fields = (
            "id",
            "student",
            "student_name",
            "guardian",
            "guardian_name",
            "relationship",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    section_label = serializers.SerializerMethodField()
    device_name = serializers.CharField(source="device.name", read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = (
            "id",
            "student",
            "student_name",
            "section",
            "section_label",
            "date",
            "subject",
            "status",
            "marked_by",
            "capture_method",
            "device",
            "device_name",
            "source_reference",
            "confidence_score",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("marked_by", "created_at", "updated_at")

    def get_section_label(self, obj: AttendanceRecord) -> str:
        return f"{obj.section.grade_name} - {obj.section.section_name}"

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        student = attrs.get("student", getattr(self.instance, "student", None))
        section = attrs.get("section", getattr(self.instance, "section", None))
        attendance_date = attrs.get("date", getattr(self.instance, "date", None))
        if attendance_date:
            ensure_attendance_date_is_editable(attendance_date)
        if student and section and student.section_id != section.id:
            raise serializers.ValidationError({"section": "Attendance section must match the student's section."})
        subject = (attrs.get("subject", getattr(self.instance, "subject", "")) or "").strip()
        attrs["subject"] = subject
        if user and getattr(user, "role", None) == UserRole.TEACHER and section:
            is_class_teacher = section.class_teacher_id == user.id
            has_subject_access = bool(subject) and TeacherSubjectAllocation.objects.filter(
                section=section,
                teacher=user,
                subject__iexact=subject,
                is_active=True,
            ).exists()
            if not (is_class_teacher or has_subject_access):
                raise serializers.ValidationError(
                    {"section": "Teachers can mark attendance only for assigned class sections or allotted subjects."}
                )
        device = attrs.get("device", getattr(self.instance, "device", None))
        if device and student and device.campus_id != student.campus_id:
            raise serializers.ValidationError({"device": "Attendance device must belong to the student's campus."})
        return attrs


class StaffAttendanceRecordSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    staff_name = serializers.SerializerMethodField()
    staff_role = serializers.CharField(source="staff_user.role", read_only=True)
    marked_by_name = serializers.SerializerMethodField()
    device_name = serializers.CharField(source="device.name", read_only=True)

    class Meta:
        model = StaffAttendanceRecord
        fields = (
            "id",
            "campus",
            "campus_name",
            "staff_user",
            "staff_name",
            "staff_role",
            "date",
            "clock_in",
            "clock_out",
            "status",
            "capture_method",
            "device",
            "device_name",
            "marked_by",
            "marked_by_name",
            "source_reference",
            "confidence_score",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("marked_by", "created_at", "updated_at")

    def get_staff_name(self, obj: StaffAttendanceRecord) -> str:
        return obj.staff_user.get_full_name() or obj.staff_user.username

    def get_marked_by_name(self, obj: StaffAttendanceRecord) -> str:
        if not obj.marked_by:
            return ""
        return obj.marked_by.get_full_name() or obj.marked_by.username

    def validate(self, attrs):
        campus = attrs.get("campus", getattr(self.instance, "campus", None))
        staff_user = attrs.get("staff_user", getattr(self.instance, "staff_user", None))
        device = attrs.get("device", getattr(self.instance, "device", None))
        attendance_date = attrs.get("date", getattr(self.instance, "date", None))
        if attendance_date:
            ensure_attendance_date_is_editable(attendance_date)
        if staff_user and staff_user.role == UserRole.STUDENT:
            raise serializers.ValidationError({"staff_user": "Staff attendance cannot be recorded for student users."})
        if device and campus and device.campus_id != campus.id:
            raise serializers.ValidationError({"device": "Attendance device must belong to the selected campus."})
        return attrs


class StaffProfileSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    user_name = serializers.SerializerMethodField()
    user_role = serializers.CharField(source="user.role", read_only=True)

    class Meta:
        model = StaffProfile
        fields = (
            "id",
            "campus",
            "campus_name",
            "user",
            "user_name",
            "user_role",
            "employee_code",
            "designation",
            "department",
            "employment_type",
            "joining_date",
            "qualification",
            "emergency_contact",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_user_name(self, obj: StaffProfile) -> str:
        return obj.user.get_full_name() or obj.user.username

    def validate(self, attrs):
        user = attrs.get("user", getattr(self.instance, "user", None))
        if user and user.role == UserRole.STUDENT:
            raise serializers.ValidationError({"user": "Staff profile users must be administrators or teachers."})
        return attrs


class TimetableSlotSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    section_label = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    day_name = serializers.CharField(source="get_day_of_week_display", read_only=True)

    class Meta:
        model = TimetableSlot
        fields = (
            "id",
            "campus",
            "campus_name",
            "section",
            "section_label",
            "teacher",
            "teacher_name",
            "subject",
            "day_of_week",
            "day_name",
            "start_time",
            "end_time",
            "room",
            "effective_from",
            "effective_to",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_section_label(self, obj: TimetableSlot) -> str:
        return f"{obj.section.grade_name} - {obj.section.section_name}"

    def get_teacher_name(self, obj: TimetableSlot) -> str:
        if not obj.teacher:
            return ""
        return obj.teacher.get_full_name() or obj.teacher.username

    def validate(self, attrs):
        campus = attrs.get("campus", getattr(self.instance, "campus", None))
        section = attrs.get("section", getattr(self.instance, "section", None))
        teacher = attrs.get("teacher", getattr(self.instance, "teacher", None))
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))
        effective_from = attrs.get("effective_from", getattr(self.instance, "effective_from", None))
        effective_to = attrs.get("effective_to", getattr(self.instance, "effective_to", None))
        subject = (attrs.get("subject", getattr(self.instance, "subject", "")) or "").strip()
        attrs["subject"] = subject
        if campus and section and section.campus_id != campus.id:
            raise serializers.ValidationError({"section": "Section must belong to the selected campus."})
        if teacher and teacher.role != UserRole.TEACHER:
            raise serializers.ValidationError({"teacher": "Timetable teacher must be a teacher user."})
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})
        if effective_from and effective_to and effective_to < effective_from:
            raise serializers.ValidationError({"effective_to": "End date must be on or after the effective from date."})
        if not subject:
            raise serializers.ValidationError({"subject": "Subject is required."})
        return attrs


class LibraryBookSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)

    class Meta:
        model = LibraryBook
        fields = (
            "id",
            "campus",
            "campus_name",
            "accession_number",
            "title",
            "author",
            "isbn",
            "category",
            "total_copies",
            "available_copies",
            "shelf_location",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def validate(self, attrs):
        total = attrs.get("total_copies", getattr(self.instance, "total_copies", 1))
        available = attrs.get("available_copies", getattr(self.instance, "available_copies", 1))
        if available > total:
            raise serializers.ValidationError({"available_copies": "Available copies cannot exceed total copies."})
        return attrs


class LibraryLoanSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    book_title = serializers.CharField(source="book.title", read_only=True)
    borrower_name = serializers.SerializerMethodField()

    class Meta:
        model = LibraryLoan
        fields = (
            "id",
            "campus",
            "campus_name",
            "book",
            "book_title",
            "student",
            "staff_user",
            "borrower_name",
            "issued_on",
            "due_on",
            "returned_on",
            "fine_amount",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_borrower_name(self, obj: LibraryLoan) -> str:
        if obj.student_id:
            return obj.student.full_name
        if obj.staff_user_id:
            return obj.staff_user.get_full_name() or obj.staff_user.username
        return ""

    def validate(self, attrs):
        campus = attrs.get("campus", getattr(self.instance, "campus", None))
        book = attrs.get("book", getattr(self.instance, "book", None))
        student = attrs.get("student", getattr(self.instance, "student", None))
        staff_user = attrs.get("staff_user", getattr(self.instance, "staff_user", None))
        issued_on = attrs.get("issued_on", getattr(self.instance, "issued_on", None))
        due_on = attrs.get("due_on", getattr(self.instance, "due_on", None))
        returned_on = attrs.get("returned_on", getattr(self.instance, "returned_on", None))
        fine_amount = attrs.get("fine_amount", getattr(self.instance, "fine_amount", 0))
        if bool(student) == bool(staff_user):
            raise serializers.ValidationError({"student": "Select exactly one borrower: student or staff user."})
        if campus and book and book.campus_id != campus.id:
            raise serializers.ValidationError({"book": "Book must belong to the selected campus."})
        if campus and student and student.campus_id != campus.id:
            raise serializers.ValidationError({"student": "Student must belong to the selected campus."})
        if staff_user and staff_user.role == UserRole.STUDENT:
            raise serializers.ValidationError({"staff_user": "Use the student borrower field for student users."})
        if issued_on and due_on and due_on < issued_on:
            raise serializers.ValidationError({"due_on": "Due date must be on or after issue date."})
        if issued_on and returned_on and returned_on < issued_on:
            raise serializers.ValidationError({"returned_on": "Return date must be on or after issue date."})
        if fine_amount < 0:
            raise serializers.ValidationError({"fine_amount": "Fine amount cannot be negative."})
        return attrs


class TransportRouteSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)

    class Meta:
        model = TransportRoute
        fields = (
            "id",
            "campus",
            "campus_name",
            "name",
            "route_code",
            "start_point",
            "end_point",
            "stops",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class TransportVehicleSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    route_name = serializers.CharField(source="route.name", read_only=True)

    class Meta:
        model = TransportVehicle
        fields = (
            "id",
            "campus",
            "campus_name",
            "route",
            "route_name",
            "vehicle_number",
            "driver_name",
            "driver_phone",
            "capacity",
            "gps_device_id",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def validate(self, attrs):
        campus = attrs.get("campus", getattr(self.instance, "campus", None))
        route = attrs.get("route", getattr(self.instance, "route", None))
        if campus and route and route.campus_id != campus.id:
            raise serializers.ValidationError({"route": "Route must belong to the selected campus."})
        return attrs


class StudentTransportAssignmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    route_name = serializers.CharField(source="route.name", read_only=True)
    vehicle_number = serializers.CharField(source="vehicle.vehicle_number", read_only=True)

    class Meta:
        model = StudentTransportAssignment
        fields = (
            "id",
            "student",
            "student_name",
            "route",
            "route_name",
            "vehicle",
            "vehicle_number",
            "pickup_stop",
            "drop_stop",
            "start_date",
            "end_date",
            "fee_amount",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def validate(self, attrs):
        student = attrs.get("student", getattr(self.instance, "student", None))
        route = attrs.get("route", getattr(self.instance, "route", None))
        vehicle = attrs.get("vehicle", getattr(self.instance, "vehicle", None))
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        fee_amount = attrs.get("fee_amount", getattr(self.instance, "fee_amount", 0))
        if student and route and student.campus_id != route.campus_id:
            raise serializers.ValidationError({"route": "Route must belong to the student's campus."})
        if vehicle and route and vehicle.campus_id != route.campus_id:
            raise serializers.ValidationError({"vehicle": "Vehicle must belong to the route campus."})
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date must be on or after start date."})
        if fee_amount < 0:
            raise serializers.ValidationError({"fee_amount": "Transport fee cannot be negative."})
        return attrs


class HostelRoomSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)

    class Meta:
        model = HostelRoom
        fields = (
            "id",
            "campus",
            "campus_name",
            "hostel_name",
            "room_number",
            "floor",
            "capacity",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class HostelAllocationSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    room_label = serializers.SerializerMethodField()

    class Meta:
        model = HostelAllocation
        fields = (
            "id",
            "student",
            "student_name",
            "room",
            "room_label",
            "bed_number",
            "start_date",
            "end_date",
            "fee_amount",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_room_label(self, obj: HostelAllocation) -> str:
        return f"{obj.room.hostel_name} {obj.room.room_number}"

    def validate(self, attrs):
        student = attrs.get("student", getattr(self.instance, "student", None))
        room = attrs.get("room", getattr(self.instance, "room", None))
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        fee_amount = attrs.get("fee_amount", getattr(self.instance, "fee_amount", 0))
        if student and room and student.campus_id != room.campus_id:
            raise serializers.ValidationError({"room": "Hostel room must belong to the student's campus."})
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date must be on or after start date."})
        if fee_amount < 0:
            raise serializers.ValidationError({"fee_amount": "Hostel fee cannot be negative."})
        return attrs


class AssignedWorkSerializer(serializers.ModelSerializer):
    section_label = serializers.SerializerMethodField()
    assigned_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AssignedWork
        fields = (
            "id",
            "section",
            "section_label",
            "assigned_by",
            "assigned_by_name",
            "title",
            "subject",
            "description",
            "due_date",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("assigned_by", "created_at", "updated_at")

    def get_section_label(self, obj: AssignedWork) -> str:
        return f"{obj.section.grade_name} - {obj.section.section_name}"

    def get_assigned_by_name(self, obj: AssignedWork) -> str:
        if not obj.assigned_by:
            return ""
        return obj.assigned_by.get_full_name() or obj.assigned_by.username

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        section = attrs.get("section", getattr(self.instance, "section", None))
        if user and getattr(user, "role", None) == UserRole.TEACHER and section and section.class_teacher_id != user.id:
            raise serializers.ValidationError({"section": "Teachers can assign work only for assigned sections."})
        return attrs


class LearningResourceSerializer(serializers.ModelSerializer):
    section_label = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = LearningResource
        fields = (
            "id",
            "section",
            "section_label",
            "uploaded_by",
            "uploaded_by_name",
            "title",
            "subject",
            "resource_type",
            "description",
            "file_url",
            "published_on",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uploaded_by", "created_at", "updated_at")

    def get_section_label(self, obj: LearningResource) -> str:
        return f"{obj.section.grade_name} - {obj.section.section_name}"

    def get_uploaded_by_name(self, obj: LearningResource) -> str:
        if not obj.uploaded_by:
            return ""
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        section = attrs.get("section", getattr(self.instance, "section", None))
        if user and getattr(user, "role", None) == UserRole.TEACHER and section and section.class_teacher_id != user.id:
            raise serializers.ValidationError({"section": "Teachers can upload resources only for assigned sections."})
        return attrs


class ResultRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    section_label = serializers.SerializerMethodField()
    recorded_by_name = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = ResultRecord
        fields = (
            "id",
            "student",
            "student_name",
            "section_label",
            "recorded_by",
            "recorded_by_name",
            "exam_name",
            "subject",
            "score",
            "max_score",
            "percentage",
            "grade",
            "remarks",
            "published_on",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("recorded_by", "created_at", "updated_at")

    def get_section_label(self, obj: ResultRecord) -> str:
        return f"{obj.student.section.grade_name} - {obj.student.section.section_name}"

    def get_recorded_by_name(self, obj: ResultRecord) -> str:
        if not obj.recorded_by:
            return ""
        return obj.recorded_by.get_full_name() or obj.recorded_by.username

    def get_percentage(self, obj: ResultRecord) -> str:
        if not obj.max_score:
            return "0"
        return str(round((obj.score / obj.max_score) * 100, 2))

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        student = attrs.get("student", getattr(self.instance, "student", None))
        score = attrs.get("score", getattr(self.instance, "score", None))
        max_score = attrs.get("max_score", getattr(self.instance, "max_score", None))
        if user and getattr(user, "role", None) == UserRole.TEACHER and student and student.section.class_teacher_id != user.id:
            raise serializers.ValidationError({"student": "Teachers can record results only for assigned sections."})
        if score is not None and score < 0:
            raise serializers.ValidationError({"score": "Score cannot be negative."})
        if max_score is not None and max_score <= 0:
            raise serializers.ValidationError({"max_score": "Max score must be greater than zero."})
        if score is not None and max_score is not None and score > max_score:
            raise serializers.ValidationError({"score": "Score cannot exceed max score."})
        return attrs


class AdmitCardSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    admission_number = serializers.CharField(source="student.admission_number", read_only=True)
    section_label = serializers.SerializerMethodField()
    issued_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AdmitCard
        fields = (
            "id",
            "student",
            "student_name",
            "admission_number",
            "section_label",
            "issued_by",
            "issued_by_name",
            "exam_name",
            "roll_number",
            "exam_date",
            "reporting_time",
            "venue",
            "instructions",
            "status",
            "issued_on",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("issued_by", "created_at", "updated_at")

    def get_section_label(self, obj: AdmitCard) -> str:
        return f"{obj.student.section.grade_name} - {obj.student.section.section_name}"

    def get_issued_by_name(self, obj: AdmitCard) -> str:
        if not obj.issued_by:
            return ""
        return obj.issued_by.get_full_name() or obj.issued_by.username

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        student = attrs.get("student", getattr(self.instance, "student", None))
        if user and getattr(user, "role", None) == UserRole.TEACHER and student and student.section.class_teacher_id != user.id:
            raise serializers.ValidationError({"student": "Teachers can issue admit cards only for assigned sections."})
        return attrs


class FeeAssignmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    amount_paid = serializers.SerializerMethodField()
    outstanding_amount = serializers.SerializerMethodField()

    class Meta:
        model = FeeAssignment
        fields = (
            "id",
            "student",
            "student_name",
            "title",
            "amount",
            "amount_paid",
            "outstanding_amount",
            "due_date",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("status",)

    def get_amount_paid(self, obj: FeeAssignment) -> str:
        paid = obj.payments.aggregate(total=Sum("amount_paid")).get("total") or 0
        return str(paid)

    def get_outstanding_amount(self, obj: FeeAssignment) -> str:
        paid = obj.payments.aggregate(total=Sum("amount_paid")).get("total") or 0
        return str(max(obj.amount - paid, 0))

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Fee amount must be greater than zero.")
        return value


class PaymentSerializer(serializers.ModelSerializer):
    fee_title = serializers.CharField(source="fee_assignment.title", read_only=True)
    student_name = serializers.CharField(source="fee_assignment.student.full_name", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "fee_assignment",
            "fee_title",
            "student_name",
            "amount_paid",
            "paid_on",
            "payment_method",
            "reference_number",
            "collected_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("collected_by", "created_at", "updated_at")

    def validate_amount_paid(self, value):
        if value <= 0:
            raise serializers.ValidationError("Payment amount must be greater than zero.")
        return value

    def validate(self, attrs):
        fee_assignment = attrs.get("fee_assignment", getattr(self.instance, "fee_assignment", None))
        amount_paid = attrs.get("amount_paid", getattr(self.instance, "amount_paid", None))
        if fee_assignment and amount_paid:
            existing_total = (
                fee_assignment.payments.exclude(pk=getattr(self.instance, "pk", None))
                .aggregate(total=Sum("amount_paid"))
                .get("total")
                or 0
            )
            if existing_total + amount_paid > fee_assignment.amount:
                raise serializers.ValidationError({"amount_paid": "Payment cannot exceed the fee outstanding amount."})
        return attrs


class PaymentTransactionSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    fee_title = serializers.CharField(source="fee_assignment.title", read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PaymentTransaction
        fields = (
            "id",
            "campus",
            "campus_name",
            "student",
            "student_name",
            "fee_assignment",
            "fee_title",
            "payment",
            "provider",
            "method",
            "amount",
            "currency",
            "status",
            "gateway_order_id",
            "gateway_payment_id",
            "gateway_signature",
            "receipt_number",
            "webhook_verified",
            "raw_payload",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_by", "created_at", "updated_at")

    def get_created_by_name(self, obj: PaymentTransaction) -> str:
        if not obj.created_by:
            return ""
        return obj.created_by.get_full_name() or obj.created_by.username

    def validate(self, attrs):
        campus = attrs.get("campus", getattr(self.instance, "campus", None))
        student = attrs.get("student", getattr(self.instance, "student", None))
        fee_assignment = attrs.get("fee_assignment", getattr(self.instance, "fee_assignment", None))
        amount = attrs.get("amount", getattr(self.instance, "amount", None))
        if amount is not None and amount <= 0:
            raise serializers.ValidationError({"amount": "Transaction amount must be greater than zero."})
        if campus and student and student.campus_id != campus.id:
            raise serializers.ValidationError({"student": "Student must belong to the selected campus."})
        if campus and fee_assignment and fee_assignment.student.campus_id != campus.id:
            raise serializers.ValidationError({"fee_assignment": "Fee assignment must belong to the selected campus."})
        return attrs


class SalaryRecordSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    staff_name = serializers.SerializerMethodField()
    staff_role = serializers.CharField(source="staff_user.role", read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = SalaryRecord
        fields = (
            "id",
            "campus",
            "campus_name",
            "staff_user",
            "staff_name",
            "staff_role",
            "month",
            "year",
            "present_days",
            "absent_days",
            "leave_days",
            "half_days",
            "gross_salary",
            "deductions",
            "bonus",
            "final_salary",
            "payment_status",
            "paid_on",
            "slip_url",
            "status",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_by", "created_at", "updated_at")

    def get_staff_name(self, obj: SalaryRecord) -> str:
        return obj.staff_user.get_full_name() or obj.staff_user.username

    def get_created_by_name(self, obj: SalaryRecord) -> str:
        if not obj.created_by:
            return ""
        return obj.created_by.get_full_name() or obj.created_by.username

    def validate(self, attrs):
        staff_user = attrs.get("staff_user", getattr(self.instance, "staff_user", None))
        if staff_user and staff_user.role == UserRole.STUDENT:
            raise serializers.ValidationError({"staff_user": "Salary records cannot be created for student users."})
        money_fields = ("gross_salary", "deductions", "bonus", "final_salary")
        day_fields = ("present_days", "absent_days", "leave_days", "half_days")
        for field in money_fields + day_fields:
            value = attrs.get(field, getattr(self.instance, field, 0))
            if value is not None and value < 0:
                raise serializers.ValidationError({field: "Value cannot be negative."})
        return attrs


class MessageTemplateSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MessageTemplate
        fields = (
            "id",
            "campus",
            "campus_name",
            "name",
            "trigger",
            "channel",
            "subject",
            "body",
            "variables",
            "status",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_by", "created_at", "updated_at")

    def get_created_by_name(self, obj: MessageTemplate) -> str:
        if not obj.created_by:
            return ""
        return obj.created_by.get_full_name() or obj.created_by.username


class OutboundMessageSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    template_name = serializers.CharField(source="template.name", read_only=True)
    recipient_user_name = serializers.SerializerMethodField()
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = OutboundMessage
        fields = (
            "id",
            "campus",
            "campus_name",
            "template",
            "template_name",
            "recipient_user",
            "recipient_user_name",
            "student",
            "student_name",
            "channel",
            "recipient",
            "subject",
            "body",
            "status",
            "provider",
            "provider_reference",
            "error_message",
            "sent_at",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_by", "sent_at", "created_at", "updated_at")

    def get_recipient_user_name(self, obj: OutboundMessage) -> str:
        if not obj.recipient_user:
            return ""
        return obj.recipient_user.get_full_name() or obj.recipient_user.username

    def get_created_by_name(self, obj: OutboundMessage) -> str:
        if not obj.created_by:
            return ""
        return obj.created_by.get_full_name() or obj.created_by.username

    def validate(self, attrs):
        campus = attrs.get("campus", getattr(self.instance, "campus", None))
        student = attrs.get("student", getattr(self.instance, "student", None))
        template = attrs.get("template", getattr(self.instance, "template", None))
        if campus and student and student.campus_id != campus.id:
            raise serializers.ValidationError({"student": "Student must belong to the selected campus."})
        if campus and template and template.campus_id and template.campus_id != campus.id:
            raise serializers.ValidationError({"template": "Template must belong to the selected campus or be global."})
        return attrs


class AILogSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    user_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AILog
        fields = (
            "id",
            "campus",
            "campus_name",
            "user",
            "user_name",
            "role",
            "feature",
            "prompt",
            "response",
            "metadata",
            "status",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_by", "created_at", "updated_at")

    def get_user_name(self, obj: AILog) -> str:
        if not obj.user:
            return ""
        return obj.user.get_full_name() or obj.user.username

    def get_created_by_name(self, obj: AILog) -> str:
        if not obj.created_by:
            return ""
        return obj.created_by.get_full_name() or obj.created_by.username


class DocumentSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "id",
            "campus",
            "campus_name",
            "student",
            "student_name",
            "uploaded_by",
            "uploaded_by_name",
            "title",
            "document_type",
            "file_url",
            "status",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uploaded_by", "created_by", "created_at", "updated_at")

    def get_uploaded_by_name(self, obj: Document) -> str:
        if not obj.uploaded_by:
            return ""
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username

    def get_created_by_name(self, obj: Document) -> str:
        if not obj.created_by:
            return ""
        return obj.created_by.get_full_name() or obj.created_by.username

    def validate(self, attrs):
        campus = attrs.get("campus", getattr(self.instance, "campus", None))
        student = attrs.get("student", getattr(self.instance, "student", None))
        if campus and student and student.campus_id != campus.id:
            raise serializers.ValidationError({"student": "Student must belong to the selected campus."})
        return attrs


class PlatformSettingSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PlatformSetting
        fields = (
            "id",
            "campus",
            "campus_name",
            "key",
            "value",
            "status",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_by", "created_at", "updated_at")

    def get_created_by_name(self, obj: PlatformSetting) -> str:
        if not obj.created_by:
            return ""
        return obj.created_by.get_full_name() or obj.created_by.username


class AuditEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditEvent
        fields = (
            "id",
            "actor",
            "actor_name",
            "action",
            "entity_type",
            "entity_id",
            "summary",
            "ip_address",
            "metadata",
            "created_at",
        )
        read_only_fields = fields

    def get_actor_name(self, obj: AuditEvent) -> str:
        if not obj.actor:
            return ""
        return obj.actor.get_full_name() or obj.actor.username


class ApprovalRequestSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    requested_by_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalRequest
        fields = (
            "id",
            "campus",
            "campus_name",
            "title",
            "entity_type",
            "entity_id",
            "description",
            "payload",
            "status",
            "requested_by",
            "requested_by_name",
            "reviewed_by",
            "reviewed_by_name",
            "decided_at",
            "decision_note",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "status",
            "requested_by",
            "reviewed_by",
            "decided_at",
            "decision_note",
            "created_at",
            "updated_at",
        )

    def get_requested_by_name(self, obj: ApprovalRequest) -> str:
        if not obj.requested_by:
            return ""
        return obj.requested_by.get_full_name() or obj.requested_by.username

    def get_reviewed_by_name(self, obj: ApprovalRequest) -> str:
        if not obj.reviewed_by:
            return ""
        return obj.reviewed_by.get_full_name() or obj.reviewed_by.username


class AnnouncementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = (
            "id",
            "title",
            "message",
            "audience",
            "created_by",
            "created_by_name",
            "is_active",
            "publish_on",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_by", "created_at", "updated_at")

    def get_created_by_name(self, obj: Announcement) -> str:
        if not obj.created_by:
            return "Admin team"
        return obj.created_by.get_full_name() or obj.created_by.username


class SupportTicketSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    created_by_name = serializers.SerializerMethodField()
    created_by_role = serializers.CharField(source="created_by.role", read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = (
            "id",
            "campus",
            "campus_name",
            "created_by",
            "created_by_name",
            "created_by_role",
            "reviewed_by",
            "reviewed_by_name",
            "subject",
            "message",
            "category",
            "priority",
            "status",
            "response_note",
            "resolved_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "created_by",
            "created_by_name",
            "created_by_role",
            "reviewed_by",
            "reviewed_by_name",
            "resolved_at",
            "created_at",
            "updated_at",
        )

    def get_created_by_name(self, obj: SupportTicket) -> str:
        return obj.created_by.get_full_name() or obj.created_by.username

    def get_reviewed_by_name(self, obj: SupportTicket) -> str:
        if not obj.reviewed_by:
            return ""
        return obj.reviewed_by.get_full_name() or obj.reviewed_by.username

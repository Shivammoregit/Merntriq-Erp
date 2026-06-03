from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserRole

from .models import (
    AcademicSession,
    AdmitCard,
    AssignedWork,
    Announcement,
    ApprovalRequest,
    ApprovalStatus,
    AttendanceCaptureMethod,
    AttendanceDevice,
    AttendanceRecord,
    AttendanceStatus,
    AuditAction,
    AuditEvent,
    Campus,
    CampusMembership,
    ClassSection,
    FeeAssignment,
    HostelAllocation,
    HostelRoom,
    LibraryBook,
    LibraryLoan,
    LearningResource,
    Payment,
    ResultRecord,
    StaffAttendanceRecord,
    StaffProfile,
    StaffAttendanceStatus,
    Student,
    StudentGuardian,
    StudentTransportAssignment,
    SupportTicket,
    SupportTicketStatus,
    TeacherSubjectAllocation,
    TimetableSlot,
    TransportRoute,
    TransportVehicle,
)
from .attendance_rules import ensure_attendance_date_is_editable
from .permissions import RoleAccessPermission
from .serializers import (
    AcademicSessionSerializer,
    AdmitCardSerializer,
    AssignedWorkSerializer,
    AnnouncementSerializer,
    ApprovalRequestSerializer,
    AttendanceDeviceSerializer,
    AttendanceRecordSerializer,
    AuditEventSerializer,
    CampusSerializer,
    CampusMembershipSerializer,
    ClassSectionSerializer,
    FeeAssignmentSerializer,
    HostelAllocationSerializer,
    HostelRoomSerializer,
    LibraryBookSerializer,
    LibraryLoanSerializer,
    LearningResourceSerializer,
    PaymentSerializer,
    ResultRecordSerializer,
    StaffAttendanceRecordSerializer,
    StaffProfileSerializer,
    StudentSerializer,
    StudentGuardianSerializer,
    StudentTransportAssignmentSerializer,
    SupportTicketSerializer,
    TeacherSubjectAllocationSerializer,
    TimetableSlotSerializer,
    TransportRouteSerializer,
    TransportVehicleSerializer,
)

ADMIN_ROLES = (UserRole.SUPER_ADMIN, UserRole.ADMIN)
READ_ROLES = (UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT, UserRole.PARENT)
ACADEMIC_WRITE_ROLES = ADMIN_ROLES + (UserRole.TEACHER,)


def teacher_section_q(user):
    return Q(class_teacher=user) | Q(subject_allocations__teacher=user, subject_allocations__is_active=True)


def teacher_has_subject_access(user, section: ClassSection, subject: str) -> bool:
    subject = (subject or "").strip()
    if section.class_teacher_id == user.id:
        return True
    if not subject:
        return False
    return TeacherSubjectAllocation.objects.filter(
        section=section,
        teacher=user,
        subject__iexact=subject,
        is_active=True,
    ).exists()


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok", "service": "mentriq360-api"})


def get_client_ip(request) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class RoleScopedModelViewSet(viewsets.ModelViewSet):
    permission_classes = [RoleAccessPermission]
    read_roles = READ_ROLES
    write_roles = ADMIN_ROLES
    campus_filter_path: str | None = None

    def filter_queryset_by_role(self, queryset):
        return queryset.none()

    def admin_campus_ids(self) -> list[int]:
        user = self.request.user
        if getattr(user, "role", None) != UserRole.ADMIN:
            return []
        return list(
            CampusMembership.objects.filter(user=user)
            .values_list("campus_id", flat=True)
            .distinct()
        )

    def filter_admin_queryset(self, queryset):
        user = self.request.user
        if getattr(user, "role", None) == UserRole.SUPER_ADMIN:
            return queryset
        campus_ids = self.admin_campus_ids()
        if not campus_ids:
            return queryset.none()
        if not self.campus_filter_path:
            return queryset
        return queryset.filter(**{f"{self.campus_filter_path}__in": campus_ids})

    def campus_id_from_attrs(self, attrs) -> int | None:
        campus = attrs.get("campus")
        if campus:
            return campus.id
        student = attrs.get("student")
        if student:
            return student.campus_id
        section = attrs.get("section")
        if section:
            return section.campus_id
        fee_assignment = attrs.get("fee_assignment")
        if fee_assignment:
            return fee_assignment.student.campus_id
        device = attrs.get("device")
        if device:
            return device.campus_id
        book = attrs.get("book")
        if book:
            return book.campus_id
        route = attrs.get("route")
        if route:
            return route.campus_id
        vehicle = attrs.get("vehicle")
        if vehicle:
            return vehicle.campus_id
        room = attrs.get("room")
        if room:
            return room.campus_id
        return None

    def ensure_admin_payload_scope(self, attrs) -> None:
        user = self.request.user
        if getattr(user, "role", None) == UserRole.SUPER_ADMIN:
            return
        if getattr(user, "role", None) != UserRole.ADMIN:
            return
        campus_id = self.campus_id_from_attrs(attrs)
        if campus_id is None:
            return
        if campus_id not in self.admin_campus_ids():
            raise PermissionDenied("This record belongs to a campus outside your admin scope.")

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not getattr(user, "is_authenticated", False):
            return queryset.none()
        if getattr(user, "role", None) in ADMIN_ROLES:
            return self.filter_admin_queryset(queryset)
        return self.filter_queryset_by_role(queryset)

    def audit_entity_type(self) -> str:
        return self.queryset.model.__name__

    def write_audit(self, action: str, instance) -> None:
        user = self.request.user
        if not getattr(user, "is_authenticated", False):
            return
        AuditEvent.objects.create(
            actor=user,
            action=action,
            entity_type=self.audit_entity_type(),
            entity_id=str(getattr(instance, "pk", "")),
            summary=str(instance),
            ip_address=get_client_ip(self.request),
        )

    def perform_create(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save()
        self.write_audit(AuditAction.CREATE, instance)

    def perform_update(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save()
        self.write_audit(AuditAction.UPDATE, instance)

    def perform_destroy(self, instance):
        self.write_audit(AuditAction.DELETE, instance)
        instance.delete()


class CampusViewSet(RoleScopedModelViewSet):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer
    campus_filter_path = "id"
    write_roles = (UserRole.SUPER_ADMIN,)

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(
                Q(sections__class_teacher=user)
                | Q(sections__subject_allocations__teacher=user, sections__subject_allocations__is_active=True)
            ).distinct()
        if user.role == UserRole.STUDENT:
            return queryset.filter(students__user=user).distinct()
        if user.role == UserRole.PARENT:
            return queryset.filter(students__guardianships__guardian=user).distinct()
        return queryset.none()


class CampusMembershipViewSet(RoleScopedModelViewSet):
    queryset = CampusMembership.objects.select_related("campus", "user")
    serializer_class = CampusMembershipSerializer
    campus_filter_path = "campus_id"
    read_roles = ADMIN_ROLES
    write_roles = ADMIN_ROLES
    filterset_fields = ("campus", "user", "role", "is_primary")

    def campus_id_from_attrs(self, attrs) -> int | None:
        campus = attrs.get("campus")
        if campus:
            return campus.id
        return None


class AttendanceDeviceViewSet(RoleScopedModelViewSet):
    queryset = AttendanceDevice.objects.select_related("campus", "configured_by")
    serializer_class = AttendanceDeviceSerializer
    campus_filter_path = "campus_id"
    read_roles = ADMIN_ROLES + (UserRole.TEACHER,)
    write_roles = ADMIN_ROLES
    filterset_fields = ("campus", "device_type", "status", "is_enabled_for_students", "is_enabled_for_staff")
    search_fields = ("name", "device_code", "location", "provider")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(
                Q(campus__sections__class_teacher=user)
                | Q(campus__sections__subject_allocations__teacher=user, campus__sections__subject_allocations__is_active=True)
            ).distinct()
        return queryset.none()

    def get_throttles(self):
        if getattr(self, "action", None) == "capture":
            self.throttle_scope = "hardware_capture"
        return super().get_throttles()

    def perform_create(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save(configured_by=self.request.user)
        self.write_audit(AuditAction.CREATE, instance)

    def perform_update(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save(configured_by=self.request.user)
        self.write_audit(AuditAction.UPDATE, instance)

    @action(detail=True, methods=["post"], url_path="capture")
    def capture(self, request, pk=None):
        device = self.get_object()
        if getattr(request.user, "role", None) not in ADMIN_ROLES:
            raise PermissionDenied("Only campus admins can ingest hardware attendance.")

        person_type = request.data.get("person_type", "student")
        external_id = request.data.get("external_id")
        if not external_id:
            raise ValidationError({"external_id": "Provide an admission number or username."})

        captured_at_raw = request.data.get("captured_at")
        captured_at = parse_datetime(captured_at_raw) if captured_at_raw else timezone.now()
        if captured_at is None:
            raise ValidationError({"captured_at": "Use an ISO datetime value."})
        if timezone.is_naive(captured_at):
            captured_at = timezone.make_aware(captured_at)

        confidence = request.data.get("confidence_score")
        source_reference = request.data.get("source_reference", "")
        record_status = request.data.get("status", AttendanceStatus.PRESENT)
        attendance_date = ensure_attendance_date_is_editable(captured_at.date())

        if person_type == "student":
            if record_status not in {choice.value for choice in AttendanceStatus}:
                raise ValidationError({"status": f"Unsupported student attendance status: {record_status}"})
            if not device.is_enabled_for_students:
                raise ValidationError({"device": "This device is not enabled for student attendance."})
            student = get_object_or_404(Student, campus=device.campus, admission_number=external_id)
            record, _ = AttendanceRecord.objects.update_or_create(
                student=student,
                date=attendance_date,
                subject="",
                defaults={
                    "section": student.section,
                    "status": record_status,
                    "marked_by": request.user,
                    "capture_method": device.device_type,
                    "device": device,
                    "source_reference": source_reference,
                    "confidence_score": confidence or None,
                },
            )
            device.last_seen_at = timezone.now()
            device.save(update_fields=["last_seen_at", "updated_at"])
            serializer = AttendanceRecordSerializer(record, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        if person_type == "staff":
            if record_status not in {choice.value for choice in StaffAttendanceStatus}:
                raise ValidationError({"status": f"Unsupported staff attendance status: {record_status}"})
            if not device.is_enabled_for_staff:
                raise ValidationError({"device": "This device is not enabled for staff attendance."})
            from apps.accounts.models import User

            staff_user = get_object_or_404(User, username=external_id)
            if staff_user.role in (UserRole.STUDENT, UserRole.PARENT):
                raise ValidationError({"external_id": "Student and parent users must use person_type=student or portal access."})
            record, _ = StaffAttendanceRecord.objects.update_or_create(
                staff_user=staff_user,
                date=attendance_date,
                defaults={
                    "campus": device.campus,
                    "clock_in": captured_at.time(),
                    "status": record_status,
                    "marked_by": request.user,
                    "capture_method": device.device_type,
                    "device": device,
                    "source_reference": source_reference,
                    "confidence_score": confidence or None,
                },
            )
            device.last_seen_at = timezone.now()
            device.save(update_fields=["last_seen_at", "updated_at"])
            serializer = StaffAttendanceRecordSerializer(record, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        raise ValidationError({"person_type": "Use student or staff."})


class AcademicSessionViewSet(RoleScopedModelViewSet):
    queryset = AcademicSession.objects.select_related("campus")
    serializer_class = AcademicSessionSerializer
    campus_filter_path = "campus_id"
    filterset_fields = ("campus", "is_active")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(
                Q(sections__class_teacher=user)
                | Q(sections__subject_allocations__teacher=user, sections__subject_allocations__is_active=True)
            ).distinct()
        if user.role == UserRole.STUDENT:
            return queryset.filter(sections__students__user=user).distinct()
        if user.role == UserRole.PARENT:
            return queryset.filter(sections__students__guardianships__guardian=user).distinct()
        return queryset.none()


class ClassSectionViewSet(RoleScopedModelViewSet):
    queryset = ClassSection.objects.select_related("campus", "session", "class_teacher")
    serializer_class = ClassSectionSerializer
    campus_filter_path = "campus_id"
    filterset_fields = ("campus", "session", "class_teacher")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(teacher_section_q(user)).distinct()
        if user.role == UserRole.STUDENT:
            return queryset.filter(students__user=user).distinct()
        if user.role == UserRole.PARENT:
            return queryset.filter(students__guardianships__guardian=user).distinct()
        return queryset.none()


class TeacherSubjectAllocationViewSet(RoleScopedModelViewSet):
    queryset = TeacherSubjectAllocation.objects.select_related("campus", "section", "teacher")
    serializer_class = TeacherSubjectAllocationSerializer
    campus_filter_path = "campus_id"
    read_roles = ADMIN_ROLES + (UserRole.TEACHER,)
    write_roles = ADMIN_ROLES
    filterset_fields = ("campus", "section", "teacher", "subject", "is_active")
    search_fields = ("subject", "section__grade_name", "section__section_name", "teacher__username", "teacher__first_name", "teacher__last_name")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(teacher=user, is_active=True)
        return queryset.none()

    def campus_id_from_attrs(self, attrs) -> int | None:
        campus = attrs.get("campus")
        if campus:
            return campus.id
        section = attrs.get("section")
        if section:
            return section.campus_id
        return None


class StudentViewSet(RoleScopedModelViewSet):
    queryset = Student.objects.select_related("campus", "section")
    serializer_class = StudentSerializer
    campus_filter_path = "campus_id"
    search_fields = ("admission_number", "first_name", "last_name")
    filterset_fields = ("campus", "section", "status")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(
                Q(section__class_teacher=user)
                | Q(section__subject_allocations__teacher=user, section__subject_allocations__is_active=True)
            ).distinct()
        if user.role == UserRole.STUDENT:
            return queryset.filter(user=user)
        if user.role == UserRole.PARENT:
            return queryset.filter(guardianships__guardian=user)
        return queryset.none()


class StudentGuardianViewSet(RoleScopedModelViewSet):
    queryset = StudentGuardian.objects.select_related("student", "guardian", "student__section")
    serializer_class = StudentGuardianSerializer
    campus_filter_path = "student__campus_id"
    read_roles = READ_ROLES
    write_roles = ADMIN_ROLES
    filterset_fields = ("student", "guardian", "relationship")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(
                Q(student__section__class_teacher=user)
                | Q(student__section__subject_allocations__teacher=user, student__section__subject_allocations__is_active=True)
            ).distinct()
        if user.role == UserRole.STUDENT:
            return queryset.filter(student__user=user)
        if user.role == UserRole.PARENT:
            return queryset.filter(guardian=user)
        return queryset.none()


class AttendanceRecordViewSet(RoleScopedModelViewSet):
    queryset = AttendanceRecord.objects.select_related("student", "section", "marked_by")
    serializer_class = AttendanceRecordSerializer
    campus_filter_path = "student__campus_id"
    read_roles = READ_ROLES
    write_roles = ADMIN_ROLES + (UserRole.TEACHER,)
    filterset_fields = ("date", "status", "section", "subject", "capture_method", "device")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(
                Q(section__class_teacher=user)
                | Q(section__subject_allocations__teacher=user, section__subject_allocations__is_active=True)
            ).distinct()
        if user.role == UserRole.STUDENT:
            return queryset.filter(student__user=user)
        if user.role == UserRole.PARENT:
            return queryset.filter(student__guardianships__guardian=user)
        return queryset.none()

    def perform_create(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save(marked_by=self.request.user)
        self.write_audit(AuditAction.CREATE, instance)

    def perform_update(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save(marked_by=self.request.user)
        self.write_audit(AuditAction.UPDATE, instance)

    @action(detail=False, methods=["post"], url_path="bulk-upsert")
    def bulk_upsert(self, request):
        user = request.user
        if getattr(user, "role", None) not in self.write_roles:
            raise PermissionDenied("You do not have access to mark attendance.")

        section = get_object_or_404(ClassSection, pk=request.data.get("section"))
        if user.role == UserRole.ADMIN and section.campus_id not in self.admin_campus_ids():
            raise PermissionDenied("This section belongs to a campus outside your admin scope.")

        attendance_date = request.data.get("date")
        records = request.data.get("records", [])
        if not attendance_date or not isinstance(records, list):
            raise ValidationError({"detail": "Provide date and records."})
        attendance_date = ensure_attendance_date_is_editable(attendance_date)
        subject = (request.data.get("subject") or "").strip()
        if len(subject) > 80:
            raise ValidationError({"subject": "Subject must be 80 characters or fewer."})
        if user.role == UserRole.TEACHER and not teacher_has_subject_access(user, section, subject):
            raise PermissionDenied("Teachers can mark attendance only for assigned class sections or allotted subjects.")

        allowed_statuses = {choice.value for choice in AttendanceStatus}
        device = None
        if request.data.get("device"):
            device = get_object_or_404(AttendanceDevice, pk=request.data.get("device"), campus=section.campus)
        capture_method = request.data.get("capture_method") or (device.device_type if device else AttendanceCaptureMethod.MANUAL)
        if capture_method not in {choice.value for choice in AttendanceCaptureMethod}:
            raise ValidationError({"capture_method": f"Unsupported attendance capture method: {capture_method}"})
        source_reference = request.data.get("source_reference", "")
        confidence_score = request.data.get("confidence_score") or None

        saved_records = []
        with transaction.atomic():
            for item in records:
                try:
                    student_id = int(item.get("student"))
                except (TypeError, ValueError):
                    raise ValidationError({"student": "Provide a valid student id."})
                student = get_object_or_404(Student, pk=student_id, section=section)
                record_status = item.get("status")
                if record_status not in allowed_statuses:
                    raise ValidationError({"status": f"Unsupported attendance status: {record_status}"})
                record, _ = AttendanceRecord.objects.update_or_create(
                    student=student,
                    date=attendance_date,
                    subject=subject,
                    defaults={
                        "section": section,
                        "status": record_status,
                        "marked_by": user,
                        "capture_method": capture_method,
                        "device": device,
                        "source_reference": source_reference,
                        "confidence_score": confidence_score,
                    },
                )
                saved_records.append(record)
            AuditEvent.objects.create(
                actor=user,
                action=AuditAction.UPDATE,
                entity_type="AttendanceRecord",
                entity_id=str(section.pk),
                summary=f"Bulk attendance for {section} on {attendance_date}",
                ip_address=get_client_ip(request),
                metadata={"record_count": len(saved_records), "subject": subject},
            )

        serializer = self.get_serializer(saved_records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StaffAttendanceRecordViewSet(RoleScopedModelViewSet):
    queryset = StaffAttendanceRecord.objects.select_related("campus", "staff_user", "device", "marked_by")
    serializer_class = StaffAttendanceRecordSerializer
    campus_filter_path = "campus_id"
    read_roles = ADMIN_ROLES + (UserRole.TEACHER,)
    write_roles = ADMIN_ROLES
    filterset_fields = ("campus", "staff_user", "date", "status", "capture_method", "device")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(staff_user=user)
        return queryset.none()

    def perform_create(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save(marked_by=self.request.user)
        self.write_audit(AuditAction.CREATE, instance)

    def perform_update(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save(marked_by=self.request.user)
        self.write_audit(AuditAction.UPDATE, instance)


class StaffProfileViewSet(RoleScopedModelViewSet):
    queryset = StaffProfile.objects.select_related("campus", "user")
    serializer_class = StaffProfileSerializer
    campus_filter_path = "campus_id"
    read_roles = ADMIN_ROLES + (UserRole.TEACHER,)
    write_roles = ADMIN_ROLES
    filterset_fields = ("campus", "user", "department", "employment_type", "status")
    search_fields = ("employee_code", "designation", "department", "user__username", "user__first_name", "user__last_name")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(user=user)
        return queryset.none()


class TimetableSlotViewSet(RoleScopedModelViewSet):
    queryset = TimetableSlot.objects.select_related("campus", "section", "teacher")
    serializer_class = TimetableSlotSerializer
    campus_filter_path = "campus_id"
    read_roles = READ_ROLES
    write_roles = ADMIN_ROLES
    filterset_fields = ("campus", "section", "teacher", "subject", "day_of_week")
    search_fields = ("subject", "room", "section__grade_name", "section__section_name", "teacher__username")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(
                Q(teacher=user)
                | Q(section__class_teacher=user)
                | Q(section__subject_allocations__teacher=user, section__subject_allocations__is_active=True)
            ).distinct()
        if user.role == UserRole.STUDENT:
            return queryset.filter(section__students__user=user).distinct()
        if user.role == UserRole.PARENT:
            return queryset.filter(section__students__guardianships__guardian=user).distinct()
        return queryset.none()


class LibraryBookViewSet(RoleScopedModelViewSet):
    queryset = LibraryBook.objects.select_related("campus")
    serializer_class = LibraryBookSerializer
    campus_filter_path = "campus_id"
    read_roles = READ_ROLES
    write_roles = ADMIN_ROLES
    filterset_fields = ("campus", "category", "status")
    search_fields = ("accession_number", "title", "author", "isbn", "category")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(
                Q(campus__sections__class_teacher=user)
                | Q(campus__sections__subject_allocations__teacher=user, campus__sections__subject_allocations__is_active=True)
            ).distinct()
        if user.role == UserRole.STUDENT:
            return queryset.filter(campus__students__user=user).distinct()
        if user.role == UserRole.PARENT:
            return queryset.filter(campus__students__guardianships__guardian=user).distinct()
        return queryset.none()


class LibraryLoanViewSet(RoleScopedModelViewSet):
    queryset = LibraryLoan.objects.select_related("campus", "book", "student", "staff_user")
    serializer_class = LibraryLoanSerializer
    campus_filter_path = "campus_id"
    read_roles = READ_ROLES
    write_roles = ADMIN_ROLES
    filterset_fields = ("campus", "book", "student", "staff_user", "status", "due_on")
    search_fields = ("book__title", "student__first_name", "student__last_name", "staff_user__username")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(
                Q(staff_user=user)
                | Q(student__section__class_teacher=user)
                | Q(student__section__subject_allocations__teacher=user, student__section__subject_allocations__is_active=True)
            ).distinct()
        if user.role == UserRole.STUDENT:
            return queryset.filter(student__user=user)
        if user.role == UserRole.PARENT:
            return queryset.filter(student__guardianships__guardian=user)
        return queryset.none()


class TransportRouteViewSet(RoleScopedModelViewSet):
    queryset = TransportRoute.objects.select_related("campus")
    serializer_class = TransportRouteSerializer
    campus_filter_path = "campus_id"
    read_roles = READ_ROLES
    write_roles = ADMIN_ROLES
    filterset_fields = ("campus", "is_active")
    search_fields = ("name", "route_code", "start_point", "end_point")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(
                Q(campus__sections__class_teacher=user)
                | Q(campus__sections__subject_allocations__teacher=user, campus__sections__subject_allocations__is_active=True)
            ).distinct()
        if user.role == UserRole.STUDENT:
            return queryset.filter(student_assignments__student__user=user).distinct()
        if user.role == UserRole.PARENT:
            return queryset.filter(student_assignments__student__guardianships__guardian=user).distinct()
        return queryset.none()


class TransportVehicleViewSet(RoleScopedModelViewSet):
    queryset = TransportVehicle.objects.select_related("campus", "route")
    serializer_class = TransportVehicleSerializer
    campus_filter_path = "campus_id"
    read_roles = READ_ROLES
    write_roles = ADMIN_ROLES
    filterset_fields = ("campus", "route", "is_active")
    search_fields = ("vehicle_number", "driver_name", "driver_phone", "gps_device_id")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(
                Q(campus__sections__class_teacher=user)
                | Q(campus__sections__subject_allocations__teacher=user, campus__sections__subject_allocations__is_active=True)
            ).distinct()
        if user.role == UserRole.STUDENT:
            return queryset.filter(student_assignments__student__user=user).distinct()
        if user.role == UserRole.PARENT:
            return queryset.filter(student_assignments__student__guardianships__guardian=user).distinct()
        return queryset.none()


class StudentTransportAssignmentViewSet(RoleScopedModelViewSet):
    queryset = StudentTransportAssignment.objects.select_related("student", "route", "vehicle")
    serializer_class = StudentTransportAssignmentSerializer
    campus_filter_path = "student__campus_id"
    read_roles = READ_ROLES
    write_roles = ADMIN_ROLES
    filterset_fields = ("student", "route", "vehicle", "is_active")
    search_fields = ("student__first_name", "student__last_name", "route__name", "pickup_stop", "drop_stop")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(
                Q(student__section__class_teacher=user)
                | Q(student__section__subject_allocations__teacher=user, student__section__subject_allocations__is_active=True)
            ).distinct()
        if user.role == UserRole.STUDENT:
            return queryset.filter(student__user=user)
        if user.role == UserRole.PARENT:
            return queryset.filter(student__guardianships__guardian=user)
        return queryset.none()


class HostelRoomViewSet(RoleScopedModelViewSet):
    queryset = HostelRoom.objects.select_related("campus")
    serializer_class = HostelRoomSerializer
    campus_filter_path = "campus_id"
    read_roles = READ_ROLES
    write_roles = ADMIN_ROLES
    filterset_fields = ("campus", "hostel_name", "is_active")
    search_fields = ("hostel_name", "room_number", "floor")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(
                Q(campus__sections__class_teacher=user)
                | Q(campus__sections__subject_allocations__teacher=user, campus__sections__subject_allocations__is_active=True)
            ).distinct()
        if user.role == UserRole.STUDENT:
            return queryset.filter(allocations__student__user=user).distinct()
        if user.role == UserRole.PARENT:
            return queryset.filter(allocations__student__guardianships__guardian=user).distinct()
        return queryset.none()


class HostelAllocationViewSet(RoleScopedModelViewSet):
    queryset = HostelAllocation.objects.select_related("student", "room")
    serializer_class = HostelAllocationSerializer
    campus_filter_path = "student__campus_id"
    read_roles = READ_ROLES
    write_roles = ADMIN_ROLES
    filterset_fields = ("student", "room", "is_active")
    search_fields = ("student__first_name", "student__last_name", "room__hostel_name", "room__room_number", "bed_number")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(
                Q(student__section__class_teacher=user)
                | Q(student__section__subject_allocations__teacher=user, student__section__subject_allocations__is_active=True)
            ).distinct()
        if user.role == UserRole.STUDENT:
            return queryset.filter(student__user=user)
        if user.role == UserRole.PARENT:
            return queryset.filter(student__guardianships__guardian=user)
        return queryset.none()


class ApprovalRequestViewSet(RoleScopedModelViewSet):
    queryset = ApprovalRequest.objects.select_related("campus", "requested_by", "reviewed_by")
    serializer_class = ApprovalRequestSerializer
    campus_filter_path = "campus_id"
    read_roles = ADMIN_ROLES + (UserRole.TEACHER,)
    write_roles = ADMIN_ROLES + (UserRole.TEACHER,)
    filterset_fields = ("campus", "status", "entity_type", "requested_by")
    search_fields = ("title", "description", "entity_type", "entity_id")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(Q(requested_by=user) | Q(campus__sections__class_teacher=user)).distinct()
        return queryset.none()

    def perform_create(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save(requested_by=self.request.user)
        self.write_audit(AuditAction.CREATE, instance)

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        if getattr(request.user, "role", None) not in ADMIN_ROLES:
            raise PermissionDenied("Only campus admins can approve requests.")
        approval = self.get_object()
        approval.decide(
            status_value=ApprovalStatus.APPROVED,
            reviewer=request.user,
            note=request.data.get("decision_note", ""),
        )
        self.write_audit(AuditAction.UPDATE, approval)
        return Response(self.get_serializer(approval).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        if getattr(request.user, "role", None) not in ADMIN_ROLES:
            raise PermissionDenied("Only campus admins can reject requests.")
        approval = self.get_object()
        approval.decide(
            status_value=ApprovalStatus.REJECTED,
            reviewer=request.user,
            note=request.data.get("decision_note", ""),
        )
        self.write_audit(AuditAction.UPDATE, approval)
        return Response(self.get_serializer(approval).data, status=status.HTTP_200_OK)


class AnnouncementViewSet(RoleScopedModelViewSet):
    queryset = Announcement.objects.select_related("created_by")
    serializer_class = AnnouncementSerializer
    read_roles = READ_ROLES
    write_roles = ADMIN_ROLES
    filterset_fields = ("audience", "is_active")
    search_fields = ("title", "message")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(audience__in=["all", "staff"])
        if user.role in (UserRole.STUDENT, UserRole.PARENT):
            return queryset.filter(audience__in=["all", "learners"])
        return queryset.none()

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True, publish_on__lte=timezone.now())
        user = self.request.user
        if getattr(user, "role", None) in ADMIN_ROLES:
            return queryset
        return queryset

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        self.write_audit(AuditAction.CREATE, instance)

    def perform_update(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        self.write_audit(AuditAction.UPDATE, instance)


class SupportTicketViewSet(viewsets.ModelViewSet):
    queryset = SupportTicket.objects.select_related("campus", "created_by", "reviewed_by")
    serializer_class = SupportTicketSerializer
    permission_classes = [RoleAccessPermission]
    read_roles = READ_ROLES
    write_roles = READ_ROLES
    filterset_fields = ("status", "priority", "category", "campus")
    search_fields = ("subject", "message", "created_by__username")
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if getattr(user, "role", None) == UserRole.SUPER_ADMIN:
            return queryset
        return queryset.filter(created_by=user)

    def perform_create(self, serializer):
        campus = serializer.validated_data.get("campus")
        if campus is None:
            membership = CampusMembership.objects.filter(user=self.request.user, is_primary=True).first()
            membership = membership or CampusMembership.objects.filter(user=self.request.user).first()
            campus = membership.campus if membership else None
        ticket = serializer.save(created_by=self.request.user, campus=campus)
        AuditEvent.objects.create(
            actor=self.request.user,
            action=AuditAction.CREATE,
            entity_type="SupportTicket",
            entity_id=str(ticket.pk),
            summary=f"Support issue raised: {ticket.subject}",
            ip_address=get_client_ip(self.request),
            metadata={
                "priority": ticket.priority,
                "status": ticket.status,
                "campus": ticket.campus.code if ticket.campus else "",
            },
        )

    def partial_update(self, request, *args, **kwargs):
        if getattr(request.user, "role", None) != UserRole.SUPER_ADMIN:
            disallowed = {"status", "response_note", "reviewed_by", "resolved_at"} & set(request.data.keys())
            if disallowed:
                raise PermissionDenied("Only super admins can change support ticket resolution fields.")
        return super().partial_update(request, *args, **kwargs)

    def perform_update(self, serializer):
        status_value = serializer.validated_data.get("status")
        save_kwargs = {}
        if getattr(self.request.user, "role", None) == UserRole.SUPER_ADMIN:
            save_kwargs["reviewed_by"] = self.request.user
            if status_value:
                save_kwargs["resolved_at"] = timezone.now() if status_value == SupportTicketStatus.RESOLVED else None
        ticket = serializer.save(**save_kwargs)
        AuditEvent.objects.create(
            actor=self.request.user,
            action=AuditAction.UPDATE,
            entity_type="SupportTicket",
            entity_id=str(ticket.pk),
            summary=f"Support ticket updated: {ticket.subject}",
            ip_address=get_client_ip(self.request),
            metadata={"status": ticket.status, "priority": ticket.priority},
        )


class AssignedWorkViewSet(RoleScopedModelViewSet):
    queryset = AssignedWork.objects.select_related("section", "assigned_by")
    serializer_class = AssignedWorkSerializer
    campus_filter_path = "section__campus_id"
    read_roles = READ_ROLES
    write_roles = ACADEMIC_WRITE_ROLES
    filterset_fields = ("section", "subject", "status", "due_date")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(section__class_teacher=user)
        if user.role == UserRole.STUDENT:
            return queryset.filter(status="published", section__students__user=user).distinct()
        if user.role == UserRole.PARENT:
            return queryset.filter(status="published", section__students__guardianships__guardian=user).distinct()
        return queryset.none()

    def perform_create(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save(assigned_by=self.request.user)
        self.write_audit(AuditAction.CREATE, instance)

    def perform_update(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save(assigned_by=self.request.user)
        self.write_audit(AuditAction.UPDATE, instance)


class LearningResourceViewSet(RoleScopedModelViewSet):
    queryset = LearningResource.objects.select_related("section", "uploaded_by")
    serializer_class = LearningResourceSerializer
    campus_filter_path = "section__campus_id"
    read_roles = READ_ROLES
    write_roles = ACADEMIC_WRITE_ROLES
    filterset_fields = ("section", "subject", "resource_type", "published_on")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(section__class_teacher=user)
        if user.role == UserRole.STUDENT:
            return queryset.filter(section__students__user=user).distinct()
        if user.role == UserRole.PARENT:
            return queryset.filter(section__students__guardianships__guardian=user).distinct()
        return queryset.none()

    def perform_create(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save(uploaded_by=self.request.user)
        self.write_audit(AuditAction.CREATE, instance)

    def perform_update(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save(uploaded_by=self.request.user)
        self.write_audit(AuditAction.UPDATE, instance)


class ResultRecordViewSet(RoleScopedModelViewSet):
    queryset = ResultRecord.objects.select_related("student", "student__section", "recorded_by")
    serializer_class = ResultRecordSerializer
    campus_filter_path = "student__campus_id"
    read_roles = READ_ROLES
    write_roles = ACADEMIC_WRITE_ROLES
    filterset_fields = ("student", "exam_name", "subject", "published_on")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(student__section__class_teacher=user)
        if user.role == UserRole.STUDENT:
            return queryset.filter(student__user=user)
        if user.role == UserRole.PARENT:
            return queryset.filter(student__guardianships__guardian=user)
        return queryset.none()

    def perform_create(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save(recorded_by=self.request.user)
        self.write_audit(AuditAction.CREATE, instance)

    def perform_update(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save(recorded_by=self.request.user)
        self.write_audit(AuditAction.UPDATE, instance)


class AdmitCardViewSet(RoleScopedModelViewSet):
    queryset = AdmitCard.objects.select_related("student", "student__section", "issued_by")
    serializer_class = AdmitCardSerializer
    campus_filter_path = "student__campus_id"
    read_roles = READ_ROLES
    write_roles = ACADEMIC_WRITE_ROLES
    filterset_fields = ("student", "exam_name", "status", "exam_date")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(student__section__class_teacher=user)
        if user.role == UserRole.STUDENT:
            return queryset.filter(student__user=user)
        if user.role == UserRole.PARENT:
            return queryset.filter(student__guardianships__guardian=user)
        return queryset.none()

    def perform_create(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save(issued_by=self.request.user)
        self.write_audit(AuditAction.CREATE, instance)

    def perform_update(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save(issued_by=self.request.user)
        self.write_audit(AuditAction.UPDATE, instance)


class FeeAssignmentViewSet(RoleScopedModelViewSet):
    queryset = FeeAssignment.objects.select_related("student")
    serializer_class = FeeAssignmentSerializer
    campus_filter_path = "student__campus_id"
    filterset_fields = ("status", "due_date")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(student__section__class_teacher=user)
        if user.role == UserRole.STUDENT:
            return queryset.filter(student__user=user)
        if user.role == UserRole.PARENT:
            return queryset.filter(student__guardianships__guardian=user)
        return queryset.none()


class PaymentViewSet(RoleScopedModelViewSet):
    queryset = Payment.objects.select_related("fee_assignment", "collected_by")
    serializer_class = PaymentSerializer
    campus_filter_path = "fee_assignment__student__campus_id"
    filterset_fields = ("payment_method", "paid_on")

    def filter_queryset_by_role(self, queryset):
        user = self.request.user
        if user.role == UserRole.TEACHER:
            return queryset.filter(fee_assignment__student__section__class_teacher=user)
        if user.role == UserRole.STUDENT:
            return queryset.filter(fee_assignment__student__user=user)
        if user.role == UserRole.PARENT:
            return queryset.filter(fee_assignment__student__guardianships__guardian=user)
        return queryset.none()

    def perform_create(self, serializer):
        self.ensure_admin_payload_scope(serializer.validated_data)
        instance = serializer.save(collected_by=self.request.user)
        self.write_audit(AuditAction.CREATE, instance)


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditEvent.objects.select_related("actor")
    serializer_class = AuditEventSerializer
    permission_classes = [RoleAccessPermission]
    read_roles = ADMIN_ROLES
    write_roles = ()
    filterset_fields = ("actor", "action", "entity_type")

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if getattr(user, "role", None) == UserRole.SUPER_ADMIN:
            return queryset
        if getattr(user, "role", None) != UserRole.ADMIN:
            return queryset.none()

        campus_scope = CampusMembership.objects.filter(user=user).select_related("campus")
        campus_ids = list(campus_scope.values_list("campus_id", flat=True).distinct())
        campus_codes = list(campus_scope.values_list("campus__code", flat=True).distinct())
        if not campus_ids:
            return queryset.none()

        return queryset.filter(
            Q(actor__campus_memberships__campus_id__in=campus_ids)
            | Q(metadata__campus__in=campus_codes)
        ).distinct()


class DashboardSummaryView(APIView):
    permission_classes = [RoleAccessPermission]
    read_roles = READ_ROLES
    write_roles = ()

    def admin_campus_ids(self, user):
        if user.role == UserRole.SUPER_ADMIN:
            return None
        if user.role == UserRole.ADMIN:
            return list(CampusMembership.objects.filter(user=user).values_list("campus_id", flat=True).distinct())
        return []

    def scoped_students(self, user):
        queryset = Student.objects.select_related("campus", "section")
        if user.role == UserRole.SUPER_ADMIN:
            return queryset
        if user.role == UserRole.ADMIN:
            campus_ids = self.admin_campus_ids(user)
            return queryset.filter(campus_id__in=campus_ids) if campus_ids else queryset.none()
        if user.role == UserRole.TEACHER:
            return queryset.filter(
                Q(section__class_teacher=user)
                | Q(section__subject_allocations__teacher=user, section__subject_allocations__is_active=True)
            ).distinct()
        if user.role == UserRole.STUDENT:
            return queryset.filter(user=user)
        if user.role == UserRole.PARENT:
            return queryset.filter(guardianships__guardian=user)
        return queryset.none()

    def scoped_campus_ids(self, user, students):
        if user.role == UserRole.SUPER_ADMIN:
            return list(Campus.objects.values_list("id", flat=True))
        if user.role == UserRole.ADMIN:
            return self.admin_campus_ids(user) or []
        if user.role == UserRole.TEACHER:
            return list(
                ClassSection.objects.filter(teacher_section_q(user))
                .values_list("campus_id", flat=True)
                .distinct()
            )
        return list(students.values_list("campus_id", flat=True).distinct())

    def get(self, request):
        user = request.user
        students = self.scoped_students(user)
        attendance = AttendanceRecord.objects.filter(student__in=students)
        fees = FeeAssignment.objects.filter(student__in=students)
        payments = Payment.objects.filter(fee_assignment__student__in=students)
        campus_ids = self.scoped_campus_ids(user, students)
        staff_attendance = StaffAttendanceRecord.objects.filter(campus_id__in=campus_ids)
        devices = AttendanceDevice.objects.filter(campus_id__in=campus_ids)
        approvals = ApprovalRequest.objects.filter(campus_id__in=campus_ids)

        total_assigned = fees.aggregate(total=Sum("amount")).get("total") or Decimal("0")
        total_collected = payments.aggregate(total=Sum("amount_paid")).get("total") or Decimal("0")

        attendance_by_status = {
            item["status"]: item["count"]
            for item in attendance.values("status").annotate(count=Count("id"))
        }
        fees_by_status = {
            item["status"]: item["count"]
            for item in fees.values("status").annotate(count=Count("id"))
        }

        section_rows = attendance.values(
            "section",
            "section__grade_name",
            "section__section_name",
        ).annotate(
            total=Count("id"),
            present=Count("id", filter=Q(status=AttendanceStatus.PRESENT)),
            absent=Count("id", filter=Q(status=AttendanceStatus.ABSENT)),
        ).order_by("section__grade_name", "section__section_name")

        recent_payments = [
            {
                "id": payment.id,
                "student_name": payment.fee_assignment.student.full_name,
                "fee_title": payment.fee_assignment.title,
                "amount_paid": str(payment.amount_paid),
                "paid_on": payment.paid_on,
                "payment_method": payment.payment_method,
                "reference_number": payment.reference_number,
            }
            for payment in payments.select_related("fee_assignment", "fee_assignment__student").order_by("-paid_on", "-created_at")[:8]
        ]

        return Response(
            {
                "students": {
                    "total": students.count(),
                    "active": students.filter(status="active").count(),
                },
                "attendance": {
                    "total": attendance.count(),
                    "by_status": attendance_by_status,
                    "by_section": [
                        {
                            "section": row["section"],
                            "label": f"{row['section__grade_name']} - {row['section__section_name']}",
                            "total": row["total"],
                            "present": row["present"],
                            "absent": row["absent"],
                        }
                        for row in section_rows
                    ],
                },
                "fees": {
                    "total_assigned": str(total_assigned),
                    "total_collected": str(total_collected),
                    "total_outstanding": str(max(total_assigned - total_collected, Decimal("0"))),
                    "by_status": fees_by_status,
                },
                "staff_attendance": {
                    "total": staff_attendance.count(),
                    "by_status": {
                        item["status"]: item["count"]
                        for item in staff_attendance.values("status").annotate(count=Count("id"))
                    },
                },
                "devices": {
                    "total": devices.count(),
                    "active": devices.filter(status="active").count(),
                    "by_type": {
                        item["device_type"]: item["count"]
                        for item in devices.values("device_type").annotate(count=Count("id"))
                    },
                },
                "approvals": {
                    "pending": approvals.filter(status=ApprovalStatus.PENDING).count(),
                    "approved": approvals.filter(status=ApprovalStatus.APPROVED).count(),
                    "rejected": approvals.filter(status=ApprovalStatus.REJECTED).count(),
                },
                "recent_payments": recent_payments,
            }
        )

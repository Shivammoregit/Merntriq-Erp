from datetime import date, time, timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User, UserRole
from apps.core.models import (
    AcademicSession,
    AdmitCard,
    Announcement,
    AssignedWork,
    AttendanceRecord,
    AttendanceDevice,
    AuditAction,
    AuditEvent,
    CampusMembership,
    Campus,
    ClassSection,
    FeeAssignment,
    LearningResource,
    ResultRecord,
    Student,
    StudentGuardian,
    SupportTicket,
)


class ERPRoleFlowTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
            password="Passw0rd!123",
            role=UserRole.ADMIN,
            is_staff=True,
        )
        self.super_admin = User.objects.create_user(
            username="superadmin",
            password="Passw0rd!123",
            role=UserRole.SUPER_ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        self.teacher = User.objects.create_user(
            username="teacher",
            password="Passw0rd!123",
            role=UserRole.TEACHER,
        )
        self.parent = User.objects.create_user(
            username="parent",
            password="Passw0rd!123",
            role=UserRole.PARENT,
        )
        self.student_user = User.objects.create_user(
            username="student",
            password="Passw0rd!123",
            role=UserRole.STUDENT,
        )
        self.other_teacher = User.objects.create_user(
            username="other_teacher",
            password="Passw0rd!123",
            role=UserRole.TEACHER,
        )

        self.campus = Campus.objects.create(name="Main Campus", code="MAIN")
        self.other_campus = Campus.objects.create(name="North Campus", code="NORTH")
        CampusMembership.objects.create(
            campus=self.campus,
            user=self.admin,
            role="it_admin",
            is_primary=True,
            can_manage_users=True,
            can_configure_attendance=True,
        )
        CampusMembership.objects.create(
            campus=self.other_campus,
            user=self.other_teacher,
            role="teacher",
            is_primary=True,
        )
        self.session = AcademicSession.objects.create(
            campus=self.campus,
            name="2026-27",
            start_date=date(2026, 4, 1),
            end_date=date(2027, 3, 31),
        )
        self.other_session = AcademicSession.objects.create(
            campus=self.other_campus,
            name="2026-27",
            start_date=date(2026, 4, 1),
            end_date=date(2027, 3, 31),
        )
        self.section = ClassSection.objects.create(
            campus=self.campus,
            session=self.session,
            grade_name="Grade 5",
            section_name="A",
            class_teacher=self.teacher,
        )
        self.other_section = ClassSection.objects.create(
            campus=self.other_campus,
            session=self.other_session,
            grade_name="Grade 6",
            section_name="B",
            class_teacher=self.other_teacher,
        )
        self.student = Student.objects.create(
            campus=self.campus,
            section=self.section,
            user=self.student_user,
            admission_number="ADM-1",
            first_name="Anaya",
            last_name="Kapoor",
            date_of_birth=date(2015, 7, 18),
        )
        StudentGuardian.objects.create(student=self.student, guardian=self.parent)
        AttendanceRecord.objects.create(
            student=self.student,
            section=self.section,
            date=timezone.localdate() - timedelta(days=1),
            status="present",
            marked_by=self.teacher,
        )
        FeeAssignment.objects.create(
            student=self.student,
            title="Term Fee",
            amount=Decimal("12000.00"),
            due_date=date(2026, 6, 1),
        )
        AssignedWork.objects.create(
            section=self.section,
            assigned_by=self.teacher,
            title="Fractions",
            subject="Mathematics",
            description="Complete exercise 1.",
            due_date=date(2026, 5, 20),
        )
        LearningResource.objects.create(
            section=self.section,
            uploaded_by=self.teacher,
            title="Math Notes",
            subject="Mathematics",
            resource_type="notes",
            description="Revision notes.",
            published_on=date(2026, 5, 12),
        )
        ResultRecord.objects.create(
            student=self.student,
            recorded_by=self.teacher,
            exam_name="Unit Test 1",
            subject="Mathematics",
            score=Decimal("88"),
            max_score=Decimal("100"),
            grade="A",
            published_on=date(2026, 5, 13),
        )
        AdmitCard.objects.create(
            student=self.student,
            issued_by=self.admin,
            exam_name="Mid Term",
            roll_number="G5A-001",
            exam_date=date(2026, 6, 10),
            reporting_time=time(8, 30),
            venue="Room 205",
            status="issued",
            issued_on=date(2026, 5, 15),
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_admin_can_read_dashboard_summary(self):
        self.authenticate(self.admin)
        response = self.client.get(reverse("dashboard-summary"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["students"]["total"], 1)
        self.assertEqual(response.data["attendance"]["by_status"]["present"], 1)

    def test_admin_can_configure_attendance_hardware_settings(self):
        self.authenticate(self.admin)
        payload = {
            "campus": self.campus.id,
            "name": "Main Gate Nialabs Terminal",
            "device_code": "NIALABS-MAIN-01",
            "device_type": "face_recognition",
            "location": "Main gate",
            "provider": "Nialabs",
            "status": "active",
            "is_enabled_for_students": True,
            "is_enabled_for_staff": True,
            "server_required": True,
            "use_domain_name": True,
            "domain_name": "device.nialabs.in",
            "server_ip": "192.168.000.109",
            "server_port": 7743,
            "heartbeat_seconds": 3,
            "server_approval_required": False,
            "device_numeric_id": 1,
            "local_port": 5005,
            "baud_rate": 38400,
            "rs485_function": "software",
        }

        response = self.client.post("/api/v1/attendance-devices/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["domain_name"], "device.nialabs.in")
        self.assertEqual(response.data["server_port"], 7743)
        self.assertEqual(response.data["local_port"], 5005)
        self.assertEqual(response.data["baud_rate"], 38400)
        self.assertEqual(response.data["rs485_function"], "software")
        self.assertEqual(response.data["configured_by"], self.admin.id)

    def test_parent_is_scoped_to_linked_student_and_cannot_read_audit(self):
        self.authenticate(self.parent)

        students_response = self.client.get("/api/v1/students/")
        audit_response = self.client.get("/api/v1/audit-events/")

        self.assertEqual(students_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(students_response.data), 1)
        self.assertEqual(audit_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_is_scoped_to_assigned_campus(self):
        self.authenticate(self.admin)

        campus_response = self.client.get("/api/v1/campuses/")
        blocked_student = self.client.post(
            "/api/v1/students/",
            {
                "campus": self.other_campus.id,
                "section": self.other_section.id,
                "admission_number": "ADM-NORTH-1",
                "first_name": "Nikhil",
                "last_name": "Rao",
                "date_of_birth": "2015-05-10",
                "status": "active",
            },
            format="json",
        )
        blocked_user = self.client.post(
            "/api/v1/auth/users/",
            {
                "username": "north-admin",
                "password": "Passw0rd!123",
                "role": "admin",
                "campus_ids": [self.other_campus.id],
            },
            format="json",
        )

        self.assertEqual(campus_response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in campus_response.data], [self.campus.id])
        self.assertEqual(blocked_student.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(blocked_user.status_code, status.HTTP_400_BAD_REQUEST)

    def test_audit_events_are_scoped_for_admin_and_global_for_super_admin(self):
        main_event = AuditEvent.objects.create(
            actor=self.admin,
            action=AuditAction.UPDATE,
            entity_type="Student",
            entity_id=str(self.student.id),
            summary="Main campus student update",
            metadata={"campus": self.campus.code},
        )
        other_event = AuditEvent.objects.create(
            actor=self.other_teacher,
            action=AuditAction.UPDATE,
            entity_type="Student",
            entity_id="other-campus",
            summary="Other campus student update",
            metadata={"campus": self.other_campus.code},
        )

        self.authenticate(self.admin)
        admin_response = self.client.get("/api/v1/audit-events/")
        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual([event["id"] for event in admin_response.data], [main_event.id])

        self.authenticate(self.super_admin)
        super_response = self.client.get("/api/v1/audit-events/")
        self.assertEqual(super_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {main_event.id, other_event.id}.issubset({event["id"] for event in super_response.data}),
            True,
        )

    def test_teacher_can_bulk_mark_only_assigned_section(self):
        self.authenticate(self.teacher)
        device = AttendanceDevice.objects.create(
            campus=self.campus,
            name="Main Gate Face Terminal",
            device_code="FACE-MAIN-01",
            device_type="face_recognition",
        )
        response = self.client.post(
            "/api/v1/attendance-records/bulk-upsert/",
            {
                "section": self.section.id,
                "date": timezone.localdate().isoformat(),
                "capture_method": "face_recognition",
                "device": device.id,
                "records": [{"student": self.student.id, "status": "on_duty"}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        saved = AttendanceRecord.objects.get(date=timezone.localdate())
        self.assertEqual(saved.status, "on_duty")
        self.assertEqual(saved.capture_method, "face_recognition")

        self.authenticate(self.other_teacher)
        denied = self.client.post(
            "/api/v1/attendance-records/bulk-upsert/",
            {
                "section": self.section.id,
                "date": timezone.localdate().isoformat(),
                "records": [{"student": self.student.id, "status": "present"}],
            },
            format="json",
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

    def test_attendance_older_than_three_days_is_locked(self):
        self.authenticate(self.teacher)
        response = self.client.post(
            "/api/v1/attendance-records/bulk-upsert/",
            {
                "section": self.section.id,
                "date": (timezone.localdate() - timedelta(days=4)).isoformat(),
                "records": [{"student": self.student.id, "status": "present"}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_can_read_own_academic_workspace_only(self):
        self.authenticate(self.student_user)

        students_response = self.client.get("/api/v1/students/")
        work_response = self.client.get("/api/v1/assigned-work/")
        resources_response = self.client.get("/api/v1/learning-resources/")
        results_response = self.client.get("/api/v1/result-records/")
        admit_cards_response = self.client.get("/api/v1/admit-cards/")
        write_response = self.client.post(
            "/api/v1/assigned-work/",
            {
                "section": self.section.id,
                "title": "Blocked",
                "subject": "Science",
                "due_date": "2026-06-01",
            },
            format="json",
        )

        self.assertEqual(students_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(students_response.data), 1)
        self.assertEqual(students_response.data[0]["user"], self.student_user.id)
        self.assertEqual(work_response.status_code, status.HTTP_200_OK)
        self.assertEqual(resources_response.status_code, status.HTTP_200_OK)
        self.assertEqual(results_response.status_code, status.HTTP_200_OK)
        self.assertEqual(admit_cards_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(work_response.data), 1)
        self.assertEqual(len(resources_response.data), 1)
        self.assertEqual(len(results_response.data), 1)
        self.assertEqual(len(admit_cards_response.data), 1)
        self.assertEqual(write_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_announcements_are_visible_by_audience(self):
        Announcement.objects.create(title="All notice", message="For everyone", audience="all", created_by=self.admin)
        Announcement.objects.create(title="Staff notice", message="For staff", audience="staff", created_by=self.admin)
        Announcement.objects.create(title="Learner notice", message="For learners", audience="learners", created_by=self.admin)
        Announcement.objects.create(title="Admin notice", message="For admins", audience="admins", created_by=self.admin)

        self.authenticate(self.teacher)
        teacher_response = self.client.get("/api/v1/announcements/")
        self.assertEqual(teacher_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {item["title"] for item in teacher_response.data},
            {"All notice", "Staff notice"},
        )

        self.authenticate(self.student_user)
        student_response = self.client.get("/api/v1/announcements/")
        self.assertEqual(student_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {item["title"] for item in student_response.data},
            {"All notice", "Learner notice"},
        )

        self.authenticate(self.admin)
        admin_response = self.client.get("/api/v1/announcements/")
        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(admin_response.data), 4)

    def test_support_tickets_are_sent_to_super_admin_queue(self):
        self.authenticate(self.student_user)
        create_response = self.client.post(
            "/api/v1/support-tickets/",
            {
                "campus": self.campus.id,
                "subject": "Admit card download issue",
                "message": "The download button is not opening the admit card.",
                "category": "student_portal",
                "priority": "high",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        ticket_id = create_response.data["id"]

        self.authenticate(self.parent)
        parent_response = self.client.get("/api/v1/support-tickets/")
        self.assertEqual(parent_response.status_code, status.HTTP_200_OK)
        self.assertEqual(parent_response.data, [])

        self.authenticate(self.super_admin)
        queue_response = self.client.get("/api/v1/support-tickets/?status=open")
        self.assertEqual(queue_response.status_code, status.HTTP_200_OK)
        self.assertIn(ticket_id, [item["id"] for item in queue_response.data])

        resolve_response = self.client.patch(
            f"/api/v1/support-tickets/{ticket_id}/",
            {"status": "resolved", "response_note": "Shared with IT admin."},
            format="json",
        )
        self.assertEqual(resolve_response.status_code, status.HTTP_200_OK)
        ticket = SupportTicket.objects.get(pk=ticket_id)
        self.assertEqual(ticket.status, "resolved")
        self.assertEqual(ticket.reviewed_by, self.super_admin)

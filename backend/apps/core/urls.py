from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AcademicSessionViewSet,
    AdmitCardViewSet,
    AILogViewSet,
    AssignedWorkViewSet,
    AnnouncementViewSet,
    ApprovalRequestViewSet,
    AttendanceDeviceViewSet,
    AttendanceRecordViewSet,
    AuditEventViewSet,
    CampusViewSet,
    CampusMembershipViewSet,
    ClassSectionViewSet,
    DocumentViewSet,
    DashboardSummaryView,
    FeeAssignmentViewSet,
    HealthCheckView,
    HostelAllocationViewSet,
    HostelRoomViewSet,
    LibraryBookViewSet,
    LibraryLoanViewSet,
    LearningResourceViewSet,
    MessageTemplateViewSet,
    OutboundMessageViewSet,
    PaymentViewSet,
    PaymentTransactionViewSet,
    PlatformSettingViewSet,
    ResultRecordViewSet,
    SalaryRecordViewSet,
    StaffAttendanceRecordViewSet,
    StaffProfileViewSet,
    StudentGuardianViewSet,
    StudentViewSet,
    StudentTransportAssignmentViewSet,
    SupportTicketViewSet,
    TeacherSubjectAllocationViewSet,
    TimetableSlotViewSet,
    TransportRouteViewSet,
    TransportVehicleViewSet,
)

router = DefaultRouter()
router.register("campuses", CampusViewSet, basename="campus")
router.register("campus-memberships", CampusMembershipViewSet, basename="campus-membership")
router.register("attendance-devices", AttendanceDeviceViewSet, basename="attendance-device")
router.register("academic-sessions", AcademicSessionViewSet, basename="academic-session")
router.register("sections", ClassSectionViewSet, basename="section")
router.register("teacher-subject-allocations", TeacherSubjectAllocationViewSet, basename="teacher-subject-allocation")
router.register("students", StudentViewSet, basename="student")
router.register("student-guardians", StudentGuardianViewSet, basename="student-guardian")
router.register("attendance-records", AttendanceRecordViewSet, basename="attendance-record")
router.register("staff-attendance-records", StaffAttendanceRecordViewSet, basename="staff-attendance-record")
router.register("staff-profiles", StaffProfileViewSet, basename="staff-profile")
router.register("timetable-slots", TimetableSlotViewSet, basename="timetable-slot")
router.register("library-books", LibraryBookViewSet, basename="library-book")
router.register("library-loans", LibraryLoanViewSet, basename="library-loan")
router.register("transport-routes", TransportRouteViewSet, basename="transport-route")
router.register("transport-vehicles", TransportVehicleViewSet, basename="transport-vehicle")
router.register("student-transport-assignments", StudentTransportAssignmentViewSet, basename="student-transport-assignment")
router.register("hostel-rooms", HostelRoomViewSet, basename="hostel-room")
router.register("hostel-allocations", HostelAllocationViewSet, basename="hostel-allocation")
router.register("announcements", AnnouncementViewSet, basename="announcement")
router.register("approval-requests", ApprovalRequestViewSet, basename="approval-request")
router.register("support-tickets", SupportTicketViewSet, basename="support-ticket")
router.register("assigned-work", AssignedWorkViewSet, basename="assigned-work")
router.register("learning-resources", LearningResourceViewSet, basename="learning-resource")
router.register("result-records", ResultRecordViewSet, basename="result-record")
router.register("admit-cards", AdmitCardViewSet, basename="admit-card")
router.register("fee-assignments", FeeAssignmentViewSet, basename="fee-assignment")
router.register("payments", PaymentViewSet, basename="payment")
router.register("payment-transactions", PaymentTransactionViewSet, basename="payment-transaction")
router.register("salary-records", SalaryRecordViewSet, basename="salary-record")
router.register("message-templates", MessageTemplateViewSet, basename="message-template")
router.register("outbound-messages", OutboundMessageViewSet, basename="outbound-message")
router.register("ai-logs", AILogViewSet, basename="ai-log")
router.register("documents", DocumentViewSet, basename="document")
router.register("platform-settings", PlatformSettingViewSet, basename="platform-setting")
router.register("audit-events", AuditEventViewSet, basename="audit-event")

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("reports/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("", include(router.urls)),
]

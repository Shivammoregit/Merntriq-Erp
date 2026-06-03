export const roleTabs = ["Admin", "Teacher", "Student", "Parent"] as const;

export const overviewMetrics = [
  { label: "Connected modules", value: "21", delta: "Admissions, SIS, parent portal, staff, finance, exams, services, analytics, security", tone: "info" },
  { label: "Active roles", value: "5", delta: "Super Admin, Admin, Teacher, Student, Parent", tone: "accent" },
  { label: "Core records", value: "20+", delta: "Campus, users, students, attendance, fees, academics, support, audit", tone: "warning" },
  { label: "Workflow lanes", value: "8", delta: "Admissions, People, Academics, Operations, Finance, Services, Leadership, Security", tone: "danger" }
] as const;

export const workflowPhases = [
  {
    id: "auth",
    label: "Authentication",
    icon: "ShieldCheck",
    title: "Login, register, and route by role",
    description:
      "The frontend starts with a secure login gate, then sends the user to the correct workspace based on the backend role returned by JWT.",
    backend: ["accounts.UserRole", "JWT token pair", "Current user profile", "Parent guardian links"],
    ui: ["Login / Register", "Role decision", "Session shell"],
    outcome: "Authenticated access with role-specific landing"
  },
  {
    id: "admin",
    label: "Admin Flow",
    icon: "LayoutDashboard",
    title: "Create campus admins, students, and class sections",
    description:
      "The admin flow mirrors the diagram and adds campus separation: super admins create campuses, assign IT admins, add students, assign class sections, and approve operational changes.",
    backend: ["Campus", "CampusMembership", "AcademicSession", "ClassSection", "Student", "ApprovalRequest"],
    ui: ["Campus control", "User admin", "Student intake form", "Approval queue"],
    outcome: "Campus-scoped users, students, and approvals ready for downstream operations"
  },
  {
    id: "attendance",
    label: "Attendance Flow",
    icon: "UserRoundCheck",
    title: "Teacher and hardware attendance by class",
    description:
      "Teachers select a section, view the student list, choose manual, face recognition, fingerprint, or card scan as the source, and submit attendance for admin and student visibility.",
    backend: ["AttendanceRecord", "StaffAttendanceRecord", "AttendanceDevice", "ClassSection", "Student"],
    ui: ["Attendance panel", "Hardware source selector", "Teacher attendance"],
    outcome: "Daily student and staff attendance stored with source and device traceability"
  },
  {
    id: "fees",
    label: "Fees Flow",
    icon: "ReceiptText",
    title: "Assign fees, collect payments, and track dues",
    description:
      "Finance and admin users create fee assignments, attach the student, capture payment, and auto-refresh the fee status when a payment lands.",
    backend: ["FeeAssignment", "Payment", "FeeStatus", "PaymentMethod"],
    ui: ["Fee record", "Assign to student", "Payment entry"],
    outcome: "Receivables, receipts, and payment history stay synchronized"
  }
] as const;

export const moduleCards = [
  {
    title: "Authentication Module",
    description: "Handles login, registration, password rules, and role-aware redirects.",
    icon: "ShieldCheck",
    backend: ["User", "UserRole", "Token obtain pair", "CurrentUserView"]
  },
  {
    title: "Student Module",
    description: "Stores campus, section, identity, and status for every student record.",
    icon: "GraduationCap",
    backend: ["Campus", "AcademicSession", "ClassSection", "Student"]
  },
  {
    title: "Attendance Module",
    description: "Captures manual and hardware-sourced attendance for students and staff.",
    icon: "ClipboardCheck",
    backend: ["AttendanceRecord", "StaffAttendanceRecord", "AttendanceDevice"]
  },
  {
    title: "Campus Control",
    description: "Scopes admins, teachers, devices, and approvals to each campus.",
    icon: "ShieldCheck",
    backend: ["CampusMembership", "ApprovalRequest", "AuditEvent"]
  },
  {
    title: "Fee Module",
    description: "Creates the payable structure, due dates, and status refresh logic.",
    icon: "ReceiptText",
    backend: ["FeeAssignment", "FeeStatus", "PaymentMethod"]
  },
  {
    title: "Payment Module",
    description: "Records cash, card, bank, and online receipts against the assigned fee.",
    icon: "CreditCard",
    backend: ["Payment", "FeeAssignment", "Collected by user"]
  }
] as const;

export const flowNodes = [
  "Authentication",
  "Campus and user scope",
  "Student master data",
  "Attendance and hardware",
  "Fees module",
  "Payment records",
  "Student workspace"
] as const;

export const roleWorkspaces = {
  Admin: ["Admissions", "SIS", "Staff", "Fees", "Exams", "Services", "Reports"],
  Teacher: ["My classes", "Attendance", "Homework", "Resources", "Results", "Timetable"],
  Student: ["Homework", "Attendance", "Results", "Notes", "Admit card", "Library"],
  Parent: ["Linked students", "Attendance", "Fees", "Results", "Transport", "Hostel"]
} as const;

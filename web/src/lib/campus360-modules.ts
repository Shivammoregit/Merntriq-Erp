import {
  BarChart3,
  BedDouble,
  BellRing,
  BookOpen,
  Bus,
  CalendarDays,
  ClipboardCheck,
  FileBadge2,
  FileText,
  GraduationCap,
  IdCard,
  Landmark,
  LibraryBig,
  LockKeyhole,
  MonitorPlay,
  PackageCheck,
  ReceiptText,
  Users,
} from "lucide-react";
import type { UserRole } from "@/lib/api";

export type Campus360ModuleStatus = "live" | "configured" | "foundation";
export type Campus360PermissionLevel = "manage" | "operate" | "view";
export type Campus360ModuleArea =
  | "Admissions"
  | "Academics"
  | "People"
  | "Operations"
  | "Finance"
  | "Services"
  | "Leadership"
  | "Security";

export type Campus360Module = {
  id: string;
  number: number;
  title: string;
  area: Campus360ModuleArea;
  status: Campus360ModuleStatus;
  summary: string;
  owner: string;
  responsibility: string;
  features: string[];
  components: string[];
  roles: UserRole[];
  permissions: Partial<Record<UserRole, Campus360PermissionLevel>>;
  icon: React.ComponentType<{ size?: number; className?: string }>;
};

export type RoleDefinition = {
  role: UserRole;
  label: string;
  access: string;
  responsibility: string;
};

export const roleDefinitions: RoleDefinition[] = [
  {
    role: "super_admin",
    label: "Super Admin",
    access: "Full institution access",
    responsibility: "Creates campuses, controls global settings, audits activity, and resolves support issues.",
  },
  {
    role: "admin",
    label: "School Admin",
    access: "Campus-scoped management",
    responsibility: "Manages students, staff, fees, attendance settings, reports, and campus operations.",
  },
  {
    role: "account",
    label: "Account",
    access: "School-scoped finance operations",
    responsibility: "Manages fees, receipts, payment reminders, transactions, refunds, and attendance-based salary records.",
  },
  {
    role: "teacher",
    label: "Teacher",
    access: "Assigned class operations",
    responsibility: "Marks attendance, uploads homework/resources, records marks, and reviews learner progress.",
  },
  {
    role: "student",
    label: "Student",
    access: "Own record view",
    responsibility: "Views personal attendance, work, results, fees, resources, admit cards, notices, and parent view.",
  },
];

const adminPermissions = {
  super_admin: "manage",
  admin: "manage",
} satisfies Partial<Record<UserRole, Campus360PermissionLevel>>;

const academicPermissions = {
  super_admin: "manage",
  admin: "manage",
  teacher: "operate",
  student: "view",
} satisfies Partial<Record<UserRole, Campus360PermissionLevel>>;

const learnerViewPermissions = {
  super_admin: "manage",
  admin: "manage",
  student: "view",
} satisfies Partial<Record<UserRole, Campus360PermissionLevel>>;

const financePermissions = {
  super_admin: "manage",
  admin: "manage",
  account: "operate",
  student: "view",
} satisfies Partial<Record<UserRole, Campus360PermissionLevel>>;

export const campus360Modules: Campus360Module[] = [
  {
    id: "admission-registration",
    number: 1,
    title: "Admission & Registration",
    area: "Admissions",
    status: "live",
    summary: "Student intake, approval, ID generation, and class allocation.",
    owner: "Admissions office",
    responsibility: "Capture applications, verify documents, approve admissions, and assign classes.",
    features: [
      "Online student registration",
      "Admission form management",
      "Document upload for Aadhar and marksheet",
      "Admission approval system",
      "Student ID generation",
      "Section and class allocation",
    ],
    components: ["Application form", "Document upload", "Approval queue", "Student ID card", "Class allocation"],
    roles: ["super_admin", "admin"],
    permissions: adminPermissions,
    icon: IdCard,
  },
  {
    id: "student-information-system",
    number: 2,
    title: "Student Information System (SIS)",
    area: "People",
    status: "live",
    summary: "Complete student profile, guardian, medical, academic, and document records.",
    owner: "Student records team",
    responsibility: "Maintain accurate student, guardian, academic, medical, and document records.",
    features: [
      "Student profile management",
      "Academic history",
      "Address and guardian details",
      "Medical information",
      "Student document storage",
    ],
    components: ["Student profile", "Guardian record", "Academic history", "Medical notes", "Document vault"],
    roles: ["super_admin", "admin", "teacher", "student"],
    permissions: academicPermissions,
    icon: GraduationCap,
  },
  {
    id: "student-parent-view",
    number: 3,
    title: "Parent View Inside Student Portal",
    area: "People",
    status: "live",
    summary: "Parent-facing access to student progress, fees, attendance, transport, hostel, and notices inside the student login.",
    owner: "Student services team",
    responsibility: "Keep parent visibility inside the student portal without issuing a separate parent account.",
    features: [
      "Linked student profiles",
      "Attendance and academic progress view",
      "Fee and receipt visibility",
      "Transport and hostel status",
      "School announcements",
    ],
    components: ["Parent view", "Student dashboard", "Fee view", "Student updates", "Announcements"],
    roles: ["super_admin", "admin", "student"],
    permissions: {
      super_admin: "manage",
      admin: "manage",
      student: "view",
    },
    icon: Users,
  },
  {
    id: "staff-employee-management",
    number: 4,
    title: "Staff / Employee Management",
    area: "People",
    status: "configured",
    summary: "Employee records, teacher profiles, role assignment, salary, and leave structure.",
    owner: "HR and administration",
    responsibility: "Maintain staff records, assign roles, manage salary structure, and track leave.",
    features: [
      "Employee registration",
      "Teacher profile management",
      "Role assignment",
      "Salary structure",
      "Leave management",
    ],
    components: ["Employee form", "Teacher profile", "Role assignment", "Salary structure", "Leave tracker"],
    roles: ["super_admin", "admin", "account"],
    permissions: {
      super_admin: "manage",
      admin: "manage",
      account: "operate",
    },
    icon: Users,
  },
  {
    id: "attendance-management",
    number: 5,
    title: "Attendance Management",
    area: "Operations",
    status: "live",
    summary: "Student and teacher attendance with biometric/RFID-ready capture and reports.",
    owner: "Operations team",
    responsibility: "Track attendance, connect capture devices, review reports, and alert absences.",
    features: [
      "Student attendance",
      "Teacher attendance",
      "Biometric and RFID attendance integration",
      "Attendance reports",
      "SMS alerts for absence",
    ],
    components: ["Attendance roster", "Staff attendance", "Device integration", "Reports", "Absence alerts"],
    roles: ["super_admin", "admin", "teacher", "student"],
    permissions: academicPermissions,
    icon: ClipboardCheck,
  },
  {
    id: "fees-management",
    number: 6,
    title: "Fees Management",
    area: "Finance",
    status: "live",
    summary: "Fee setup, payment tracking, reminders, late fee logic, and receipts.",
    owner: "Finance team",
    responsibility: "Create fee structures, collect payments, issue receipts, and monitor dues.",
    features: [
      "Fee structure setup",
      "Online fee payment",
      "Fee reminders",
      "Late fee calculation",
      "Receipt generation",
    ],
    components: ["Fee structure", "Payment entry", "Due reminders", "Late fee rules", "Receipts"],
    roles: ["super_admin", "admin", "account", "student"],
    permissions: financePermissions,
    icon: ReceiptText,
  },
  {
    id: "examination-management",
    number: 7,
    title: "Examination Management",
    area: "Academics",
    status: "live",
    summary: "Exam setup, admit cards, marks entry, and result processing.",
    owner: "Examination cell",
    responsibility: "Plan exams, issue admit cards, collect marks, and process results.",
    features: [
      "Exam schedule creation",
      "Subject wise exam setup",
      "Admit card generation",
      "Marks entry system",
      "Result processing",
    ],
    components: ["Exam schedule", "Subject setup", "Admit card", "Marks entry", "Result processing"],
    roles: ["super_admin", "admin", "teacher", "student"],
    permissions: academicPermissions,
    icon: FileText,
  },
  {
    id: "result-report-card",
    number: 8,
    title: "Result & Report Card",
    area: "Academics",
    status: "live",
    summary: "Report cards, GPA/percentage, rank, and progress reports.",
    owner: "Academic team",
    responsibility: "Publish report cards, calculate scores, and share progress with learners.",
    features: [
      "Automated report cards",
      "GPA and percentage calculation",
      "Rank system",
      "Progress report",
      "Student access to results",
    ],
    components: ["Report card", "GPA/percentage", "Rank list", "Progress report", "Student result view"],
    roles: ["super_admin", "admin", "teacher", "student"],
    permissions: academicPermissions,
    icon: FileBadge2,
  },
  {
    id: "certificate-tc",
    number: 9,
    title: "Certificate & TC Module",
    area: "Admissions",
    status: "foundation",
    summary: "Transfer certificate, bonafide, character certificate, marksheet, and signature flows.",
    owner: "Administration office",
    responsibility: "Generate certificates, print marksheets, and manage digital signature approvals.",
    features: [
      "Transfer Certificate generation",
      "Bonafide certificate",
      "Character certificate",
      "Marksheet printing",
      "Digital signature support",
    ],
    components: ["TC generator", "Bonafide certificate", "Character certificate", "Marksheet print", "Digital signature"],
    roles: ["super_admin", "admin"],
    permissions: adminPermissions,
    icon: FileBadge2,
  },
  {
    id: "homework-assignment",
    number: 10,
    title: "Homework & Assignment",
    area: "Academics",
    status: "live",
    summary: "Teacher homework upload, learner submission, files, and deadline reminders.",
    owner: "Teachers",
    responsibility: "Publish homework, collect submissions, attach files, and remind learners before deadlines.",
    features: [
      "Homework upload by teachers",
      "Assignment submission",
      "File upload system",
      "Deadline reminders",
    ],
    components: ["Homework upload", "Assignment submission", "File upload", "Deadline reminder"],
    roles: ["super_admin", "admin", "teacher", "student"],
    permissions: academicPermissions,
    icon: BookOpen,
  },
  {
    id: "timetable-management",
    number: 11,
    title: "Timetable Management",
    area: "Academics",
    status: "foundation",
    summary: "Class timetable, teacher timetable, and auto timetable generation workflows.",
    owner: "Academic scheduler",
    responsibility: "Create class and teacher timetables and reduce clashes with auto scheduling.",
    features: [
      "Class timetable creation",
      "Teacher timetable",
      "Auto timetable generator",
    ],
    components: ["Class timetable", "Teacher timetable", "Auto generator"],
    roles: ["super_admin", "admin", "teacher", "student"],
    permissions: academicPermissions,
    icon: CalendarDays,
  },
  {
    id: "library-management",
    number: 12,
    title: "Library Management",
    area: "Services",
    status: "foundation",
    summary: "Book catalog, issue/return, fine calculation, and barcode-ready library operations.",
    owner: "Library team",
    responsibility: "Track books, issue and return materials, calculate fines, and support barcode scanning.",
    features: [
      "Book catalog",
      "Issue and return books",
      "Fine calculation",
      "Barcode system",
    ],
    components: ["Book catalog", "Issue/return", "Fine calculation", "Barcode scanner"],
    roles: ["super_admin", "admin", "teacher", "student"],
    permissions: {
      super_admin: "manage",
      admin: "manage",
      teacher: "view",
      student: "view",
    },
    icon: LibraryBig,
  },
  {
    id: "transport-management",
    number: 13,
    title: "Transport Management",
    area: "Services",
    status: "foundation",
    summary: "Bus routes, driver details, GPS tracking integration, and transport fee linkage.",
    owner: "Transport team",
    responsibility: "Manage routes, driver information, GPS tracking, and transport fee records.",
    features: [
      "Bus route management",
      "Driver details",
      "Bus tracking with GPS integration",
      "Transport fee",
    ],
    components: ["Bus routes", "Driver records", "GPS tracking", "Transport fee"],
    roles: ["super_admin", "admin", "student"],
    permissions: learnerViewPermissions,
    icon: Bus,
  },
  {
    id: "hostel-management",
    number: 14,
    title: "Hostel Management",
    area: "Services",
    status: "foundation",
    summary: "Room allocation, hostel fee, and student check-in/check-out management.",
    owner: "Hostel team",
    responsibility: "Allocate rooms, manage hostel fees, and track student check-in/out.",
    features: [
      "Room allocation",
      "Hostel fee",
      "Student check-in/out",
    ],
    components: ["Room allocation", "Hostel fee", "Check-in/out"],
    roles: ["super_admin", "admin", "student"],
    permissions: learnerViewPermissions,
    icon: BedDouble,
  },
  {
    id: "inventory-management",
    number: 15,
    title: "Inventory Management",
    area: "Operations",
    status: "foundation",
    summary: "Assets, lab equipment, purchase records, and operational stock tracking.",
    owner: "Store and inventory team",
    responsibility: "Track assets, lab equipment, purchases, and stock movement.",
    features: [
      "Asset tracking",
      "Lab equipment management",
      "Purchase records",
    ],
    components: ["Asset register", "Lab equipment", "Purchase records"],
    roles: ["super_admin", "admin"],
    permissions: adminPermissions,
    icon: PackageCheck,
  },
  {
    id: "communication-module",
    number: 16,
    title: "Communication Module",
    area: "Operations",
    status: "live",
    summary: "Announcements, alerts, email/SMS-ready notifications, and student messaging.",
    owner: "Communication team",
    responsibility: "Send alerts, publish announcements, notify students, and coordinate school messages.",
    features: [
      "SMS alerts",
      "Email notifications",
      "Announcement board",
      "Student messaging",
    ],
    components: ["SMS alerts", "Email notifications", "Announcement board", "Student messaging"],
    roles: ["super_admin", "admin", "account", "teacher", "student"],
    permissions: {
      super_admin: "manage",
      admin: "manage",
      account: "operate",
      teacher: "operate",
      student: "view",
    },
    icon: BellRing,
  },
  {
    id: "online-learning",
    number: 17,
    title: "Online Learning Module",
    area: "Academics",
    status: "configured",
    summary: "Study material, videos, quizzes, and online exam foundations.",
    owner: "Academic digital learning team",
    responsibility: "Upload materials, share videos, run quizzes, and support online exams.",
    features: [
      "Study material upload",
      "Video lectures",
      "Online quizzes",
      "Online exams",
    ],
    components: ["Study material", "Video lectures", "Online quizzes", "Online exams"],
    roles: ["super_admin", "admin", "teacher", "student"],
    permissions: academicPermissions,
    icon: MonitorPlay,
  },
  {
    id: "analytics-reports",
    number: 18,
    title: "Analytics & Reports",
    area: "Leadership",
    status: "live",
    summary: "Attendance, financial, academic, and staff performance reporting.",
    owner: "Leadership and reporting team",
    responsibility: "Review attendance, finance, academics, and staff performance reports.",
    features: [
      "Attendance analytics",
      "Financial reports",
      "Academic performance reports",
      "Staff performance reports",
    ],
    components: ["Attendance analytics", "Financial reports", "Academic reports", "Staff reports"],
    roles: ["super_admin", "admin", "account", "teacher"],
    permissions: {
      super_admin: "manage",
      admin: "manage",
      account: "view",
      teacher: "view",
    },
    icon: BarChart3,
  },
  {
    id: "director-dashboard",
    number: 19,
    title: "Director Dashboard",
    area: "Leadership",
    status: "live",
    summary: "Institution analytics, financial overview, productivity, and admission statistics.",
    owner: "Director and management",
    responsibility: "Monitor institution health, finance, staff productivity, and admission trends.",
    features: [
      "Institution analytics",
      "Financial overview",
      "Staff productivity",
      "Admission statistics",
    ],
    components: ["Institution analytics", "Financial overview", "Staff productivity", "Admission statistics"],
    roles: ["super_admin", "admin"],
    permissions: adminPermissions,
    icon: Landmark,
  },
  {
    id: "security-access-control",
    number: 20,
    title: "Security & Access Control",
    area: "Security",
    status: "live",
    summary: "Role-based login, permissions, data protection, and activity logs.",
    owner: "IT security team",
    responsibility: "Control access, apply permissions, protect data, and monitor activity logs.",
    features: [
      "Role-based login",
      "Multi-level permissions",
      "Data encryption",
      "Activity logs",
    ],
    components: ["Role login", "Permission matrix", "Data protection", "Activity logs"],
    roles: ["super_admin", "admin"],
    permissions: adminPermissions,
    icon: LockKeyhole,
  },
];

export const moduleAreas: Campus360ModuleArea[] = [
  "Admissions",
  "People",
  "Academics",
  "Operations",
  "Finance",
  "Services",
  "Leadership",
  "Security",
];

export function modulesForRole(role: UserRole) {
  return campus360Modules.filter((module) => module.roles.includes(role));
}

export function permissionLabel(level?: Campus360PermissionLevel) {
  if (level === "manage") return "Manage";
  if (level === "operate") return "Use";
  if (level === "view") return "View";
  return "No access";
}

export function roleDefinitionFor(role: UserRole) {
  return roleDefinitions.find((item) => item.role === role);
}

export function statusLabel(status: Campus360ModuleStatus) {
  if (status === "live") return "Ready";
  if (status === "configured") return "Setup";
  return "Planned";
}

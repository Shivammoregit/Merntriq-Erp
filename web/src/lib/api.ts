/**
 * Mentriq360 typed API client
 * All backend calls go through this module so token management is centralised.
 */

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const AUTH_BASE = process.env.NEXT_PUBLIC_API_BASE_URL
  ? process.env.NEXT_PUBLIC_API_BASE_URL.replace("/api/v1", "/api/v1/auth")
  : "http://localhost:8000/api/v1/auth";
const REQUEST_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_API_TIMEOUT_MS ?? "20000");
export const SESSION_EXPIRED_EVENT = "mentriq360-session-expired";

// ─── Token helpers ────────────────────────────────────────────────────────────
function getAccess() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("erp_access");
}
function getRefresh() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("erp_refresh");
}
export function storeTokens(access: string, refresh: string) {
  localStorage.setItem("erp_access", access);
  localStorage.setItem("erp_refresh", refresh);
}
export function clearTokens() {
  localStorage.removeItem("erp_access");
  localStorage.removeItem("erp_refresh");
}
export function hasTokens() {
  return !!getAccess();
}

function notifySessionExpired() {
  clearTokens();
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT));
  }
}

// ─── Core fetch wrapper ───────────────────────────────────────────────────────
async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefresh();
  if (!refresh) return null;
  try {
    const res = await fetch(`${AUTH_BASE}/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) { clearTokens(); return null; }
    const data = await res.json();
    storeTokens(data.access, refresh);
    return data.access;
  } catch {
    clearTokens();
    return null;
  }
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  retried = false
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  const token = getAccess();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const url = path.startsWith("http") ? path : `${BASE}${path}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  let res: Response;
  try {
    res = await fetch(url, {
      ...options,
      headers,
      signal: options.signal ?? controller.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(0, "Request timed out. Please check the network and try again.");
    }
    throw new ApiError(0, "Network connection failed. Please check the server or internet connection.");
  } finally {
    clearTimeout(timeout);
  }

  if (res.status === 401 && !retried) {
    const newToken = await refreshAccessToken();
    if (newToken) return apiFetch<T>(path, options, true);
    notifySessionExpired();
    throw new ApiError(401, "Session expired. Please log in again.");
  }

  if (res.status === 401) {
    notifySessionExpired();
    throw new ApiError(401, "Session expired. Please log in again.");
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      detail = err.detail ?? err.non_field_errors?.[0] ?? JSON.stringify(err);
    } catch { /* ignore */ }
    if (res.status === 429) {
      detail = "Too many requests. Please wait a moment and try again.";
    }
    throw new ApiError(res.status, detail);
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

// ─── Type definitions ─────────────────────────────────────────────────────────
export type UserRole = "super_admin" | "admin" | "teacher" | "parent" | "student";

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: UserRole;
  campuses?: UserCampusScope[];
  is_active: boolean;
}

export interface ERPUser extends User {
  phone_number: string;
  must_change_password: boolean;
  is_staff: boolean;
  campuses?: UserCampusScope[];
  created_at: string;
  updated_at: string;
}

export interface UserCampusScope {
  id: number;
  name: string;
  code: string;
  role: string;
  is_primary: boolean;
  can_manage_users?: boolean;
  can_configure_attendance?: boolean;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface CaptchaChallenge {
  challenge_id: string;
  image: string;
  expires_in: number;
  expires_at: string;
}

export interface Campus {
  id: number;
  name: string;
  code: string;
  address: string;
  created_at?: string;
  updated_at?: string;
}

export type CampusMemberRole =
  | "it_admin"
  | "academic_admin"
  | "finance_admin"
  | "hr_admin"
  | "teacher"
  | "support";

export interface CampusMembership {
  id: number;
  campus: number;
  campus_name?: string;
  user: number;
  user_name?: string;
  user_role?: UserRole;
  role: CampusMemberRole;
  is_primary: boolean;
  can_manage_users: boolean;
  can_configure_attendance: boolean;
  created_at?: string;
  updated_at?: string;
}

export type AttendanceCaptureMethod = "manual" | "face_recognition" | "fingerprint" | "card_scan";
export type AttendanceDeviceStatus = "active" | "inactive" | "maintenance";
export type AttendanceRS485Function = "software" | "hardware" | "disabled";

export interface AttendanceDevice {
  id: number;
  campus: number;
  campus_name?: string;
  name: string;
  device_code: string;
  device_type: AttendanceCaptureMethod;
  location: string;
  provider: string;
  status: AttendanceDeviceStatus;
  is_enabled_for_students: boolean;
  is_enabled_for_staff: boolean;
  server_required: boolean;
  use_domain_name: boolean;
  domain_name: string;
  server_ip: string;
  server_port: number;
  heartbeat_seconds: number;
  server_approval_required: boolean;
  device_numeric_id: number;
  local_port: number;
  baud_rate: number;
  rs485_function: AttendanceRS485Function;
  last_seen_at: string | null;
  configured_by: number | null;
  configured_by_name?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AcademicSession {
  id: number;
  campus: number;
  campus_name?: string;
  name: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ClassSection {
  id: number;
  campus: number;
  campus_name?: string;
  session: number;
  grade_name: string;
  section_name: string;
  label?: string;
  class_teacher: number | null;
  class_teacher_name?: string;
  created_at?: string;
  updated_at?: string;
}

export type StudentStatus = "active" | "inactive" | "alumni";

export interface Student {
  id: number;
  campus: number;
  campus_name?: string;
  section: number;
  section_label?: string;
  user?: number | null;
  user_name?: string;
  admission_number: string;
  first_name: string;
  last_name: string;
  full_name: string;
  date_of_birth: string;
  father_name: string;
  mother_name: string;
  contact_email: string;
  phone_number: string;
  alternate_phone_number: string;
  address: string;
  blood_group: string;
  medical_notes: string;
  status: StudentStatus;
  created_at?: string;
  updated_at?: string;
}

export type AttendanceStatus = "present" | "absent" | "on_duty";

export interface AttendanceRecord {
  id: number;
  student: number;
  student_name?: string;
  section: number;
  section_label?: string;
  date: string;
  status: AttendanceStatus;
  marked_by: number | null;
  capture_method: AttendanceCaptureMethod;
  device: number | null;
  device_name?: string;
  source_reference: string;
  confidence_score: string | null;
  created_at: string;
  updated_at?: string;
}

export type StaffAttendanceStatus = "present" | "absent" | "late" | "half_day" | "on_leave";

export interface StaffAttendanceRecord {
  id: number;
  campus: number;
  campus_name?: string;
  staff_user: number;
  staff_name?: string;
  staff_role?: UserRole;
  date: string;
  clock_in: string | null;
  clock_out: string | null;
  status: StaffAttendanceStatus;
  capture_method: AttendanceCaptureMethod;
  device: number | null;
  device_name?: string;
  marked_by: number | null;
  marked_by_name?: string;
  source_reference: string;
  confidence_score: string | null;
  notes: string;
  created_at?: string;
  updated_at?: string;
}

export type AcademicWorkStatus = "draft" | "published" | "closed";

export interface AssignedWork {
  id: number;
  section: number;
  section_label?: string;
  assigned_by: number | null;
  assigned_by_name?: string;
  title: string;
  subject: string;
  description: string;
  due_date: string;
  status: AcademicWorkStatus;
  created_at?: string;
  updated_at?: string;
}

export type ResourceType = "notes" | "syllabus" | "assignment_help" | "reference";

export interface LearningResource {
  id: number;
  section: number;
  section_label?: string;
  uploaded_by: number | null;
  uploaded_by_name?: string;
  title: string;
  subject: string;
  resource_type: ResourceType;
  description: string;
  file_url: string;
  published_on: string;
  created_at?: string;
  updated_at?: string;
}

export interface ResultRecord {
  id: number;
  student: number;
  student_name?: string;
  section_label?: string;
  recorded_by: number | null;
  recorded_by_name?: string;
  exam_name: string;
  subject: string;
  score: string;
  max_score: string;
  percentage?: string;
  grade: string;
  remarks: string;
  published_on: string;
  created_at?: string;
  updated_at?: string;
}

export type AdmitCardStatus = "draft" | "issued" | "blocked";

export interface AdmitCard {
  id: number;
  student: number;
  student_name?: string;
  admission_number?: string;
  section_label?: string;
  issued_by: number | null;
  issued_by_name?: string;
  exam_name: string;
  roll_number: string;
  exam_date: string;
  reporting_time: string;
  venue: string;
  instructions: string;
  status: AdmitCardStatus;
  issued_on: string;
  created_at?: string;
  updated_at?: string;
}

export type FeeStatus = "pending" | "partial" | "paid" | "overdue";

export interface FeeAssignment {
  id: number;
  student: number;
  student_name?: string;
  title: string;
  amount: string;
  amount_paid?: string;
  outstanding_amount?: string;
  due_date: string;
  status: FeeStatus;
  created_at?: string;
  updated_at?: string;
}

export type PaymentMethod = "cash" | "card" | "bank" | "online";

export interface Payment {
  id: number;
  fee_assignment: number;
  fee_title?: string;
  student_name?: string;
  amount_paid: string;
  paid_on: string;
  payment_method: PaymentMethod;
  reference_number: string;
  collected_by: number | null;
  created_at?: string;
  updated_at?: string;
}

export interface AuditEvent {
  id: number;
  actor: number | null;
  actor_name: string;
  action: string;
  entity_type: string;
  entity_id: string;
  summary: string;
  ip_address: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export type ApprovalStatus = "pending" | "approved" | "rejected";
export type AnnouncementAudience = "all" | "admins" | "staff" | "learners";
export type SupportTicketStatus = "open" | "in_progress" | "resolved";
export type SupportTicketPriority = "normal" | "high" | "urgent";

export interface ApprovalRequest {
  id: number;
  campus: number;
  campus_name?: string;
  title: string;
  entity_type: string;
  entity_id: string;
  description: string;
  payload: Record<string, unknown>;
  status: ApprovalStatus;
  requested_by: number | null;
  requested_by_name?: string;
  reviewed_by: number | null;
  reviewed_by_name?: string;
  decided_at: string | null;
  decision_note: string;
  created_at?: string;
  updated_at?: string;
}

export interface Announcement {
  id: number;
  title: string;
  message: string;
  audience: AnnouncementAudience;
  created_by: number | null;
  created_by_name: string;
  is_active: boolean;
  publish_on: string;
  created_at?: string;
  updated_at?: string;
}

export interface SupportTicket {
  id: number;
  campus: number | null;
  campus_name?: string;
  created_by: number;
  created_by_name: string;
  created_by_role: UserRole;
  reviewed_by: number | null;
  reviewed_by_name?: string;
  subject: string;
  message: string;
  category: string;
  priority: SupportTicketPriority;
  status: SupportTicketStatus;
  response_note: string;
  resolved_at: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface DashboardSummary {
  students: {
    total: number;
    active: number;
  };
  attendance: {
    total: number;
    by_status: Partial<Record<AttendanceStatus, number>>;
    by_section: {
      section: number;
      label: string;
      total: number;
      present: number;
      absent: number;
    }[];
  };
  fees: {
    total_assigned: string;
    total_collected: string;
    total_outstanding: string;
    by_status: Partial<Record<FeeStatus, number>>;
  };
  staff_attendance?: {
    total: number;
    by_status: Partial<Record<StaffAttendanceStatus, number>>;
  };
  devices?: {
    total: number;
    active: number;
    by_type: Partial<Record<AttendanceCaptureMethod, number>>;
  };
  approvals?: {
    pending: number;
    approved: number;
    rejected: number;
  };
  recent_payments: {
    id: number;
    student_name: string;
    fee_title: string;
    amount_paid: string;
    paid_on: string;
    payment_method: PaymentMethod;
    reference_number: string;
  }[];
}

// Paginated DRF response wrapper
export interface PagedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// ─── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  captcha: () => apiFetch<CaptchaChallenge>(`${AUTH_BASE}/captcha/`),

  login: (username: string, password: string, captcha_id: string, captcha_answer: string) =>
    apiFetch<LoginResponse>(`${AUTH_BASE}/token/`, {
      method: "POST",
      body: JSON.stringify({ username, password, captcha_id, captcha_answer }),
    }),

  me: () => apiFetch<User>(`${AUTH_BASE}/me/`),
};

export const userApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<ERPUser[]>(`${AUTH_BASE}/users/${q}`);
  },
  create: (data: Partial<ERPUser> & { username: string; password?: string; role: UserRole; campus_ids?: number[] }) =>
    apiFetch<ERPUser>(`${AUTH_BASE}/users/`, { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<ERPUser> & { password?: string; campus_ids?: number[] }) =>
    apiFetch<ERPUser>(`${AUTH_BASE}/users/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  remove: (id: number) => apiFetch<void>(`${AUTH_BASE}/users/${id}/`, { method: "DELETE" }),
};

// ─── Campus ──────────────────────────────────────────────────────────────────
export const campusApi = {
  list: () => apiFetch<Campus[]>("/campuses/"),
  get: (id: number) => apiFetch<Campus>(`/campuses/${id}/`),
  create: (data: Omit<Campus, "id">) =>
    apiFetch<Campus>("/campuses/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<Campus>) =>
    apiFetch<Campus>(`/campuses/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  remove: (id: number) => apiFetch<void>(`/campuses/${id}/`, { method: "DELETE" }),
};

export const campusMembershipApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<CampusMembership[]>(`/campus-memberships/${q}`);
  },
  create: (data: Omit<CampusMembership, "id" | "campus_name" | "user_name" | "user_role">) =>
    apiFetch<CampusMembership>("/campus-memberships/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<CampusMembership>) =>
    apiFetch<CampusMembership>(`/campus-memberships/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  remove: (id: number) => apiFetch<void>(`/campus-memberships/${id}/`, { method: "DELETE" }),
};

export const attendanceDeviceApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<AttendanceDevice[]>(`/attendance-devices/${q}`);
  },
  create: (data: Omit<AttendanceDevice, "id" | "campus_name" | "configured_by" | "configured_by_name" | "last_seen_at">) =>
    apiFetch<AttendanceDevice>("/attendance-devices/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<AttendanceDevice>) =>
    apiFetch<AttendanceDevice>(`/attendance-devices/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  remove: (id: number) => apiFetch<void>(`/attendance-devices/${id}/`, { method: "DELETE" }),
  capture: (
    id: number,
    data: {
      person_type: "student" | "staff";
      external_id: string;
      captured_at?: string;
      status?: AttendanceStatus | StaffAttendanceStatus;
      source_reference?: string;
      confidence_score?: string;
    }
  ) =>
    apiFetch<AttendanceRecord | StaffAttendanceRecord>(`/attendance-devices/${id}/capture/`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

export const sessionApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<AcademicSession[]>(`/academic-sessions/${q}`);
  },
  create: (data: Omit<AcademicSession, "id">) =>
    apiFetch<AcademicSession>("/academic-sessions/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<AcademicSession>) =>
    apiFetch<AcademicSession>(`/academic-sessions/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  remove: (id: number) => apiFetch<void>(`/academic-sessions/${id}/`, { method: "DELETE" }),
};

// ─── Sections ────────────────────────────────────────────────────────────────
export const sectionApi = {
  list: () => apiFetch<ClassSection[]>("/sections/"),
  get: (id: number) => apiFetch<ClassSection>(`/sections/${id}/`),
  create: (data: Omit<ClassSection, "id">) =>
    apiFetch<ClassSection>("/sections/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<ClassSection>) =>
    apiFetch<ClassSection>(`/sections/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  remove: (id: number) => apiFetch<void>(`/sections/${id}/`, { method: "DELETE" }),
};

// ─── Students ────────────────────────────────────────────────────────────────
export const studentApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<Student[]>(`/students/${q}`);
  },
  get: (id: number) => apiFetch<Student>(`/students/${id}/`),
  create: (data: Omit<Student, "id" | "full_name">) =>
    apiFetch<Student>("/students/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<Student>) =>
    apiFetch<Student>(`/students/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  remove: (id: number) => apiFetch<void>(`/students/${id}/`, { method: "DELETE" }),
};

// ─── Attendance ───────────────────────────────────────────────────────────────
export const attendanceApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<AttendanceRecord[]>(`/attendance-records/${q}`);
  },
  create: (data: {
    student: number;
    section: number;
    date: string;
    status: AttendanceStatus;
    capture_method?: AttendanceCaptureMethod;
    device?: number | null;
    source_reference?: string;
    confidence_score?: string | null;
  }) =>
    apiFetch<AttendanceRecord>("/attendance-records/", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: number, data: Partial<AttendanceRecord>) =>
    apiFetch<AttendanceRecord>(`/attendance-records/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  bulkCreate: (records: {
    student: number;
    section: number;
    date: string;
    status: AttendanceStatus;
    capture_method?: AttendanceCaptureMethod;
    device?: number | null;
    source_reference?: string;
    confidence_score?: string | null;
  }[]) =>
    Promise.all(records.map((r) => attendanceApi.create(r))),
  bulkUpsert: (data: {
    section: number;
    date: string;
    capture_method?: AttendanceCaptureMethod;
    device?: number | null;
    source_reference?: string;
    confidence_score?: string;
    records: { student: number; status: AttendanceStatus }[];
  }) =>
    apiFetch<AttendanceRecord[]>("/attendance-records/bulk-upsert/", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

export const staffAttendanceApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<StaffAttendanceRecord[]>(`/staff-attendance-records/${q}`);
  },
  create: (data: Omit<StaffAttendanceRecord, "id" | "marked_by" | "marked_by_name" | "campus_name" | "staff_name" | "staff_role" | "device_name">) =>
    apiFetch<StaffAttendanceRecord>("/staff-attendance-records/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<StaffAttendanceRecord>) =>
    apiFetch<StaffAttendanceRecord>(`/staff-attendance-records/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  remove: (id: number) => apiFetch<void>(`/staff-attendance-records/${id}/`, { method: "DELETE" }),
};

export const assignedWorkApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<AssignedWork[]>(`/assigned-work/${q}`);
  },
  create: (data: Omit<AssignedWork, "id" | "assigned_by" | "assigned_by_name" | "section_label">) =>
    apiFetch<AssignedWork>("/assigned-work/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<AssignedWork>) =>
    apiFetch<AssignedWork>(`/assigned-work/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  remove: (id: number) => apiFetch<void>(`/assigned-work/${id}/`, { method: "DELETE" }),
};

export const learningResourceApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<LearningResource[]>(`/learning-resources/${q}`);
  },
  create: (data: Omit<LearningResource, "id" | "uploaded_by" | "uploaded_by_name" | "section_label">) =>
    apiFetch<LearningResource>("/learning-resources/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<LearningResource>) =>
    apiFetch<LearningResource>(`/learning-resources/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  remove: (id: number) => apiFetch<void>(`/learning-resources/${id}/`, { method: "DELETE" }),
};

export const resultRecordApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<ResultRecord[]>(`/result-records/${q}`);
  },
  create: (data: Omit<ResultRecord, "id" | "recorded_by" | "recorded_by_name" | "student_name" | "section_label" | "percentage">) =>
    apiFetch<ResultRecord>("/result-records/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<ResultRecord>) =>
    apiFetch<ResultRecord>(`/result-records/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  remove: (id: number) => apiFetch<void>(`/result-records/${id}/`, { method: "DELETE" }),
};

export const admitCardApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<AdmitCard[]>(`/admit-cards/${q}`);
  },
  create: (data: Omit<AdmitCard, "id" | "issued_by" | "issued_by_name" | "student_name" | "admission_number" | "section_label">) =>
    apiFetch<AdmitCard>("/admit-cards/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<AdmitCard>) =>
    apiFetch<AdmitCard>(`/admit-cards/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  remove: (id: number) => apiFetch<void>(`/admit-cards/${id}/`, { method: "DELETE" }),
};

// ─── Fee Assignments ──────────────────────────────────────────────────────────
export const feeApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<FeeAssignment[]>(`/fee-assignments/${q}`);
  },
  get: (id: number) => apiFetch<FeeAssignment>(`/fee-assignments/${id}/`),
  create: (data: Omit<FeeAssignment, "id" | "status">) =>
    apiFetch<FeeAssignment>("/fee-assignments/", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: number, data: Partial<FeeAssignment>) =>
    apiFetch<FeeAssignment>(`/fee-assignments/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  remove: (id: number) => apiFetch<void>(`/fee-assignments/${id}/`, { method: "DELETE" }),
};

// ─── Payments ─────────────────────────────────────────────────────────────────
export const paymentApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<Payment[]>(`/payments/${q}`);
  },
  create: (data: Omit<Payment, "id" | "collected_by">) =>
    apiFetch<Payment>("/payments/", { method: "POST", body: JSON.stringify(data) }),
};

export const auditApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<AuditEvent[]>(`/audit-events/${q}`);
  },
};

export const approvalRequestApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<ApprovalRequest[]>(`/approval-requests/${q}`);
  },
  create: (data: Omit<ApprovalRequest, "id" | "status" | "requested_by" | "requested_by_name" | "reviewed_by" | "reviewed_by_name" | "decided_at" | "decision_note">) =>
    apiFetch<ApprovalRequest>("/approval-requests/", { method: "POST", body: JSON.stringify(data) }),
  approve: (id: number, decision_note = "") =>
    apiFetch<ApprovalRequest>(`/approval-requests/${id}/approve/`, {
      method: "POST",
      body: JSON.stringify({ decision_note }),
    }),
  reject: (id: number, decision_note = "") =>
    apiFetch<ApprovalRequest>(`/approval-requests/${id}/reject/`, {
      method: "POST",
      body: JSON.stringify({ decision_note }),
    }),
};

export const announcementApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<Announcement[]>(`/announcements/${q}`);
  },
  create: (data: Pick<Announcement, "title" | "message" | "audience"> & { is_active?: boolean }) =>
    apiFetch<Announcement>("/announcements/", { method: "POST", body: JSON.stringify(data) }),
};

export const supportTicketApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? "?" + new URLSearchParams(params).toString() : "";
    return apiFetch<SupportTicket[]>(`/support-tickets/${q}`);
  },
  create: (data: {
    campus?: number | null;
    subject: string;
    message: string;
    category: string;
    priority: SupportTicketPriority;
  }) => apiFetch<SupportTicket>("/support-tickets/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<Pick<SupportTicket, "status" | "response_note" | "subject" | "message" | "category" | "priority">>) =>
    apiFetch<SupportTicket>(`/support-tickets/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
};

export const reportApi = {
  summary: () => apiFetch<DashboardSummary>("/reports/summary/"),
};

// ─── Health ───────────────────────────────────────────────────────────────────
export const healthApi = {
  check: () => apiFetch<{ status: string; service: string }>("/health/"),
};

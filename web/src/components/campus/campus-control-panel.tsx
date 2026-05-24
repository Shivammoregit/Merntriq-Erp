"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Building2,
  Camera,
  CheckCircle2,
  Clock3,
  Cpu,
  Fingerprint,
  IdCard,
  PencilLine,
  Plus,
  RefreshCcw,
  ShieldCheck,
  Trash2,
  Users,
  XCircle,
} from "lucide-react";

import {
  ApiError,
  approvalRequestApi,
  attendanceDeviceApi,
  campusApi,
  campusMembershipApi,
  staffAttendanceApi,
  userApi,
  type ApprovalRequest,
  type AttendanceCaptureMethod,
  type AttendanceDevice,
  type Campus,
  type CampusMembership,
  type CampusMemberRole,
  type ERPUser,
  type StaffAttendanceRecord,
  type StaffAttendanceStatus,
} from "@/lib/api";
import { Badge, statusBadge } from "@/components/ui/badge";
import {
  HardwareDeviceConfiguration,
  type AttendanceDeviceConfigurationPayload,
} from "@/components/attendance/hardware-device-configuration";
import { Modal } from "@/components/ui/modal";
import { Spinner } from "@/components/ui/spinner";

type ControlView = "members" | "devices" | "staff" | "approvals";

const inputCls =
  "w-full rounded-lg border border-line/80 bg-white px-3.5 py-2.5 text-sm text-ink outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20";

const views: {
  id: ControlView;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
}[] = [
  { id: "members", label: "Campus Admins", icon: ShieldCheck },
  { id: "devices", label: "Hardware Devices", icon: Cpu },
  { id: "staff", label: "Staff Attendance", icon: Clock3 },
  { id: "approvals", label: "Approvals", icon: CheckCircle2 },
];

const captureLabels: Record<AttendanceCaptureMethod, string> = {
  manual: "Manual",
  face_recognition: "Face Recognition",
  fingerprint: "Fingerprint",
  card_scan: "Card Scan",
};

const methodIcons: Record<AttendanceCaptureMethod, React.ComponentType<{ size?: number; className?: string }>> = {
  manual: Users,
  face_recognition: Camera,
  fingerprint: Fingerprint,
  card_scan: IdCard,
};

function asArray<T>(value: T[] | { results?: T[] }): T[] {
  return Array.isArray(value) ? value : value.results ?? [];
}

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

function ErrorNote({ message }: { message: string }) {
  if (!message) return null;
  return <p className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700">{message}</p>;
}

function Metric({
  label,
  value,
  note,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  note: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
}) {
  return (
    <div className="surface p-5 shadow-soft">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">{label}</p>
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-ink text-white">
          <Icon size={18} />
        </div>
      </div>
      <p className="display-font mt-3 text-3xl font-semibold text-ink">{value}</p>
      <p className="mt-1 text-xs text-muted">{note}</p>
    </div>
  );
}

function FormActions({
  busy,
  label,
  onCancel,
}: {
  busy: boolean;
  label: string;
  onCancel: () => void;
}) {
  return (
    <div className="flex justify-end gap-3 border-t border-line/60 pt-4">
      <button type="button" onClick={onCancel} className="rounded-lg border border-line/70 px-4 py-2 text-sm font-medium text-ink hover:bg-slate-50">
        Cancel
      </button>
      <button type="submit" disabled={busy} className="flex items-center gap-2 rounded-lg bg-ink px-5 py-2 text-sm font-semibold text-white shadow transition hover:-translate-y-0.5 disabled:opacity-60">
        {busy && <Spinner size={14} />}
        {busy ? "Saving..." : label}
      </button>
    </div>
  );
}

function MembershipForm({
  campuses,
  users,
  onSave,
  onCancel,
}: {
  campuses: Campus[];
  users: ERPUser[];
  onSave: (data: Omit<CampusMembership, "id" | "campus_name" | "user_name" | "user_role">) => Promise<void>;
  onCancel: () => void;
}) {
  const [form, setForm] = useState({
    campus: String(campuses[0]?.id ?? ""),
    user: String(users[0]?.id ?? ""),
    role: "it_admin" as CampusMemberRole,
    is_primary: true,
    can_manage_users: true,
    can_configure_attendance: true,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await onSave({
        campus: Number(form.campus),
        user: Number(form.user),
        role: form.role,
        is_primary: form.is_primary,
        can_manage_users: form.can_manage_users,
        can_configure_attendance: form.can_configure_attendance,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Membership save failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <ErrorNote message={error} />
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm font-medium text-ink">
          Campus
          <select className={`mt-1 ${inputCls}`} value={form.campus} onChange={(e) => setForm((f) => ({ ...f, campus: e.target.value }))} required>
            {campuses.map((campus) => <option key={campus.id} value={campus.id}>{campus.name}</option>)}
          </select>
        </label>
        <label className="block text-sm font-medium text-ink">
          User
          <select className={`mt-1 ${inputCls}`} value={form.user} onChange={(e) => setForm((f) => ({ ...f, user: e.target.value }))} required>
            {users.map((user) => <option key={user.id} value={user.id}>{user.full_name || user.username} ({user.role.replace("_", " ")})</option>)}
          </select>
        </label>
        <label className="block text-sm font-medium text-ink">
          Campus role
          <select className={`mt-1 ${inputCls}`} value={form.role} onChange={(e) => setForm((f) => ({ ...f, role: e.target.value as CampusMemberRole }))}>
            <option value="it_admin">IT Admin</option>
            <option value="academic_admin">Academic Admin</option>
            <option value="finance_admin">Finance Admin</option>
            <option value="hr_admin">HR Admin</option>
            <option value="teacher">Teacher</option>
            <option value="support">Support</option>
          </select>
        </label>
        <div className="grid content-end gap-2">
          {[
            ["is_primary", "Primary campus"],
            ["can_manage_users", "Can manage users"],
            ["can_configure_attendance", "Can configure attendance"],
          ].map(([key, label]) => (
            <label key={key} className="flex items-center gap-2 text-sm text-ink">
              <input
                type="checkbox"
                checked={Boolean(form[key as keyof typeof form])}
                onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.checked }))}
              />
              {label}
            </label>
          ))}
        </div>
      </div>
      <FormActions busy={busy} label="Save membership" onCancel={onCancel} />
    </form>
  );
}

function StaffAttendanceForm({
  campuses,
  users,
  devices,
  onSave,
  onCancel,
}: {
  campuses: Campus[];
  users: ERPUser[];
  devices: AttendanceDevice[];
  onSave: (data: Omit<StaffAttendanceRecord, "id" | "marked_by" | "marked_by_name" | "campus_name" | "staff_name" | "staff_role" | "device_name">) => Promise<void>;
  onCancel: () => void;
}) {
  const staffUsers = users.filter((user) => user.role !== "student");
  const [form, setForm] = useState({
    campus: String(campuses[0]?.id ?? ""),
    staff_user: String(staffUsers[0]?.id ?? ""),
    date: todayISO(),
    clock_in: "08:00",
    clock_out: "",
    status: "present" as StaffAttendanceStatus,
    capture_method: "manual" as AttendanceCaptureMethod,
    device: "",
    source_reference: "",
    confidence_score: "",
    notes: "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const campusDevices = devices.filter((device) => String(device.campus) === form.campus && device.is_enabled_for_staff);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await onSave({
        campus: Number(form.campus),
        staff_user: Number(form.staff_user),
        date: form.date,
        clock_in: form.clock_in || null,
        clock_out: form.clock_out || null,
        status: form.status,
        capture_method: form.capture_method,
        device: form.device ? Number(form.device) : null,
        source_reference: form.source_reference,
        confidence_score: form.confidence_score || null,
        notes: form.notes,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Staff attendance save failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <ErrorNote message={error} />
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm font-medium text-ink">
          Campus
          <select className={`mt-1 ${inputCls}`} value={form.campus} onChange={(e) => setForm((f) => ({ ...f, campus: e.target.value, device: "" }))}>
            {campuses.map((campus) => <option key={campus.id} value={campus.id}>{campus.name}</option>)}
          </select>
        </label>
        <label className="block text-sm font-medium text-ink">
          Staff user
          <select className={`mt-1 ${inputCls}`} value={form.staff_user} onChange={(e) => setForm((f) => ({ ...f, staff_user: e.target.value }))}>
            {staffUsers.map((user) => <option key={user.id} value={user.id}>{user.full_name || user.username} ({user.role.replace("_", " ")})</option>)}
          </select>
        </label>
        <label className="block text-sm font-medium text-ink">
          Date
          <input type="date" className={`mt-1 ${inputCls}`} value={form.date} onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))} required />
        </label>
        <label className="block text-sm font-medium text-ink">
          Status
          <select className={`mt-1 ${inputCls}`} value={form.status} onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as StaffAttendanceStatus }))}>
            <option value="present">Present</option>
            <option value="late">Late</option>
            <option value="half_day">Half Day</option>
            <option value="on_leave">On Leave</option>
            <option value="absent">Absent</option>
          </select>
        </label>
        <label className="block text-sm font-medium text-ink">
          Clock in
          <input type="time" className={`mt-1 ${inputCls}`} value={form.clock_in} onChange={(e) => setForm((f) => ({ ...f, clock_in: e.target.value }))} />
        </label>
        <label className="block text-sm font-medium text-ink">
          Clock out
          <input type="time" className={`mt-1 ${inputCls}`} value={form.clock_out} onChange={(e) => setForm((f) => ({ ...f, clock_out: e.target.value }))} />
        </label>
        <label className="block text-sm font-medium text-ink">
          Capture method
          <select className={`mt-1 ${inputCls}`} value={form.capture_method} onChange={(e) => setForm((f) => ({ ...f, capture_method: e.target.value as AttendanceCaptureMethod }))}>
            <option value="manual">Manual</option>
            <option value="face_recognition">Face Recognition</option>
            <option value="fingerprint">Fingerprint</option>
            <option value="card_scan">Card Scan</option>
          </select>
        </label>
        <label className="block text-sm font-medium text-ink">
          Device
          <select className={`mt-1 ${inputCls}`} value={form.device} onChange={(e) => setForm((f) => ({ ...f, device: e.target.value }))}>
            <option value="">Manual entry</option>
            {campusDevices.map((device) => <option key={device.id} value={device.id}>{device.name}</option>)}
          </select>
        </label>
        <label className="block text-sm font-medium text-ink">
          Source reference
          <input className={`mt-1 ${inputCls}`} value={form.source_reference} onChange={(e) => setForm((f) => ({ ...f, source_reference: e.target.value }))} placeholder="hardware event id" />
        </label>
        <label className="block text-sm font-medium text-ink">
          Confidence
          <input type="number" min="0" max="100" step="0.01" className={`mt-1 ${inputCls}`} value={form.confidence_score} onChange={(e) => setForm((f) => ({ ...f, confidence_score: e.target.value }))} placeholder="98.50" />
        </label>
        <label className="block text-sm font-medium text-ink sm:col-span-2">
          Notes
          <input className={`mt-1 ${inputCls}`} value={form.notes} onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} />
        </label>
      </div>
      <FormActions busy={busy} label="Save attendance" onCancel={onCancel} />
    </form>
  );
}

function ApprovalForm({
  campuses,
  onSave,
  onCancel,
}: {
  campuses: Campus[];
  onSave: (data: Omit<ApprovalRequest, "id" | "status" | "requested_by" | "requested_by_name" | "reviewed_by" | "reviewed_by_name" | "decided_at" | "decision_note">) => Promise<void>;
  onCancel: () => void;
}) {
  const [form, setForm] = useState({
    campus: String(campuses[0]?.id ?? ""),
    title: "",
    entity_type: "Student",
    entity_id: "",
    description: "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await onSave({
        campus: Number(form.campus),
        title: form.title,
        entity_type: form.entity_type,
        entity_id: form.entity_id,
        description: form.description,
        payload: {},
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Approval request save failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <ErrorNote message={error} />
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm font-medium text-ink">
          Campus
          <select className={`mt-1 ${inputCls}`} value={form.campus} onChange={(e) => setForm((f) => ({ ...f, campus: e.target.value }))}>
            {campuses.map((campus) => <option key={campus.id} value={campus.id}>{campus.name}</option>)}
          </select>
        </label>
        <label className="block text-sm font-medium text-ink">
          Entity type
          <select className={`mt-1 ${inputCls}`} value={form.entity_type} onChange={(e) => setForm((f) => ({ ...f, entity_type: e.target.value }))}>
            <option value="Student">Student</option>
            <option value="StaffAttendanceRecord">Staff Attendance</option>
            <option value="FeeAssignment">Fee Assignment</option>
            <option value="AttendanceDevice">Attendance Device</option>
          </select>
        </label>
        <label className="block text-sm font-medium text-ink sm:col-span-2">
          Title
          <input className={`mt-1 ${inputCls}`} value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} required />
        </label>
        <label className="block text-sm font-medium text-ink">
          Entity ID
          <input className={`mt-1 ${inputCls}`} value={form.entity_id} onChange={(e) => setForm((f) => ({ ...f, entity_id: e.target.value }))} placeholder="ADM-2026-001" />
        </label>
        <label className="block text-sm font-medium text-ink sm:col-span-2">
          Description
          <textarea className={`mt-1 min-h-24 ${inputCls}`} value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
        </label>
      </div>
      <FormActions busy={busy} label="Create request" onCancel={onCancel} />
    </form>
  );
}

export function CampusControlPanel() {
  const [activeView, setActiveView] = useState<ControlView>("members");
  const [campuses, setCampuses] = useState<Campus[]>([]);
  const [users, setUsers] = useState<ERPUser[]>([]);
  const [memberships, setMemberships] = useState<CampusMembership[]>([]);
  const [devices, setDevices] = useState<AttendanceDevice[]>([]);
  const [staffAttendance, setStaffAttendance] = useState<StaffAttendanceRecord[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modal, setModal] = useState<ControlView | null>(null);
  const [deviceToEdit, setDeviceToEdit] = useState<AttendanceDevice | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [campusRes, userRes, membershipRes, deviceRes, staffRes, approvalRes] = await Promise.all([
        campusApi.list(),
        userApi.list(),
        campusMembershipApi.list(),
        attendanceDeviceApi.list(),
        staffAttendanceApi.list(),
        approvalRequestApi.list(),
      ]);
      setCampuses(asArray(campusRes));
      setUsers(asArray(userRes));
      setMemberships(asArray(membershipRes));
      setDevices(asArray(deviceRes));
      setStaffAttendance(asArray(staffRes));
      setApprovals(asArray(approvalRes));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load campus control data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const staffUsers = useMemo(() => users.filter((user) => user.role === "teacher" || user.role === "admin"), [users]);
  const activeDevices = devices.filter((device) => device.status === "active").length;
  const pendingApprovals = approvals.filter((approval) => approval.status === "pending").length;

  async function refreshAfterSave() {
    setModal(null);
    setDeviceToEdit(null);
    await load();
  }

  async function removeMembership(id: number) {
    if (!confirm("Remove this campus membership?")) return;
    await campusMembershipApi.remove(id);
    await load();
  }

  async function removeDevice(id: number) {
    if (!confirm("Remove this attendance device?")) return;
    await attendanceDeviceApi.remove(id);
    await load();
  }

  async function decideApproval(id: number, action: "approve" | "reject") {
    if (action === "approve") await approvalRequestApi.approve(id);
    else await approvalRequestApi.reject(id);
    await load();
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24">
        <Spinner size={32} className="text-blue-600" />
        <p className="text-sm text-muted">Loading campus control...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="surface p-6 shadow-soft">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <span className="section-kicker">
              <ShieldCheck size={14} />
              Campus control
            </span>
            <h1 className="display-font mt-3 text-3xl font-semibold text-ink">Institution operations and access</h1>
            <p className="mt-2 max-w-3xl text-sm leading-7 text-muted">
              Manage campus-specific IT admins, attendance hardware, teacher attendance records, and approval requests from one operational surface.
            </p>
          </div>
          <button
            type="button"
            onClick={load}
            className="flex items-center gap-2 rounded-lg border border-line/70 bg-white px-4 py-2 text-sm font-medium text-muted hover:bg-slate-50 hover:text-ink"
          >
            <RefreshCcw size={14} />
            Refresh
          </button>
        </div>
      </section>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
          <button className="ml-2 underline" onClick={load}>Retry</button>
        </div>
      )}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Campuses" value={campuses.length} note="campus-scoped ERP records" icon={Building2} />
        <Metric label="Campus admins" value={memberships.filter((item) => item.can_manage_users).length} note={`${memberships.length} total memberships`} icon={ShieldCheck} />
        <Metric label="Active devices" value={activeDevices} note={`${devices.length} hardware profiles`} icon={Cpu} />
        <Metric label="Pending approvals" value={pendingApprovals} note={`${approvals.length} requests in queue`} icon={CheckCircle2} />
      </section>

      <div className="flex flex-wrap items-center gap-2">
        {views.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => setActiveView(id)}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition ${
              activeView === id ? "bg-ink text-white shadow" : "border border-line/70 bg-white text-muted hover:bg-slate-50 hover:text-ink"
            }`}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
        <button
          type="button"
          onClick={() => {
            if (activeView === "devices") setDeviceToEdit(null);
            setModal(activeView);
          }}
          className="ml-auto flex items-center gap-2 rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-white shadow transition hover:-translate-y-0.5"
        >
          <Plus size={14} />
          New
        </button>
      </div>

      {activeView === "members" && (
        <div className="surface overflow-hidden shadow-soft">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line/60 bg-slate-50">
                  {["User", "System role", "Campus", "Campus role", "Capabilities", "Actions"].map((head) => (
                    <th key={head} className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted">{head}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {memberships.map((membership) => (
                  <tr key={membership.id} className="border-b border-line/40 hover:bg-slate-50/60">
                    <td className="px-5 py-3.5 font-semibold text-ink">{membership.user_name}</td>
                    <td className="px-5 py-3.5 text-muted">{membership.user_role?.replace("_", " ")}</td>
                    <td className="px-5 py-3.5 text-muted">{membership.campus_name}</td>
                    <td className="px-5 py-3.5"><Badge variant="info">{membership.role.replace("_", " ")}</Badge></td>
                    <td className="px-5 py-3.5">
                      <div className="flex flex-wrap gap-2">
                        {membership.is_primary && <Badge variant="success">primary</Badge>}
                        {membership.can_manage_users && <Badge variant="purple">users</Badge>}
                        {membership.can_configure_attendance && <Badge variant="warning">attendance</Badge>}
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <button type="button" onClick={() => removeMembership(membership.id)} className="inline-flex items-center gap-1 rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-medium text-rose-600 hover:bg-rose-50">
                        <Trash2 size={12} />
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
                {memberships.length === 0 && (
                  <tr><td colSpan={6} className="px-5 py-12 text-center text-muted">No campus memberships configured.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeView === "devices" && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {devices.map((device) => {
            const Icon = methodIcons[device.device_type];
            const serverTarget = device.use_domain_name ? device.domain_name : device.server_ip;
            return (
              <article key={device.id} className="surface p-5 shadow-soft">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
                      <Icon size={18} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-ink">{device.name}</h3>
                      <p className="mt-1 font-mono text-xs text-muted">{device.device_code}</p>
                    </div>
                  </div>
                  <Badge variant={statusBadge(device.status)}>{device.status}</Badge>
                </div>
                <div className="mt-4 grid gap-2 text-sm text-muted">
                  <p>{device.campus_name}</p>
                  <p>{captureLabels[device.device_type]} - {device.location || "No location"}</p>
                  <p>Students: {device.is_enabled_for_students ? "enabled" : "disabled"} / Staff: {device.is_enabled_for_staff ? "enabled" : "disabled"}</p>
                  <div className="rounded-lg border border-line/70 bg-slate-50 p-3 text-xs leading-5 text-slate-600">
                    <p><span className="font-semibold text-ink">Server:</span> {serverTarget || "not configured"}:{device.server_port || "-"}</p>
                    <p><span className="font-semibold text-ink">Heartbeat:</span> {device.heartbeat_seconds || "-"} sec / Approval: {device.server_approval_required ? "Yes" : "No"}</p>
                    <p><span className="font-semibold text-ink">Comm:</span> ID {device.device_numeric_id || "-"}, Port {device.local_port || "-"}, Baud {device.baud_rate || "-"}</p>
                    <p><span className="font-semibold text-ink">RS485:</span> {device.rs485_function || "software"}</p>
                  </div>
                  <p>Last seen: {device.last_seen_at ? new Date(device.last_seen_at).toLocaleString("en-IN") : "not reported"}</p>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setDeviceToEdit(device);
                      setModal("devices");
                    }}
                    className="inline-flex items-center gap-1 rounded-lg border border-line/70 px-3 py-1.5 text-xs font-medium text-ink hover:bg-slate-50"
                  >
                    <PencilLine size={12} />
                    Configure
                  </button>
                  <button type="button" onClick={() => removeDevice(device.id)} className="inline-flex items-center gap-1 rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-medium text-rose-600 hover:bg-rose-50">
                    <Trash2 size={12} />
                    Remove
                  </button>
                </div>
              </article>
            );
          })}
          {devices.length === 0 && (
            <div className="surface p-8 text-center text-sm text-muted shadow-soft md:col-span-2 xl:col-span-3">No attendance hardware profiles configured.</div>
          )}
        </div>
      )}

      {activeView === "staff" && (
        <div className="surface overflow-hidden shadow-soft">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line/60 bg-slate-50">
                  {["Date", "Staff", "Campus", "Status", "Time", "Source", "Device"].map((head) => (
                    <th key={head} className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted">{head}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {staffAttendance.map((record) => (
                  <tr key={record.id} className="border-b border-line/40 hover:bg-slate-50/60">
                    <td className="px-5 py-3.5 text-ink">{record.date}</td>
                    <td className="px-5 py-3.5 font-semibold text-ink">{record.staff_name}</td>
                    <td className="px-5 py-3.5 text-muted">{record.campus_name}</td>
                    <td className="px-5 py-3.5"><Badge variant={statusBadge(record.status)}>{record.status.replace("_", " ")}</Badge></td>
                    <td className="px-5 py-3.5 text-muted">{record.clock_in || "-"} to {record.clock_out || "-"}</td>
                    <td className="px-5 py-3.5 text-muted">{captureLabels[record.capture_method]}</td>
                    <td className="px-5 py-3.5 text-muted">{record.device_name || "Manual"}</td>
                  </tr>
                ))}
                {staffAttendance.length === 0 && (
                  <tr><td colSpan={7} className="px-5 py-12 text-center text-muted">No staff attendance records yet.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeView === "approvals" && (
        <div className="grid gap-4 lg:grid-cols-2">
          {approvals.map((approval) => (
            <article key={approval.id} className="surface p-5 shadow-soft">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">{approval.campus_name}</p>
                  <h3 className="mt-1 font-semibold text-ink">{approval.title}</h3>
                  <p className="mt-1 text-sm text-muted">{approval.entity_type}{approval.entity_id ? ` - ${approval.entity_id}` : ""}</p>
                </div>
                <Badge variant={statusBadge(approval.status)}>{approval.status}</Badge>
              </div>
              {approval.description && <p className="mt-3 text-sm leading-6 text-muted">{approval.description}</p>}
              <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-muted">
                <span>Requested by {approval.requested_by_name || "System"}</span>
                <span>{approval.created_at ? new Date(approval.created_at).toLocaleString("en-IN") : ""}</span>
              </div>
              {approval.status === "pending" && (
                <div className="mt-4 flex gap-2">
                  <button type="button" onClick={() => decideApproval(approval.id, "approve")} className="inline-flex items-center gap-1 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 hover:bg-emerald-100">
                    <CheckCircle2 size={12} />
                    Approve
                  </button>
                  <button type="button" onClick={() => decideApproval(approval.id, "reject")} className="inline-flex items-center gap-1 rounded-lg border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-medium text-rose-700 hover:bg-rose-100">
                    <XCircle size={12} />
                    Reject
                  </button>
                </div>
              )}
            </article>
          ))}
          {approvals.length === 0 && (
            <div className="surface p-8 text-center text-sm text-muted shadow-soft lg:col-span-2">No approval requests yet.</div>
          )}
        </div>
      )}

      <Modal open={modal === "members"} onClose={() => setModal(null)} title="Add Campus Membership" size="lg">
        <MembershipForm campuses={campuses} users={users} onSave={async (data) => {
          await campusMembershipApi.create(data);
          await refreshAfterSave();
        }} onCancel={() => setModal(null)} />
      </Modal>

      <Modal
        open={modal === "devices"}
        onClose={() => {
          setDeviceToEdit(null);
          setModal(null);
        }}
        title={deviceToEdit ? "Configure Attendance Device" : "Add Attendance Device"}
        size="xl"
      >
        <HardwareDeviceConfiguration campuses={campuses} device={deviceToEdit} onSave={async (data: AttendanceDeviceConfigurationPayload) => {
          if (deviceToEdit) await attendanceDeviceApi.update(deviceToEdit.id, data);
          else await attendanceDeviceApi.create(data);
          await refreshAfterSave();
        }} onCancel={() => {
          setDeviceToEdit(null);
          setModal(null);
        }} />
      </Modal>

      <Modal open={modal === "staff"} onClose={() => setModal(null)} title="Record Staff Attendance" size="lg">
        <StaffAttendanceForm campuses={campuses} users={staffUsers} devices={devices} onSave={async (data) => {
          await staffAttendanceApi.create(data);
          await refreshAfterSave();
        }} onCancel={() => setModal(null)} />
      </Modal>

      <Modal open={modal === "approvals"} onClose={() => setModal(null)} title="Create Approval Request" size="lg">
        <ApprovalForm campuses={campuses} onSave={async (data) => {
          await approvalRequestApi.create(data);
          await refreshAfterSave();
        }} onCancel={() => setModal(null)} />
      </Modal>
    </div>
  );
}

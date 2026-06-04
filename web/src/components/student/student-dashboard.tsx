"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Award,
  BadgeCheck,
  Bell,
  BookOpen,
  CalendarDays,
  ChevronDown,
  ClipboardCheck,
  ExternalLink,
  FileText,
  GraduationCap,
  MapPin,
  Printer,
  RefreshCcw,
  ReceiptText,
  X,
  UserRound,
} from "lucide-react";

import {
  admitCardApi,
  announcementApi,
  assignedWorkApi,
  attendanceApi,
  feeApi,
  learningResourceApi,
  paymentApi,
  paymentTransactionApi,
  resultRecordApi,
  studentApi,
  ApiError,
  type AdmitCard,
  type Announcement,
  type AssignedWork,
  type AttendanceRecord,
  type FeeAssignment,
  type LearningResource,
  type Payment,
  type ResultRecord,
  type Student,
} from "@/lib/api";
import { Badge, statusBadge, statusLabel } from "@/components/ui/badge";
import { WorkspacePlaceholder } from "@/components/ui/workspace-placeholder";

type StudentView = "overview" | "profile" | "lms" | "fees" | "attendance" | "results" | "work" | "resources" | "admit" | "parent";

const studentViews: {
  id: StudentView;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
}[] = [
  { id: "overview", label: "Dashboard", icon: GraduationCap },
  { id: "profile", label: "Student Information", icon: UserRound },
  { id: "lms", label: "Select Course", icon: BookOpen },
  { id: "fees", label: "Online Payment", icon: ReceiptText },
  { id: "attendance", label: "Attendance Details", icon: ClipboardCheck },
  { id: "results", label: "Result Details", icon: Award },
  { id: "work", label: "Homework", icon: FileText },
  { id: "resources", label: "Course Registered", icon: BadgeCheck },
  { id: "admit", label: "Admit Card", icon: BadgeCheck },
  { id: "parent", label: "Parent View", icon: UserRound },
];

function asArray<T>(value: T[] | { results?: T[] }): T[] {
  return Array.isArray(value) ? value : value.results ?? [];
}

function formatDate(value?: string) {
  if (!value) return "";
  return new Date(value).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function amountValue(value?: string | number | null) {
  return Number(value ?? 0) || 0;
}

function formatMoney(value?: string | number | null) {
  return amountValue(value).toLocaleString("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  });
}

function formatResourceType(value: string) {
  return value.replace("_", " ");
}

function scorePercent(result: ResultRecord) {
  if (result.percentage) return Number(result.percentage);
  const max = Number(result.max_score || 0);
  return max ? Math.round((Number(result.score) / max) * 100) : 0;
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="surface py-14 text-center shadow-soft">
      <p className="text-sm text-muted">{label}</p>
    </div>
  );
}

function profileValue(value?: string | null) {
  return value?.trim() || "Not added";
}

function pageTitleFor(view: StudentView) {
  if (view === "overview") return "Student Dashboard";
  if (view === "profile") return "Student Complete Detail";
  if (view === "lms") return "Select Course";
  if (view === "fees") return "Online Payment";
  if (view === "attendance") return "Attendance Details";
  if (view === "results") return "Result Details";
  if (view === "work") return "Homework & Assignment";
  if (view === "resources") return "Course Registered";
  if (view === "admit") return "Admit Card";
  if (view === "parent") return "Parent View";
  return "Student Dashboard";
}

function InfoRow({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div className="grid grid-cols-[minmax(8rem,0.55fr)_minmax(0,1fr)] border-b border-line/70 py-2 text-sm">
      <span className="font-medium text-ink">{label}</span>
      <span className="min-w-0 break-words text-muted">{profileValue(String(value ?? ""))}</span>
    </div>
  );
}

function PanelHeader({
  title,
  icon: Icon = RefreshCcw,
}: {
  title: string;
  icon?: React.ComponentType<{ size?: number; className?: string }>;
}) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-line/70 px-5 py-4">
      <h2 className="text-lg font-semibold text-ink">{title}</h2>
      <Icon size={17} className="text-ink" />
    </div>
  );
}

function DateNotice({ day, month, title }: { day: string; month: string; title: string }) {
  return (
    <div className="flex items-center gap-3 border-b border-line/70 px-2 py-3">
      <div className="flex h-16 w-16 shrink-0 flex-col items-center justify-center rounded-lg bg-cyan-600 text-white">
        <span className="text-xs font-semibold">{month}</span>
        <span className="text-3xl font-bold leading-none">{day}</span>
      </div>
      <p className="text-sm font-semibold leading-6 text-black">{title}</p>
    </div>
  );
}

function StudentHomePage({
  attendancePct,
  presentCount,
  attendanceTotal,
  openWork,
  visibleWork,
  visibleAdmitCards,
  notices,
  setActiveView,
}: {
  attendancePct: number;
  presentCount: number;
  attendanceTotal: number;
  openWork: AssignedWork[];
  visibleWork: AssignedWork[];
  visibleAdmitCards: AdmitCard[];
  notices: Announcement[];
  setActiveView: (view: StudentView) => void;
}) {
  return (
    <div className="space-y-5">
      <section className="grid gap-4 xl:grid-cols-3">
        <button type="button" onClick={() => setActiveView("attendance")} className="surface flex items-center justify-center gap-4 p-6 text-left shadow-soft hover:border-accent">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent text-white">
            <span className="text-2xl font-bold">%</span>
          </div>
          <div>
            <p className="text-4xl font-semibold text-ink">{attendancePct} %</p>
            <p className="text-sm text-muted">Attendance</p>
          </div>
        </button>
        <button type="button" onClick={() => setActiveView("work")} className="surface flex items-center justify-center gap-4 p-6 text-left shadow-soft hover:border-accent">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-rose-600 text-white">
            <ClipboardCheck size={24} />
          </div>
          <div>
            <p className="text-4xl font-semibold text-ink">{openWork.length}</p>
            <p className="text-sm text-muted">Assignments</p>
          </div>
        </button>
        <button type="button" onClick={() => setActiveView("admit")} className="surface flex items-center justify-center gap-4 p-6 text-left shadow-soft hover:border-accent">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-600 text-white">
            <Bell size={24} />
          </div>
          <div>
            <p className="text-4xl font-semibold text-ink">{visibleAdmitCards.length}</p>
            <p className="text-sm text-muted">Announcements</p>
          </div>
        </button>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr_0.8fr_2fr]">
        <div className="surface overflow-hidden shadow-soft">
          <PanelHeader title="Attendance" />
          <div className="compact-table p-5">
            <table className="min-w-full text-sm">
              <thead>
                <tr>{["Subject", "Lectures", "%"].map((head) => <th key={head} className="px-4 py-3 text-center">{head}</th>)}</tr>
              </thead>
              <tbody>
                <tr>
                  <td className="px-4 py-4 text-center text-muted">All Subjects</td>
                  <td className="px-4 py-4 text-center text-muted">{presentCount} / {attendanceTotal}</td>
                  <td className="px-4 py-4 text-center font-semibold text-ink">{attendancePct}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="surface overflow-hidden shadow-soft">
          <PanelHeader title="Quick Access" />
          <div className="grid gap-2 p-4">
            {[
              ["Student Complete Detail", "profile"],
              ["Online Payment", "fees"],
              ["Select Course", "lms"],
              ["Result Details", "results"],
            ].map(([label, view]) => (
              <button key={label} type="button" onClick={() => setActiveView(view as StudentView)} className="rounded-md border border-line/70 bg-white px-3 py-2 text-left text-sm font-medium text-accent hover:border-accent hover:bg-accent-soft hover:text-accent-strong">
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="surface overflow-hidden shadow-soft">
          <PanelHeader title="Tasks" />
          <div className="divide-y divide-line/60">
            {visibleWork.slice(0, 3).map((item) => (
              <button key={item.id} type="button" onClick={() => setActiveView("work")} className="block w-full px-4 py-3 text-left">
                <p className="text-sm font-semibold text-ink">{item.title}</p>
                <p className="mt-1 text-xs text-muted">{item.subject} - Due {formatDate(item.due_date)}</p>
              </button>
            ))}
            {!visibleWork.length && <p className="px-4 py-10 text-center text-sm text-muted">No task available.</p>}
          </div>
        </div>

        <div className="surface overflow-hidden shadow-soft">
          <PanelHeader title="Active Notice/News" icon={Bell} />
          <div className="px-4">
            {notices.slice(0, 3).map((notice) => {
              const date = notice.publish_on ? new Date(notice.publish_on) : new Date();
              return (
                <DateNotice
                  key={notice.id}
                  day={date.toLocaleDateString("en-IN", { day: "2-digit" })}
                  month={date.toLocaleDateString("en-IN", { month: "short" })}
                  title={notice.title}
                />
              );
            })}
            {!notices.length && <p className="px-2 py-10 text-center text-sm text-muted">No notices published yet.</p>}
          </div>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.8fr_2.1fr_2.1fr]">
        <div className="surface overflow-hidden shadow-soft">
          <PanelHeader title="Today's Time Table" />
          <div className="compact-table p-5">
            <table className="min-w-full text-sm">
              <thead><tr>{["Slot", "CCode"].map((head) => <th key={head} className="px-4 py-3 text-center">{head}</th>)}</tr></thead>
              <tbody><tr><td className="px-4 py-10 text-center text-muted" colSpan={2}>No lecture scheduled.</td></tr></tbody>
            </table>
          </div>
        </div>

        <div className="surface overflow-hidden shadow-soft">
          <PanelHeader title="Class Time Table" />
          <div className="overflow-x-auto p-5">
            <table className="text-sm">
              <thead><tr>{["Time/Day", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"].map((head) => <th key={head} className="px-4 py-3 text-center">{head}</th>)}</tr></thead>
              <tbody><tr><td className="px-4 py-10 text-center text-muted" colSpan={7}>Time table will be published by school admin.</td></tr></tbody>
            </table>
          </div>
        </div>

        <div className="surface overflow-hidden shadow-soft">
          <PanelHeader title="Exam Time Table" />
          <div className="overflow-x-auto p-5">
            <table className="text-sm">
              <thead><tr>{["EXAMDATE", "SLOTNAME", "CCODE", "COURSENAME", "SEMESTERNAME", "REGULAR_BACKLOG"].map((head) => <th key={head} className="px-4 py-3 text-center">{head}</th>)}</tr></thead>
              <tbody><tr><td className="px-4 py-10 text-center text-muted" colSpan={6}>No exam schedule published.</td></tr></tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}

function StudentCompleteDetailPage({ student }: { student: Student }) {
  const detailRows = [
    ["RRN No.", student.admission_number],
    ["Student Name", student.full_name],
    ["User Login Status", "Enabled"],
    ["Admission Status", "Admitted"],
    ["Current Student/Admission Status", "ADMISSION"],
    ["User Last Login Details", "23-May-2026 07:38AM"],
  ];
  const schoolRows = [
    ["Admission Batch", "2024-25"],
    ["School", student.campus_name || "MentriQ School"],
    ["Degree/Branch", student.section_label || "Class / Section"],
    ["Semester", "IV"],
    ["Scheme", "School ERP Academic Session 2025-2026"],
  ];
  const sidebar = [
    "Student Information",
    "Personal Details",
    "Address Details",
    "Qualification Details",
    "Fees Details",
    "Course Registered",
    "Attendance Details",
    "Result Details",
    "Revaluation Result Details",
    "Internal Marks",
    "Mentor-Mentee",
  ];

  return (
    <div className="grid gap-5 xl:grid-cols-[18rem_minmax(0,1fr)]">
      <aside className="surface h-fit p-3 shadow-soft">
        {sidebar.map((item, index) => (
          <div key={item} className={`flex items-center gap-2 rounded-md px-3 py-3 text-sm ${index === 0 ? "bg-accent-soft font-semibold text-accent-strong" : "text-slate-700 hover:bg-slate-50"}`}>
            <FileText size={15} />
            {item}
          </div>
        ))}
      </aside>

      <section className="surface overflow-hidden p-4 shadow-soft md:p-6">
        <div className="grid gap-6 rounded-md border border-line/60 bg-white p-4 xl:grid-cols-[1fr_1fr_14rem]">
          <div>{detailRows.map(([label, value]) => <InfoRow key={label} label={label} value={value} />)}</div>
          <div>{schoolRows.map(([label, value]) => <InfoRow key={label} label={label} value={value} />)}</div>
          <div className="flex flex-col items-center justify-start border-l border-line/70 px-4">
            <div className="flex h-28 w-28 items-center justify-center overflow-hidden rounded-md bg-slate-100 text-4xl font-bold text-muted">
              {student.full_name[0]?.toUpperCase()}
            </div>
            <div className="mt-2 rounded-sm bg-slate-200 px-3 py-1 text-center text-xs font-bold text-muted">SIGNATURE<br />NOT AVAILABLE</div>
          </div>
        </div>

        <label className="mt-5 block max-w-md">
          <span className="text-sm font-medium text-ink"><span className="text-red-600">*</span> Session</span>
          <span className="relative mt-1.5 block">
            <select className="w-full rounded-md border border-blue-200 bg-white px-4 py-3 text-sm text-muted outline-none">
              <option>Jan-June 2025-2026</option>
            </select>
            <ChevronDown size={16} className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-muted" />
          </span>
        </label>

        <div className="mt-5">
          <h2 className="mastersoft-section-title">Student Information</h2>
          <div className="mt-3 grid gap-8 xl:grid-cols-2">
            <div>
              <InfoRow label="Student Name" value={student.full_name} />
              <InfoRow label="Gender" value="Not added" />
              <InfoRow label="Father's Name" value={student.father_name} />
              <InfoRow label="Mother's Name" value={student.mother_name} />
              <InfoRow label="RRNO" value={student.admission_number} />
            </div>
            <div>
              <InfoRow label="School/Institute Name" value={student.campus_name || "MentriQ School"} />
              <InfoRow label="Degree" value={student.section_label || "Class / Section"} />
              <InfoRow label="Branch" value={student.section_label || "General"} />
              <InfoRow label="Semester" value="IV" />
              <InfoRow label="Scheme" value="School ERP Academic Session 2025-2026" />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function LmsSelectCoursePage({ student }: { student: Student }) {
  return (
    <div className="grid gap-5 xl:grid-cols-[18rem_minmax(0,1fr)]">
      <aside className="surface min-h-[34rem] p-4 shadow-soft">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="font-medium text-ink">Transactions</h2>
          <X size={18} className="text-muted" />
        </div>
        <div className="border-l-4 border-accent px-4 py-3 text-sm font-semibold text-accent">Select Course</div>
      </aside>

      <section className="surface min-h-[34rem] overflow-hidden p-4 shadow-soft md:p-6">
        <h2 className="mb-4 text-xl font-semibold text-ink">Select Course</h2>
        <div className="mb-8 flex max-w-5xl items-center gap-3 rounded-md border border-line/70 bg-white px-3 py-3 text-sm font-semibold text-green-700">
          <span className="flex h-11 w-11 items-center justify-center bg-accent text-white"><Bell size={18} /></span>
          If the session is not showing, check the Exam Type on the session creation page.
        </div>
        <label className="block max-w-2xl">
          <span className="text-sm font-medium text-ink"><span className="text-red-600">*</span> Session</span>
          <select className="mt-2 w-full rounded-md border border-blue-200 bg-white px-4 py-3 text-sm text-ink outline-none">
            <option>Jan-June 2025-2026 - {student.campus_name || "MentriQ School"} ({student.section_label || "Class"})</option>
          </select>
        </label>

        <div className="mt-16 rounded-md border border-line/70 bg-white p-5 shadow-soft">
          <div className="max-w-lg rounded-lg bg-blue-50 p-6 shadow-soft">
            <div className="flex items-start justify-between gap-5">
              <div>
                <p className="text-sm leading-7 text-blue-700">MCA175A - Industrial<br />Training/Internship/Dissertation Project<br />Presentation - [ A ] A</p>
                <p className="mt-2 text-sm"><strong>Type:</strong> Internship</p>
                <p className="mt-2 text-sm"><strong>Year/Semester:</strong> IV</p>
              </div>
              <GraduationCap size={58} className="text-slate-800" />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function StudentQuickTabs({
  activeView,
  setActiveView,
}: {
  activeView: StudentView;
  setActiveView: (view: StudentView) => void;
}) {
  return (
    <nav className="surface student-tabs shadow-soft" aria-label="Student workspace">
      {studentViews.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          type="button"
          onClick={() => setActiveView(id)}
          aria-current={activeView === id ? "page" : undefined}
          className={`student-tab ${activeView === id ? "student-tab-active" : ""}`}
        >
          <Icon size={15} />
          <span>{label}</span>
        </button>
      ))}
    </nav>
  );
}

export function StudentDashboard() {
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);
  const [work, setWork] = useState<AssignedWork[]>([]);
  const [attendance, setAttendance] = useState<AttendanceRecord[]>([]);
  const [results, setResults] = useState<ResultRecord[]>([]);
  const [resources, setResources] = useState<LearningResource[]>([]);
  const [admitCards, setAdmitCards] = useState<AdmitCard[]>([]);
  const [fees, setFees] = useState<FeeAssignment[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [activeView, setActiveView] = useState<StudentView>("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [studentRes, workRes, attendanceRes, resultRes, resourceRes, admitRes, feeRes, paymentRes, announcementRes] = await Promise.all([
        studentApi.list(),
        assignedWorkApi.list(),
        attendanceApi.list(),
        resultRecordApi.list(),
        learningResourceApi.list(),
        admitCardApi.list(),
        feeApi.list(),
        paymentApi.list(),
        announcementApi.list(),
      ]);
      const studentList = asArray(studentRes);
      setStudents(studentList);
      setSelectedStudentId((current) => (
        studentList.some((item) => item.id === current)
          ? current
          : studentList[0]?.id ?? null
      ));
      setWork(asArray(workRes));
      setAttendance(asArray(attendanceRes));
      setResults(asArray(resultRes));
      setResources(asArray(resourceRes));
      setAdmitCards(asArray(admitRes));
      setFees(asArray(feeRes));
      setPayments(asArray(paymentRes));
      setAnnouncements(asArray(announcementRes));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load student workspace.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const student = useMemo(
    () => students.find((item) => item.id === selectedStudentId) ?? students[0] ?? null,
    [selectedStudentId, students]
  );
  const visibleWork = useMemo(
    () => student ? work.filter((item) => item.section === student.section) : [],
    [student, work]
  );
  const visibleAttendance = useMemo(
    () => student ? attendance.filter((item) => item.student === student.id) : [],
    [attendance, student]
  );
  const visibleResults = useMemo(
    () => student ? results.filter((item) => item.student === student.id) : [],
    [results, student]
  );
  const visibleResources = useMemo(
    () => student ? resources.filter((item) => item.section === student.section) : [],
    [resources, student]
  );
  const visibleAdmitCards = useMemo(
    () => student ? admitCards.filter((card) => card.student === student.id) : [],
    [admitCards, student]
  );
  const visibleFees = useMemo(
    () => student ? fees.filter((item) => item.student === student.id) : [],
    [fees, student]
  );
  const visiblePayments = useMemo(() => {
    const feeIds = new Set(visibleFees.map((item) => item.id));
    return payments.filter((payment) => feeIds.has(payment.fee_assignment));
  }, [payments, visibleFees]);

  const presentCount = visibleAttendance.filter((item) => item.status === "present").length;
  const attendancePct = visibleAttendance.length ? Math.round((presentCount / visibleAttendance.length) * 100) : 0;
  const openWork = visibleWork.filter((item) => item.status !== "closed");
  const latestAdmitCard = visibleAdmitCards.find((card) => card.status === "issued") ?? visibleAdmitCards[0];
  const outstandingAmount = visibleFees.reduce((total, item) => {
    const openAmount = item.outstanding_amount ?? (item.status === "paid" ? 0 : item.amount);
    return total + amountValue(openAmount);
  }, 0);
  const paidAmount = visibleFees.reduce((total, item) => total + amountValue(item.amount_paid), 0);

  if (loading) {
    return <WorkspacePlaceholder title="Student workspace" detail="Preparing attendance, LMS, fees, and results." />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-16">
        <p className="text-sm text-rose-600">{error}</p>
        <button type="button" onClick={load} className="flex items-center gap-2 rounded-2xl bg-ink px-4 py-2 text-sm font-medium text-white">
          <RefreshCcw size={14} />
          Retry
        </button>
      </div>
    );
  }

  if (!student) {
    return <EmptyState label="No learner profile is linked to this login." />;
  }

  return (
    <div className="space-y-6">
      <div className="mastersoft-page-title flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <span className="block truncate">{pageTitleFor(activeView)}</span>
          <span className="mt-1 block text-sm font-medium text-muted">
            {student.full_name} - {student.admission_number}
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {students.length > 1 && (
            <label className="flex min-w-0 items-center gap-2 rounded-md border border-line/70 bg-white px-3 py-2 text-sm text-muted shadow-sm">
              <span className="shrink-0 font-medium">Learner</span>
              <select
                value={student.id}
                onChange={(event) => setSelectedStudentId(Number(event.target.value))}
                className="min-h-0 min-w-0 max-w-[13rem] border-0 bg-transparent p-0 font-medium text-ink outline-none"
                aria-label="Select learner"
              >
                {students.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.full_name} ({item.admission_number})
                  </option>
                ))}
              </select>
            </label>
          )}
          <button
            type="button"
            onClick={load}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-line/70 bg-white px-3 text-sm font-medium text-muted shadow-sm hover:bg-slate-50 hover:text-ink"
          >
            <RefreshCcw size={14} />
            Refresh
          </button>
        </div>
      </div>

      <StudentQuickTabs activeView={activeView} setActiveView={setActiveView} />

      <div className="min-w-0 space-y-6">
          {activeView === "overview" && (
            <StudentHomePage
              attendancePct={attendancePct}
              presentCount={presentCount}
              attendanceTotal={visibleAttendance.length}
              openWork={openWork}
              visibleWork={visibleWork}
              visibleAdmitCards={visibleAdmitCards}
              notices={announcements}
              setActiveView={setActiveView}
            />
          )}

          {activeView === "profile" && <StudentCompleteDetailPage student={student} />}
          {activeView === "lms" && <LmsSelectCoursePage student={student} />}
          {activeView === "work" && <WorkList items={visibleWork} framed />}
          {activeView === "attendance" && (
        <section className="surface overflow-hidden shadow-soft">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line/60 px-5 py-4">
            <h2 className="font-semibold text-ink">Attendance History</h2>
            <Badge variant={attendancePct >= 75 ? "success" : attendancePct >= 50 ? "warning" : "danger"}>{attendancePct}%</Badge>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line/60 bg-slate-50">
                  {["Date", "Section", "Status"].map((head) => (
                    <th key={head} className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted">{head}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {visibleAttendance.length === 0 ? (
                  <tr><td colSpan={3} className="px-5 py-12 text-center text-muted">No attendance records.</td></tr>
                ) : visibleAttendance.map((item) => (
                  <tr key={item.id} className="border-b border-line/40 hover:bg-slate-50/60">
                    <td className="px-5 py-3.5 text-ink">{formatDate(item.date)}</td>
                    <td className="px-5 py-3.5 text-muted">{item.section_label}</td>
                    <td className="px-5 py-3.5"><Badge variant={statusBadge(item.status)}>{statusLabel(item.status)}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
          )}
          {activeView === "results" && <ResultList items={visibleResults} framed />}
          {activeView === "fees" && (
            <OnlinePaymentPage
              student={student}
              items={visibleFees}
              payments={visiblePayments}
              outstandingAmount={outstandingAmount}
              paidAmount={paidAmount}
            />
          )}
          {activeView === "parent" && (
            <ParentViewPage
              student={student}
              attendancePct={attendancePct}
              outstandingAmount={outstandingAmount}
              paidAmount={paidAmount}
              assignments={visibleWork}
              results={visibleResults}
              resources={visibleResources}
              fees={visibleFees}
              payments={visiblePayments}
              notices={announcements}
            />
          )}
          {activeView === "resources" && <ResourceList items={visibleResources} />}
          {activeView === "admit" && <AdmitCardPanel card={latestAdmitCard} />}
      </div>
    </div>
  );
}

function WorkList({ items, framed = false }: { items: AssignedWork[]; framed?: boolean }) {
  const content = items.length === 0 ? (
    <p className="px-5 py-10 text-center text-sm text-muted">No assigned work available.</p>
  ) : (
    <div className="divide-y divide-line/40">
      {items.map((item) => (
        <article key={item.id} className="px-5 py-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-muted">{item.subject}</p>
              <h3 className="mt-1 font-semibold text-ink">{item.title}</h3>
              {item.description && <p className="mt-2 max-w-3xl text-sm text-muted">{item.description}</p>}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={statusBadge(item.status)}>{item.status}</Badge>
              <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-0.5 text-xs text-slate-600">
                Due {formatDate(item.due_date)}
              </span>
            </div>
          </div>
        </article>
      ))}
    </div>
  );

  if (!framed) return content;
  return <section className="surface overflow-hidden shadow-soft">{content}</section>;
}

function ResultList({ items, framed = false }: { items: ResultRecord[]; framed?: boolean }) {
  const content = items.length === 0 ? (
    <p className="px-5 py-10 text-center text-sm text-muted">No result records available.</p>
  ) : (
    <div className="divide-y divide-line/40">
      {items.map((item) => {
        const pct = scorePercent(item);
        return (
          <article key={item.id} className="px-5 py-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-muted">{item.exam_name}</p>
                <h3 className="mt-1 font-semibold text-ink">{item.subject}</h3>
                {item.remarks && <p className="mt-2 max-w-3xl text-sm text-muted">{item.remarks}</p>}
              </div>
              <div className="text-right">
                <p className="display-font text-2xl font-bold text-ink">{pct}%</p>
                <p className="text-xs text-muted">{item.score} / {item.max_score}</p>
                {item.grade && <Badge variant={pct >= 75 ? "success" : pct >= 50 ? "warning" : "danger"}>{item.grade}</Badge>}
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );

  if (!framed) return content;
  return <section className="surface overflow-hidden shadow-soft">{content}</section>;
}

function ParentViewPage({
  student,
  attendancePct,
  outstandingAmount,
  paidAmount,
  assignments,
  results,
  resources,
  fees,
  payments,
  notices,
}: {
  student: Student;
  attendancePct: number;
  outstandingAmount: number;
  paidAmount: number;
  assignments: AssignedWork[];
  results: ResultRecord[];
  resources: LearningResource[];
  fees: FeeAssignment[];
  payments: Payment[];
  notices: Announcement[];
}) {
  const latestResult = results[0];
  const pendingAssignments = assignments.filter((item) => item.status !== "closed");
  const pendingFees = fees.filter((item) => item.status !== "paid");

  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_1fr]">
      <section className="surface p-5 shadow-soft xl:col-span-2">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-muted">Parent View</p>
            <h2 className="mt-1 text-xl font-semibold text-ink">{student.full_name}</h2>
            <p className="mt-1 text-sm text-muted">{student.section_label} - {student.campus_name}</p>
          </div>
          <Badge variant={attendancePct >= 75 ? "success" : attendancePct >= 50 ? "warning" : "danger"}>
            {attendancePct}% attendance
          </Badge>
        </div>
      </section>

      {[
        ["Pending fees", formatMoney(outstandingAmount), `${pendingFees.length} open fee record${pendingFees.length === 1 ? "" : "s"}`],
        ["Paid fees", formatMoney(paidAmount), `${payments.length} receipt${payments.length === 1 ? "" : "s"}`],
        ["Pending assignments", pendingAssignments.length, `${assignments.length} total assignment${assignments.length === 1 ? "" : "s"}`],
        ["Available notes", resources.length, "Teacher-uploaded study material"],
      ].map(([label, value, note]) => (
        <div key={label} className="surface p-5 shadow-soft">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">{label}</p>
          <p className="display-font mt-2 text-3xl font-semibold text-ink">{value}</p>
          <p className="mt-1 text-xs text-muted">{note}</p>
        </div>
      ))}

      <section className="surface overflow-hidden shadow-soft">
        <PanelHeader title="Fees & Payment Status" icon={ReceiptText} />
        <div className="divide-y divide-line/50">
          {fees.length ? fees.slice(0, 5).map((fee) => (
            <div key={fee.id} className="flex items-center justify-between gap-4 px-5 py-4 text-sm">
              <div>
                <p className="font-semibold text-ink">{fee.title}</p>
                <p className="text-xs text-muted">Due {formatDate(fee.due_date)}</p>
              </div>
              <div className="text-right">
                <p className="font-semibold text-ink">{formatMoney(fee.outstanding_amount ?? fee.amount)}</p>
                <Badge variant={statusBadge(fee.status)}>{fee.status}</Badge>
              </div>
            </div>
          )) : <p className="px-5 py-10 text-center text-sm text-muted">No fee records available.</p>}
        </div>
      </section>

      <section className="surface overflow-hidden shadow-soft">
        <PanelHeader title="Results" icon={Award} />
        {latestResult ? (
          <div className="p-5">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted">{latestResult.exam_name}</p>
            <h3 className="mt-1 font-semibold text-ink">{latestResult.subject}</h3>
            <p className="mt-3 display-font text-3xl font-semibold text-ink">{scorePercent(latestResult)}%</p>
            <p className="mt-1 text-sm text-muted">{latestResult.score} / {latestResult.max_score} {latestResult.grade ? `- ${latestResult.grade}` : ""}</p>
          </div>
        ) : <p className="px-5 py-10 text-center text-sm text-muted">No published results yet.</p>}
      </section>

      <section className="surface overflow-hidden shadow-soft">
        <PanelHeader title="Assignments & Documents" icon={FileText} />
        <div className="divide-y divide-line/50">
          {assignments.length ? assignments.slice(0, 5).map((item) => (
            <div key={item.id} className="px-5 py-4">
              <p className="font-semibold text-ink">{item.title}</p>
              <p className="mt-1 text-xs text-muted">{item.subject} - Due {formatDate(item.due_date)}</p>
            </div>
          )) : <p className="px-5 py-10 text-center text-sm text-muted">No assignments available.</p>}
        </div>
      </section>

      <section className="surface overflow-hidden shadow-soft">
        <PanelHeader title="Notices" icon={Bell} />
        <div className="divide-y divide-line/50">
          {notices.length ? notices.slice(0, 5).map((notice) => (
            <div key={notice.id} className="px-5 py-4">
              <p className="font-semibold text-ink">{notice.title}</p>
              <p className="mt-1 text-xs text-muted">{formatDate(notice.publish_on)}</p>
            </div>
          )) : <p className="px-5 py-10 text-center text-sm text-muted">No notices available.</p>}
        </div>
      </section>
    </div>
  );
}

function OnlinePaymentPage({
  student,
  items,
  payments,
  outstandingAmount,
  paidAmount,
}: {
  student: Student;
  items: FeeAssignment[];
  payments: Payment[];
  outstandingAmount: number;
  paidAmount: number;
}) {
  const [payBusy, setPayBusy] = useState(false);
  const [payMessage, setPayMessage] = useState("");
  const [payError, setPayError] = useState("");
  const payableFee = items.find((item) => item.status !== "paid" && amountValue(item.outstanding_amount ?? item.amount) > 0);
  const tableRows = items.length
    ? items.map((item, index) => ({
        id: item.id,
        receiptType: item.title,
        semester: String(index + 1),
        payable: item.amount,
        paid: item.amount_paid ?? "0",
        balance: item.outstanding_amount ?? "0",
      }))
    : [];

  async function startPayment() {
    if (!payableFee) return;
    setPayBusy(true);
    setPayError("");
    setPayMessage("");
    try {
      await paymentTransactionApi.create({
        campus: student.campus,
        student: student.id,
        fee_assignment: payableFee.id,
        payment: null,
        provider: "razorpay",
        method: "upi",
        amount: String(amountValue(payableFee.outstanding_amount ?? payableFee.amount)),
        currency: "INR",
        status: "pending",
        gateway_order_id: "",
        gateway_payment_id: "",
        gateway_signature: "",
        receipt_number: "",
        webhook_verified: false,
        raw_payload: { source: "student_portal", fee_title: payableFee.title },
      });
      setPayMessage("Payment transaction created. Complete the payment from the configured Razorpay/UPI checkout.");
    } catch (err) {
      setPayError(err instanceof ApiError ? err.message : "Unable to start payment.");
    } finally {
      setPayBusy(false);
    }
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[18rem_minmax(0,1fr)]">
      <aside className="surface min-h-[34rem] p-4 shadow-soft">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="font-medium text-ink">Online Payment</h2>
          <X size={18} className="text-muted" />
        </div>
        <div className="border-l-4 border-line/70 px-4 py-3 text-sm text-muted">Online Payment</div>
      </aside>

      <section className="surface overflow-hidden p-4 shadow-soft md:p-6">
        <h2 className="mb-4 border-b border-line/70 pb-3 text-xl font-semibold text-ink">Online Payment</h2>

        <div className="grid gap-x-10 gap-y-0 xl:grid-cols-2">
          <div>
            <InfoRow label="Student Name" value={student.full_name} />
            <InfoRow label="RRNO" value={student.admission_number} />
            <InfoRow label="School/Institute Name" value={student.campus_name || "MentriQ School"} />
            <InfoRow label="E-Mail ID" value={student.contact_email} />
          </div>
          <div>
            <InfoRow label="Degree Name" value={student.section_label || "Class / Section"} />
            <InfoRow label="Branch / Program" value={student.section_label || "General"} />
            <InfoRow label="Mobile No." value={student.phone_number} />
            <InfoRow label="Total Amount" value={formatMoney(outstandingAmount || paidAmount)} />
          </div>
        </div>

        <div className="mt-8 grid max-w-3xl gap-5 md:grid-cols-2">
          <label className="block">
            <span className="text-sm font-medium text-ink"><span className="text-red-600">*</span> Receipt Type</span>
            <select className="mt-2 w-full rounded-md border border-blue-200 bg-white px-4 py-3 text-sm text-ink outline-none">
              <option>Academic Fees</option>
              <option>Transport Fees</option>
              <option>Hostel Fees</option>
            </select>
          </label>
          <label className="block">
            <span className="text-sm font-medium text-ink"><span className="text-red-600">*</span> Semester</span>
            <select className="mt-2 w-full rounded-md border border-blue-200 bg-white px-4 py-3 text-sm text-ink outline-none">
              <option>Please Select</option>
              <option>I</option>
              <option>II</option>
              <option>III</option>
              <option>IV</option>
            </select>
          </label>
        </div>

        <div className="mt-12 flex justify-center">
          <button
            type="button"
            onClick={startPayment}
            disabled={!payableFee || payBusy}
            className="rounded-md bg-accent px-5 py-2 text-sm font-semibold text-white hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-60"
          >
            {payBusy ? "Starting..." : "Pay Now"}
          </button>
        </div>
        {payMessage && <p className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-center text-sm text-emerald-700">{payMessage}</p>}
        {payError && <p className="mt-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-center text-sm text-rose-700">{payError}</p>}

        <div className="mt-7">
          <h2 className="mastersoft-section-title">Payment Details</h2>
          <div className="mt-5 overflow-x-auto">
            <table className="text-sm">
              <thead>
                <tr>
                  {["Receipt Type", "Semester", "Payable Fee / Applicable Fee", "Paid", "Balance"].map((head) => (
                    <th key={head} className="px-4 py-3 text-left">{head}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tableRows.length ? tableRows.map((row) => (
                  <tr key={row.id} className="border-b border-white even:bg-slate-100">
                    <td className="px-4 py-3">{row.receiptType}</td>
                    <td className="px-4 py-3 text-blue-700">{row.semester}</td>
                    <td className="px-4 py-3">{Number(row.payable || 0).toFixed(2)}</td>
                    <td className="px-4 py-3">{Number(row.paid || 0).toFixed(2)}</td>
                    <td className="px-4 py-3">{Number(row.balance || 0).toFixed(2)}</td>
                  </tr>
                )) : (
                  <tr><td className="px-4 py-8 text-center text-muted" colSpan={5}>No fee payment records available.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-6">
          <h2 className="mastersoft-section-title">Previous Receipts Information</h2>
          <div className="mt-4 divide-y divide-line/60 rounded-md border border-line/70 bg-white">
            {payments.length === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-muted">No previous receipt records available.</p>
            ) : payments.map((payment) => (
              <div key={payment.id} className="flex items-center justify-between gap-4 px-4 py-3 text-sm">
                <div>
                  <p className="font-semibold text-ink">{payment.fee_title ?? "Academic Fees"}</p>
                  <p className="text-xs capitalize text-muted">{payment.payment_method} - {payment.reference_number || "No reference"}</p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-ink">{formatMoney(payment.amount_paid)}</p>
                  <p className="text-xs text-muted">{formatDate(payment.paid_on)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

function ResourceList({ items }: { items: LearningResource[] }) {
  if (items.length === 0) return <EmptyState label="No resources or notes published yet." />;

  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {items.map((item) => (
        <article key={item.id} className="surface p-5 shadow-soft">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-muted">{item.subject}</p>
              <h3 className="mt-1 font-semibold text-ink">{item.title}</h3>
            </div>
            <Badge variant="info">{formatResourceType(item.resource_type)}</Badge>
          </div>
          {item.description && <p className="mt-3 text-sm text-muted">{item.description}</p>}
          <div className="mt-4 flex items-center justify-between gap-3">
            <span className="text-xs text-muted">{formatDate(item.published_on)}</span>
            {item.file_url && (
              <a
                href={item.file_url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 rounded-xl border border-line/70 px-3 py-1.5 text-xs font-medium text-ink hover:bg-slate-50"
              >
                <ExternalLink size={12} />
                Open
              </a>
            )}
          </div>
        </article>
      ))}
    </section>
  );
}

function AdmitCardPanel({ card }: { card?: AdmitCard }) {
  if (!card) return <EmptyState label="No admit card issued yet." />;

  return (
    <section className="surface p-6 shadow-soft">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-line/60 pb-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">Admit Card</p>
          <h2 className="display-font mt-1 text-2xl font-bold text-ink">{card.exam_name}</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            <Badge variant={statusBadge(card.status)}>{card.status}</Badge>
            <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-0.5 text-xs text-slate-600">
              Roll No. {card.roll_number}
            </span>
          </div>
        </div>
        <button
          type="button"
          onClick={() => window.print()}
          className="flex items-center gap-2 rounded-2xl border border-line/70 bg-white px-4 py-2 text-sm font-medium text-muted transition hover:bg-slate-50 hover:text-ink"
        >
          <Printer size={14} />
          Print
        </button>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-line/70 bg-white p-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">Student</p>
          <p className="mt-2 font-semibold text-ink">{card.student_name}</p>
          <p className="mt-1 text-sm text-muted">{card.admission_number} - {card.section_label}</p>
        </div>
        <div className="rounded-2xl border border-line/70 bg-white p-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">Schedule</p>
          <p className="mt-2 flex items-center gap-2 font-semibold text-ink">
            <CalendarDays size={15} className="text-teal-600" />
            {formatDate(card.exam_date)}
          </p>
          <p className="mt-1 text-sm text-muted">Reporting {card.reporting_time?.slice(0, 5)}</p>
        </div>
        <div className="rounded-2xl border border-line/70 bg-white p-4 md:col-span-2">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">Venue</p>
          <p className="mt-2 flex items-center gap-2 font-semibold text-ink">
            <MapPin size={15} className="text-teal-600" />
            {card.venue}
          </p>
        </div>
      </div>

      {card.instructions && (
        <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-amber-700">Instructions</p>
          <p className="mt-2 text-sm text-amber-800">{card.instructions}</p>
        </div>
      )}
    </section>
  );
}

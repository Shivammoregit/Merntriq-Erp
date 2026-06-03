"use client";

import Image from "next/image";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  Building2,
  CheckCircle2,
  Eye,
  EyeOff,
  KeyRound,
  Lock,
  QrCode,
  RefreshCcw,
  Search,
  ShieldCheck,
  Smartphone,
  User,
  UsersRound,
  WifiOff,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { ApiError, authApi, getActiveTenantCampusCode, type CaptchaChallenge } from "@/lib/api";
import { BrandLogo } from "@/components/brand-logo";

const DEMO_PASSWORD = "Mentriq@123";

type DemoAccount = {
  role: string;
  username: string;
  scope: string;
  responsibility: string;
};

const DEMO_ACCOUNTS = [
  {
    role: "Super admin",
    username: "super.admin",
    scope: "All campuses",
    responsibility: "Full access to all campuses, settings, audit logs, and support issues.",
  },
  {
    role: "IT admin",
    username: "it.admin",
    scope: "Main campus",
    responsibility: "Manage users, devices, campus settings, attendance configuration, and approvals.",
  },
  {
    role: "IT admin",
    username: "north.admin",
    scope: "North campus",
    responsibility: "Manage north campus users, devices, operations, and configuration.",
  },
  {
    role: "Academic admin",
    username: "academic.admin",
    scope: "Academic records",
    responsibility: "Own sections, academic records, exams, resources, and report workflows.",
  },
  {
    role: "Finance admin",
    username: "finance.admin",
    scope: "Fees desk",
    responsibility: "Own fee structures, online payments, receipts, dues, and financial reports.",
  },
  {
    role: "Teacher",
    username: "teacher.meera",
    scope: "Main campus",
    responsibility: "Mark attendance, upload homework, publish resources, and update results.",
  },
  {
    role: "Teacher",
    username: "teacher.dev",
    scope: "North campus",
    responsibility: "Manage north campus class attendance, assignments, resources, and results.",
  },
  {
    role: "Student",
    username: "student.anaya",
    scope: "Learner portal",
    responsibility: "View personal profile, attendance, work, LMS resources, fees, and admit cards.",
  },
  {
    role: "Parent",
    username: "parent.rohan",
    scope: "Family portal",
    responsibility: "View linked student attendance, homework, results, fee status, transport, hostel, and notices.",
  },
  {
    role: "Admission admin",
    username: "admission.admin",
    scope: "Admissions",
    responsibility: "Approve applications, verify documents, generate IDs, and allocate class sections.",
  },
  {
    role: "Student records admin",
    username: "student.records",
    scope: "SIS",
    responsibility: "Maintain student profiles, guardians, medical records, documents, and academic history.",
  },
  {
    role: "HR admin",
    username: "hr.admin",
    scope: "Staff",
    responsibility: "Register employees, assign roles, maintain salary structure, and track leave.",
  },
  {
    role: "Exam admin",
    username: "exam.admin",
    scope: "Examination",
    responsibility: "Create exam schedules, manage marks entry, process results, and issue admit cards.",
  },
  {
    role: "Certificate admin",
    username: "certificate.admin",
    scope: "Certificates",
    responsibility: "Generate transfer, bonafide, character certificates, marksheets, and digital signatures.",
  },
  {
    role: "Library admin",
    username: "library.admin",
    scope: "Library",
    responsibility: "Manage books, issue-return flow, fines, barcode records, and reading resources.",
  },
  {
    role: "Transport admin",
    username: "transport.admin",
    scope: "Transport",
    responsibility: "Maintain bus routes, drivers, GPS tracking, and transport fee coordination.",
  },
  {
    role: "Hostel admin",
    username: "hostel.admin",
    scope: "Hostel",
    responsibility: "Manage room allocation, hostel fees, check-in/out records, and occupancy.",
  },
  {
    role: "Inventory admin",
    username: "inventory.admin",
    scope: "Inventory",
    responsibility: "Track assets, lab equipment, purchase records, stock, and maintenance needs.",
  },
  {
    role: "Communication admin",
    username: "communication.admin",
    scope: "Communication",
    responsibility: "Send SMS, email notices, announcement board updates, and student or parent messages.",
  },
  {
    role: "Teacher",
    username: "teacher.english",
    scope: "English",
    responsibility: "Manage English homework, reading journals, attendance, and result updates.",
  },
  {
    role: "Teacher",
    username: "teacher.maths",
    scope: "Mathematics",
    responsibility: "Publish maths assignments, record marks, and review learner progress.",
  },
  {
    role: "Teacher",
    username: "teacher.science",
    scope: "Science",
    responsibility: "Upload science resources, practical work, homework, and attendance records.",
  },
  {
    role: "Teacher",
    username: "teacher.social",
    scope: "Social science",
    responsibility: "Publish map work, worksheets, class notes, attendance, and assessment updates.",
  },
  {
    role: "Teacher",
    username: "teacher.hindi",
    scope: "Hindi",
    responsibility: "Manage Hindi lessons, assignments, attendance, and student assessment updates.",
  },
  {
    role: "Teacher",
    username: "teacher.computer",
    scope: "Computer lab",
    responsibility: "Run computer lab resources, digital assignments, quizzes, and online learning tasks.",
  },
  {
    role: "Teacher",
    username: "teacher.sports",
    scope: "Sports",
    responsibility: "Record sports participation, activity attendance, and student performance.",
  },
  {
    role: "Teacher",
    username: "teacher.art",
    scope: "Art",
    responsibility: "Review art assignments, project submissions, and activity evaluations.",
  },
  {
    role: "Teacher",
    username: "teacher.music",
    scope: "Music",
    responsibility: "Manage music practice schedules, resources, activity progress, and notices.",
  },
  {
    role: "Teacher",
    username: "teacher.primary",
    scope: "Primary",
    responsibility: "Handle primary attendance, homework, notices, and report remarks.",
  },
  {
    role: "Teacher",
    username: "teacher.exam",
    scope: "Exam duty",
    responsibility: "Support internal marks, result drafts, exam duty, and assessment checks.",
  },
  {
    role: "Teacher",
    username: "teacher.library",
    scope: "Reading support",
    responsibility: "Guide reading lists, library periods, resources, and learner reading progress.",
  },
  {
    role: "Student",
    username: "student.aarav",
    scope: "Learner",
    responsibility: "View attendance, homework, fee dues, results, notices, and admit cards.",
  },
  {
    role: "Student",
    username: "student.diyaa",
    scope: "Learner",
    responsibility: "Access course resources, assignment submissions, online learning, and results.",
  },
  {
    role: "Student",
    username: "student.kabir",
    scope: "Learner",
    responsibility: "Review admit card, school notices, academic history, and fees.",
  },
  {
    role: "Student",
    username: "student.isha",
    scope: "Learner",
    responsibility: "Track progress, homework deadlines, report cards, and LMS resources.",
  },
  {
    role: "Student",
    username: "student.mira",
    scope: "North learner",
    responsibility: "Use north campus student dashboard for attendance and academic updates.",
  },
  {
    role: "Student",
    username: "student.arjun",
    scope: "North learner",
    responsibility: "View assignments, fees, results, documents, and school notifications.",
  },
  {
    role: "Student",
    username: "student.tara",
    scope: "Learner",
    responsibility: "Open profile, documents, LMS resources, homework, and notices.",
  },
  {
    role: "Student",
    username: "student.ved",
    scope: "North learner",
    responsibility: "Use timetable, homework, online payment view, and attendance dashboard.",
  },
  {
    role: "Student",
    username: "student.zara",
    scope: "Learner",
    responsibility: "View marks, announcements, registered courses, and admit cards.",
  },
  {
    role: "Student",
    username: "student.om",
    scope: "North learner",
    responsibility: "Check attendance, documents, resources, and exam admit cards.",
  },
] satisfies DemoAccount[];

const LOGIN_FEATURES = [
  { label: "Role access", value: "Admin, teacher, parent, student" },
  { label: "Campus suite", value: "Admission, fees, academics, reports" },
  { label: "Learner portal", value: "Attendance, homework, results, admit card" },
];

export function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [captcha, setCaptcha] = useState("");
  const [captchaChallenge, setCaptchaChallenge] = useState<CaptchaChallenge | null>(null);
  const [captchaLoading, setCaptchaLoading] = useState(false);
  const [remember, setRemember] = useState(false);
  const [showPwd, setShowPwd] = useState(false);
  const [showPasswordHelp, setShowPasswordHelp] = useState(false);
  const [accountSearch, setAccountSearch] = useState("");
  const [tenantCode, setTenantCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const filteredDemoAccounts = useMemo(() => {
    const term = accountSearch.trim().toLowerCase();
    if (!term) return DEMO_ACCOUNTS;
    return DEMO_ACCOUNTS.filter((account) =>
      [account.role, account.username, account.scope, account.responsibility]
        .join(" ")
        .toLowerCase()
        .includes(term),
    );
  }, [accountSearch]);
  const connectionStatus = useMemo(() => {
    if (captchaLoading) return { label: "Checking API", tone: "checking", Icon: RefreshCcw };
    if (captchaChallenge) return { label: "API connected", tone: "online", Icon: CheckCircle2 };
    return { label: "API offline", tone: "offline", Icon: WifiOff };
  }, [captchaChallenge, captchaLoading]);
  const ConnectionIcon = connectionStatus.Icon;
  const tenantLabel = tenantCode ? `Tenant ${tenantCode}` : "Central tenant";

  const loadCaptcha = useCallback(async (clearError = true) => {
    setCaptchaLoading(true);
    if (clearError) setError("");
    try {
      const challenge = await authApi.captcha();
      setCaptchaChallenge(challenge);
      setCaptcha("");
    } catch (err) {
      setCaptchaChallenge(null);
      setError(err instanceof ApiError ? err.message : "Captcha could not be loaded. Check the server connection.");
    } finally {
      setCaptchaLoading(false);
    }
  }, []);

  useEffect(() => {
    setTenantCode(getActiveTenantCampusCode());
    void loadCaptcha(false);
  }, [loadCaptcha]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!username.trim() || !password) return;
    if (!captchaChallenge) {
      setError("Captcha is not ready. Refresh the captcha and try again.");
      return;
    }
    if (!captcha.trim()) {
      setError("Enter the captcha code shown on the screen.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await login(username.trim(), password, captchaChallenge.challenge_id, captcha.trim());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed. Please try again.");
      void loadCaptcha(false);
    } finally {
      setBusy(false);
    }
  }

  function fillDemoAccount(usernameValue: string) {
    setUsername(usernameValue);
    setPassword(DEMO_PASSWORD);
    setError("");
  }

  return (
    <main className="login-shell">
      <section className="login-frame">
        <aside className="login-hero" aria-label="MentriQ360 ERP overview">
          <div className="relative z-10 flex h-full flex-col gap-6 p-6 lg:p-8 xl:p-10">
            <div className="flex items-center justify-between gap-4">
              <BrandLogo size="lg" />
              <span className="rounded-md border border-line/70 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-muted shadow-sm">
                Campus360
              </span>
            </div>

            <div className="login-school-photo" aria-hidden="true">
              <Image
                src="/login-school-campus.jpg"
                alt=""
                fill
                priority
                sizes="(min-width: 1024px) 48vw, 0px"
                className="object-cover"
              />
            </div>

            <div className="max-w-2xl py-6">
              <span className="inline-flex rounded-md border border-blue-100 bg-accent-soft px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-accent-strong">
                Secure ERP login
              </span>
              <h1 className="mt-5 text-4xl font-bold leading-tight text-ink xl:text-5xl">
                One login for every campus workflow.
              </h1>
              <p className="mt-4 max-w-xl text-sm leading-7 text-muted">
                Manage admissions, attendance, academics, fees, reports, staff, guardians, and student services from one responsive ERP workspace.
              </p>
            </div>

            <div className="mt-auto grid gap-3 xl:grid-cols-3">
              {LOGIN_FEATURES.map(({ label, value }) => (
                <div key={label} className="rounded-lg border border-line/70 bg-white/90 p-4 text-ink shadow-sm backdrop-blur">
                  <p className="text-sm font-semibold">{label}</p>
                  <p className="mt-1 text-xs leading-5 text-muted">{value}</p>
                </div>
              ))}
            </div>
          </div>
        </aside>

        <section className="login-panel-wrap">
          <div className="mb-5 flex items-center justify-between gap-4 lg:hidden">
            <BrandLogo compact className="shrink-0" />
            <span className="rounded-md border border-line/70 bg-white px-3 py-1 text-xs font-semibold text-muted">
              Campus ERP
            </span>
          </div>

          <form onSubmit={handleSubmit} className="login-card" noValidate>
            <div className="mb-6 flex flex-col gap-4 border-b border-line/70 pb-4 sm:flex-row sm:items-start sm:justify-between">
              <BrandLogo />
              <p className="max-w-[13rem] text-left text-xs leading-5 text-muted sm:text-right">
                MentriQ Campus360 School ERP
                <span className="block font-semibold text-ink">Secure institutional access</span>
              </p>
            </div>

            <div className="mb-6 text-left">
              <div className="login-status-strip mb-4" aria-label="Connection and tenant status">
                <span className={`login-status-pill login-status-pill--${connectionStatus.tone}`}>
                  <ConnectionIcon size={14} className={captchaLoading ? "animate-spin" : ""} />
                  {connectionStatus.label}
                </span>
                <span className="login-status-pill login-status-pill--neutral">
                  <Building2 size={14} />
                  {tenantLabel}
                </span>
              </div>
              <p className="inline-flex rounded-full bg-accent-soft px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-accent-strong">
                Professional ERP login
              </p>
              <h1 className="mt-2 text-2xl font-bold text-ink">Sign in</h1>
              <p className="mt-1 text-sm leading-6 text-muted">Use the account assigned by your institution.</p>
            </div>

            {error && (
              <div role="alert" className="mb-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <label htmlFor="login-username" className="block">
                <span className="mb-1.5 block text-sm font-semibold text-ink">User name</span>
                <span className="relative block">
                  <User size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
                  <input
                    id="login-username"
                    type="text"
                    autoComplete="username"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Enter user name"
                    className="w-full rounded-md border border-line bg-white py-3 pl-10 pr-4 text-sm text-ink outline-none placeholder:text-slate-400"
                  />
                </span>
              </label>

              <label htmlFor="login-password" className="block">
                <span className="mb-1.5 block text-sm font-semibold text-ink">Password</span>
                <span className="relative block">
                  <Lock size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
                  <input
                    id="login-password"
                    type={showPwd ? "text" : "password"}
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password"
                    className="w-full rounded-md border border-line bg-white py-3 pl-10 pr-12 text-sm text-ink outline-none placeholder:text-slate-400"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPwd(!showPwd)}
                    className="absolute right-2.5 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-md text-muted hover:bg-slate-50 hover:text-ink"
                    aria-label={showPwd ? "Hide password" : "Show password"}
                  >
                    {showPwd ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </span>
              </label>

              <div className="grid gap-3 sm:grid-cols-[1fr_8.5rem]">
                <div>
                  <span className="mb-1.5 block text-sm font-semibold text-ink">Captcha number</span>
                  <div className="flex min-h-[3.75rem] items-center gap-2 rounded-md border border-line bg-slate-50 px-3 py-2">
                    <button
                      type="button"
                      onClick={() => void loadCaptcha()}
                      disabled={captchaLoading || busy}
                      className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-muted hover:bg-white hover:text-ink disabled:cursor-not-allowed disabled:opacity-50"
                      aria-label="Refresh captcha"
                    >
                      <RefreshCcw size={17} />
                    </button>
                    {captchaChallenge?.code ? (
                      <span
                        aria-label={`Captcha number ${captchaChallenge.code}`}
                        className="flex h-[3.1rem] w-full max-w-[11.5rem] select-none items-center justify-center rounded-md border border-line/70 bg-white px-4 font-mono text-2xl font-bold tracking-[0.28em] text-red-600 shadow-sm"
                      >
                        {captchaChallenge.code}
                      </span>
                    ) : (
                      <span className="flex h-[3.1rem] flex-1 items-center justify-center rounded-md border border-dashed border-line/80 bg-white text-xs font-semibold uppercase tracking-[0.16em] text-muted">
                        Captcha
                      </span>
                    )}
                  </div>
                </div>
                <label htmlFor="login-captcha" className="block">
                  <span className="mb-1.5 block text-sm font-semibold text-ink">Enter number</span>
                  <input
                    id="login-captcha"
                    type="text"
                    inputMode="numeric"
                    value={captcha}
                    onChange={(e) => setCaptcha(e.target.value.replace(/\D/g, "").slice(0, 5))}
                    placeholder="Number"
                    autoComplete="off"
                    maxLength={5}
                    className="w-full rounded-md border border-line bg-white px-3 py-3 text-sm text-ink outline-none placeholder:text-slate-400"
                  />
                </label>
              </div>
            </div>

            <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
              <label className="flex items-center gap-2 text-sm text-ink">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                  className="h-4 w-4 rounded border-line"
                />
                Remember me
              </label>
              <button
                type="button"
                onClick={() => setShowPasswordHelp((open) => !open)}
                className="text-sm font-semibold text-accent hover:text-ink"
              >
                Forgot password?
              </button>
            </div>

            {showPasswordHelp && (
              <div className="mt-3 flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2.5 text-xs leading-5 text-amber-800">
                <KeyRound size={15} className="mt-0.5 shrink-0" />
                <span>Contact the IT admin team to reset or rotate your user name or password.</span>
              </div>
            )}

            <button
              id="login-submit"
              type="submit"
              disabled={busy || captchaLoading || !captchaChallenge || !username || !password || !captcha}
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-md bg-red-600 py-3 text-base font-semibold text-white shadow-md transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {busy ? "Signing in..." : "Sign in"}
              {!busy ? <ArrowRight size={17} /> : null}
            </button>

            <div className="mt-5 grid gap-3 sm:grid-cols-[1fr_auto]">
              <div className="inline-flex items-center gap-2 rounded-md bg-slate-950 px-4 py-2 text-white">
                <Smartphone size={22} />
                <span>
                  <span className="block text-[10px] uppercase leading-none text-white/70">Mobile access</span>
                  <span className="block text-sm font-semibold leading-tight">ERP App Ready</span>
                </span>
              </div>
              <div className="flex h-14 w-14 items-center justify-center rounded-md border border-line text-ink">
                <QrCode size={38} />
              </div>
            </div>

            <div className="mt-5 rounded-lg border border-line/70 bg-slate-50 p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="min-w-0">
                  <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-muted">
                    <UsersRound size={14} />
                    Demo users and responsibilities
                  </p>
                  <p className="mt-1 text-xs text-muted">{DEMO_ACCOUNTS.length} users across admin, teacher, parent, and student roles.</p>
                </div>
                <span className="rounded-full border border-line/70 bg-white px-2 py-0.5 text-[11px] font-semibold text-muted">
                  Password: {DEMO_PASSWORD}
                </span>
              </div>

              <label htmlFor="demo-account-search" className="relative mt-3 block">
                <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                <input
                  id="demo-account-search"
                  value={accountSearch}
                  onChange={(event) => setAccountSearch(event.target.value)}
                  placeholder="Search user, role, module, or responsibility"
                  className="w-full rounded-md border border-line/70 bg-white py-2.5 pl-9 pr-3 text-xs text-ink outline-none placeholder:text-slate-400"
                />
              </label>

              <div className="mt-3 grid max-h-64 gap-2 overflow-y-auto pr-1 sm:grid-cols-2">
                {filteredDemoAccounts.map((account) => (
                  <button
                    key={account.username}
                    type="button"
                    onClick={() => fillDemoAccount(account.username)}
                    className="flex min-w-0 items-start gap-2 rounded-md border border-line/70 bg-white px-3 py-2 text-left text-xs shadow-sm hover:border-accent hover:bg-accent-soft"
                  >
                    <ShieldCheck size={14} className="mt-0.5 shrink-0 text-accent" />
                    <span className="min-w-0">
                      <span className="flex flex-wrap items-center gap-1.5">
                        <span className="font-semibold text-ink">{account.role}</span>
                        <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-muted">{account.scope}</span>
                      </span>
                      <span className="mt-0.5 block truncate font-medium text-accent">{account.username}</span>
                      <span className="mt-1 block line-clamp-2 leading-5 text-muted">{account.responsibility}</span>
                    </span>
                  </button>
                ))}
                {filteredDemoAccounts.length === 0 && (
                  <p className="rounded-md border border-line/70 bg-white px-3 py-5 text-center text-xs text-muted sm:col-span-2">
                    No demo user matches your search.
                  </p>
                )}
              </div>
            </div>
          </form>

          <p className="mt-4 text-center text-xs text-muted lg:text-right">
            Compatible with Chrome 70+, Firefox 65+, and Microsoft Edge 89+
          </p>
        </section>
      </section>
    </main>
  );
}

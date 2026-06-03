"use client";

import { useMemo, useState } from "react";
import {
  ArrowRight,
  BadgeCheck,
  BarChart3,
  Bell,
  BookOpen,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  CreditCard,
  Database,
  Download,
  FileText,
  GraduationCap,
  LayoutDashboard,
  Layers3,
  LogIn,
  Plus,
  RefreshCcw,
  ReceiptText,
  Search,
  ShieldCheck,
  Sparkles,
  UserRound,
  UserRoundCheck,
  Users
} from "lucide-react";

import { appConfig } from "@/lib/config";
import { BrandLogo } from "@/components/brand-logo";
import {
  flowNodes,
  moduleCards,
  overviewMetrics,
  roleTabs,
  roleWorkspaces,
  workflowPhases
} from "@/lib/erp-data";

const toneClasses = {
  accent: "border-teal-200 bg-teal-50/80 text-teal-900",
  info: "border-blue-200 bg-blue-50/80 text-blue-900",
  warning: "border-amber-200 bg-amber-50/80 text-amber-900",
  danger: "border-rose-200 bg-rose-50/80 text-rose-900"
} as const;

const iconMap = {
  Authentication: LogIn,
  Admin: LayoutDashboard,
  Attendance: UserRoundCheck,
  Fees: ReceiptText,
  ShieldCheck,
  GraduationCap,
  ClipboardCheck,
  CreditCard,
  Users,
  Database,
  BarChart3,
  Layers3,
  BookOpen,
  FileText,
  UserRound,
  Sparkles
} as const;

const moduleIconMap = {
  ShieldCheck,
  GraduationCap,
  ClipboardCheck,
  ReceiptText,
  CreditCard,
  Users
} as const;

type WorkflowPhaseId = (typeof workflowPhases)[number]["id"];

export function ERPWorkspace() {
  const [selectedPhaseId, setSelectedPhaseId] = useState<WorkflowPhaseId>(workflowPhases[0].id);
  const [notificationOpen, setNotificationOpen] = useState(false);

  const selectedPhase = useMemo(
    () => workflowPhases.find((phase) => phase.id === selectedPhaseId) ?? workflowPhases[0],
    [selectedPhaseId]
  );

  const SelectedPhaseIcon = iconMap[selectedPhase.icon as keyof typeof iconMap] ?? Sparkles;

  function exportFlow() {
    const content = JSON.stringify(
      {
        product: "MentriQ Campus360",
        exported_at: new Date().toISOString(),
        workflow_phases: workflowPhases,
        flow_nodes: flowNodes,
        modules: moduleCards,
        role_workspaces: roleWorkspaces,
      },
      null,
      2,
    );
    const blob = new Blob([content], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "mentriq360-workflow-map.json";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="min-h-screen overflow-x-hidden">
      <div className="absolute inset-0 -z-10 bg-page" />

      <header className="border-b border-white/60 bg-white/70 backdrop-blur-xl">
        <div className="page-shell flex min-h-16 items-center justify-between gap-3 py-3">
          <div className="flex items-center gap-3">
            <BrandLogo />
          </div>

          <div className="hidden min-w-0 max-w-[26rem] flex-1 items-center gap-2 rounded-2xl border border-line/70 bg-white/80 px-4 py-2 shadow-sm md:flex">
            <Search size={16} className="text-muted" aria-hidden="true" />
            <span className="truncate text-sm text-muted">Search student, fee record, attendance, or staff profile</span>
          </div>

          <div className="flex items-center gap-2">
            <a
              href={appConfig.apiHealthUrl}
              className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-line/70 bg-white/80 text-muted shadow-sm transition hover:-translate-y-0.5 hover:text-ink"
              aria-label="API health"
              title="API health"
            >
              <RefreshCcw size={16} aria-hidden="true" />
            </a>
            <div className="relative">
              <button
                className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-line/70 bg-white/80 text-muted shadow-sm transition hover:-translate-y-0.5 hover:text-ink"
                aria-label="Notifications"
                title="Notifications"
                type="button"
                aria-expanded={notificationOpen}
                onClick={() => setNotificationOpen((open) => !open)}
              >
                <Bell size={16} aria-hidden="true" />
              </button>
              {notificationOpen && (
                <div className="absolute right-0 top-full z-30 mt-2 w-72 rounded-lg border border-line/70 bg-white p-3 text-sm shadow-xl">
                  <p className="font-semibold text-ink">Blueprint status</p>
                  <p className="mt-1 leading-6 text-muted">Workflow map is ready. Open the live dashboard to create records and operate modules.</p>
                  <a href="/dashboard" className="mt-3 inline-flex rounded-md bg-ink px-3 py-2 text-xs font-semibold text-white">
                    Open ERP
                  </a>
                </div>
              )}
            </div>
            <button
              className="inline-flex h-10 items-center gap-2 rounded-2xl bg-ink px-4 text-sm font-semibold text-white shadow-soft transition hover:-translate-y-0.5"
              type="button"
              onClick={() => window.location.assign("/dashboard")}
            >
              <Plus size={16} aria-hidden="true" />
              <span className="hidden sm:inline">New Record</span>
            </button>
          </div>
        </div>
      </header>

      <div className="page-shell py-6 md:py-8">
        <section className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
          <div className="surface relative overflow-hidden p-6 shadow-soft md:p-8">
            <div className="relative flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-2 rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-900">
                <Sparkles size={14} aria-hidden="true" />
                Backend aligned UI
              </span>
              <span className="inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-900">
                <Database size={14} aria-hidden="true" />
                PostgreSQL first
              </span>
              <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
                <Layers3 size={14} aria-hidden="true" />
                Modules and roles
              </span>
            </div>

            <div className="relative mt-6 grid gap-5 xl:grid-cols-[1.15fr_0.85fr] xl:items-end">
              <div>
                <p className="text-sm font-medium text-muted">Academic year 2026-27</p>
                <h2 className="display-font mt-2 max-w-3xl text-4xl font-semibold tracking-tight text-ink md:text-5xl">
                  Phase-wise ERP flow for admission, attendance, academics, fees, and student visibility.
                </h2>
                <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
                  This workspace follows the attached ER workflow and the backend entities exposed by Django:
                  authenticate first, create student master data, mark attendance, manage fee assignments, record
                  payments, and surface the data in role-based dashboards.
                </p>

                <div className="mt-6 flex flex-wrap gap-3">
                  <a
                    href={appConfig.apiDocsUrl}
                    className="inline-flex items-center gap-2 rounded-2xl bg-ink px-4 py-2.5 text-sm font-semibold text-white shadow-soft transition hover:-translate-y-0.5"
                  >
                    <FileText size={16} aria-hidden="true" />
                    API Docs
                  </a>
                  <button
                    className="inline-flex items-center gap-2 rounded-2xl border border-line/80 bg-white/80 px-4 py-2.5 text-sm font-semibold text-ink shadow-sm transition hover:-translate-y-0.5"
                    type="button"
                    onClick={exportFlow}
                  >
                    <Download size={16} aria-hidden="true" />
                    Export Flow
                  </button>
                </div>
              </div>

              <div className="grid gap-3">
                <div className="rounded-3xl border border-line/70 bg-white/85 p-4 shadow-sm backdrop-blur">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted">Primary lane</p>
                      <h3 className="mt-2 text-lg font-semibold text-ink">{selectedPhase.label}</h3>
                    </div>
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-ink">
                      <SelectedPhaseIcon size={22} aria-hidden="true" />
                    </div>
                  </div>

                  <div className="mt-4 grid gap-3">
                    {overviewMetrics.map((metric) => (
                      <div
                        key={metric.label}
                        className={`rounded-2xl border px-4 py-3 ${toneClasses[metric.tone]}`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-[0.18em] opacity-70">
                              {metric.label}
                            </p>
                            <p className="mt-1 text-2xl font-semibold text-ink">{metric.value}</p>
                          </div>
                          <BadgeCheck size={16} className="mt-1 opacity-70" aria-hidden="true" />
                        </div>
                        <p className="mt-2 text-xs opacity-80">{metric.delta}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <aside className="surface overflow-hidden p-5 shadow-soft">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted">Workflow map</p>
                <h3 className="mt-2 text-xl font-semibold text-ink">System sequence</h3>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-ink text-white">
                <LayoutDashboard size={20} aria-hidden="true" />
              </div>
            </div>

            <div className="mt-5 grid gap-3">
              {workflowPhases.map((phase, index) => {
                const Icon = iconMap[phase.icon as keyof typeof iconMap] ?? Sparkles;
                const isActive = phase.id === selectedPhaseId;

                return (
                  <button
                    key={phase.id}
                    type="button"
                    onClick={() => setSelectedPhaseId(phase.id)}
                    className={`group w-full rounded-3xl border p-4 text-left transition duration-200 ${
                      isActive
                        ? "border-ink bg-ink text-white shadow-soft"
                        : "border-line/70 bg-white/85 text-ink hover:-translate-y-0.5 hover:border-teal-200"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl ${
                          isActive
                            ? "bg-white/10 text-white"
                            : "bg-slate-100 text-ink"
                        }`}
                      >
                        <Icon size={18} aria-hidden="true" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className={`text-xs font-semibold uppercase tracking-[0.18em] ${isActive ? "text-white/70" : "text-muted"}`}>
                              Phase {String(index + 1).padStart(2, "0")}
                            </p>
                            <h4 className="mt-1 text-base font-semibold">{phase.label}</h4>
                          </div>
                          <ArrowRight size={16} className={isActive ? "text-white/75" : "text-muted"} aria-hidden="true" />
                        </div>
                        <p className={`mt-2 text-sm leading-6 ${isActive ? "text-white/80" : "text-muted"}`}>
                          {phase.title}
                        </p>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </aside>
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1.08fr_0.92fr]">
          <div className="surface overflow-hidden shadow-soft">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line/70 px-5 py-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted">Selected phase</p>
                <h3 className="mt-2 text-2xl font-semibold text-ink">{selectedPhase.title}</h3>
              </div>
              <span className="inline-flex items-center gap-2 rounded-full border border-line/70 bg-page px-3 py-1.5 text-xs font-semibold text-muted">
                <CalendarDays size={14} aria-hidden="true" />
                Diagram matched
              </span>
            </div>

            <div className="grid gap-0 md:grid-cols-[1.15fr_0.85fr]">
              <div className="space-y-6 p-5">
                <p className="max-w-2xl text-sm leading-7 text-muted">{selectedPhase.description}</p>

                <div>
                  <p className="text-sm font-semibold text-ink">Backend objects</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {selectedPhase.backend.map((item) => (
                      <span
                        key={item}
                        className="inline-flex rounded-full border border-line/70 bg-page px-3 py-1.5 text-sm text-ink"
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-sm font-semibold text-ink">Frontend actions</p>
                  <div className="mt-3 grid gap-2">
                    {selectedPhase.ui.map((item) => (
                      <div key={item} className="flex items-center gap-3 rounded-2xl border border-line/70 bg-page px-4 py-3">
                        <CheckCircle2 size={16} className="text-teal-600" aria-hidden="true" />
                        <span className="text-sm text-ink">{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="border-t border-line/70 bg-slate-50 p-5 md:border-l md:border-t-0">
                <div className="rounded-3xl border border-line/70 bg-white p-4 shadow-sm">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted">Phase outcome</p>
                      <h4 className="mt-2 text-lg font-semibold text-ink">What the user gets</h4>
                    </div>
                    <BookOpen size={18} className="text-muted" aria-hidden="true" />
                  </div>
                  <p className="mt-3 text-sm leading-7 text-muted">{selectedPhase.outcome}</p>
                </div>

                <div className="mt-4 rounded-3xl border border-line/70 bg-white p-4 shadow-sm">
                  <p className="text-sm font-semibold text-ink">Role access</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {roleTabs.map((role) => (
                      <span key={role} className="rounded-full border border-line/70 bg-page px-3 py-1.5 text-sm text-ink">
                        {role}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mt-4 rounded-3xl border border-line/70 bg-ink p-4 text-white shadow-soft">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/60">Backend flow</p>
                  <div className="mt-4 grid gap-2">
                    {flowNodes.map((node, index) => (
                      <div key={node} className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-sm font-semibold">
                          {String(index + 1)}
                        </div>
                        <div className="flex-1 rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm">
                          {node}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="surface p-5 shadow-soft">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted">Module wise</p>
                <h3 className="mt-2 text-2xl font-semibold text-ink">Backend to frontend map</h3>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-ink text-white">
                <Layers3 size={20} aria-hidden="true" />
              </div>
            </div>

            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              {moduleCards.map((card) => {
                const Icon = moduleIconMap[card.icon as keyof typeof moduleIconMap] ?? Sparkles;

                return (
                  <article
                    key={card.title}
                    className="group rounded-3xl border border-line/70 bg-white p-4 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-soft"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-ink transition group-hover:scale-105">
                        <Icon size={20} aria-hidden="true" />
                      </div>
                      <div className="min-w-0">
                        <h4 className="text-base font-semibold text-ink">{card.title}</h4>
                        <p className="mt-2 text-sm leading-6 text-muted">{card.description}</p>
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2">
                      {card.backend.map((item) => (
                        <span
                          key={item}
                          className="rounded-full border border-line/70 bg-page px-3 py-1 text-xs font-medium text-muted"
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section className="mt-6 grid gap-6 xl:grid-cols-[1.02fr_0.98fr]">
          <div className="surface p-5 shadow-soft">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted">Admin workspace</p>
                <h3 className="mt-2 text-2xl font-semibold text-ink">Operational modules</h3>
              </div>
              <UserRound size={20} className="text-muted" aria-hidden="true" />
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-3">
              {roleTabs.map((role) => (
                <div key={role} className="rounded-3xl border border-line/70 bg-page p-4">
                  <div className="flex items-center justify-between gap-3">
                    <h4 className="text-base font-semibold text-ink">{role}</h4>
                    <BadgeCheck size={16} className="text-teal-600" aria-hidden="true" />
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {roleWorkspaces[role].map((item) => (
                      <span key={item} className="rounded-full border border-line/70 bg-white px-3 py-1.5 text-xs text-ink">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="surface overflow-hidden shadow-soft">
            <div className="flex items-center justify-between gap-3 border-b border-line/70 px-5 py-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted">Student visibility</p>
                <h3 className="mt-2 text-2xl font-semibold text-ink">Read-only student lane</h3>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-ink text-white">
                <Users size={20} aria-hidden="true" />
              </div>
            </div>

            <div className="grid gap-3 p-5">
              {[
                { title: "Student profile", note: "Admission, class, section, status", icon: GraduationCap },
                { title: "Attendance report", note: "Daily / monthly view from AttendanceRecord", icon: ClipboardCheck },
                { title: "Assigned work", note: "Published work and due dates", icon: BookOpen },
                { title: "Results and admit card", note: "Marks, grades, exam schedule, and venue", icon: BadgeCheck }
              ].map((item) => {
                const Icon = item.icon;

                return (
                  <div key={item.title} className="flex items-start gap-3 rounded-2xl border border-line/70 bg-page p-4">
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white text-ink shadow-sm">
                      <Icon size={18} aria-hidden="true" />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-ink">{item.title}</h4>
                      <p className="mt-1 text-sm leading-6 text-muted">{item.note}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        <section className="mt-6 surface p-5 shadow-soft">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted">End-to-end flow</p>
              <h3 className="mt-2 text-2xl font-semibold text-ink">Diagram order from auth to student workspace</h3>
            </div>
            <div className="inline-flex items-center gap-2 rounded-full border border-line/70 bg-page px-3 py-1.5 text-sm text-muted">
              <BarChart3 size={15} aria-hidden="true" />
              Live architecture shell
            </div>
          </div>

          <div className="mt-5 grid gap-3 lg:grid-cols-7">
            {flowNodes.map((node, index) => (
              <div key={node} className="relative rounded-3xl border border-line/70 bg-white p-4 shadow-sm">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">
                    Step {String(index + 1).padStart(2, "0")}
                  </span>
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-ink text-white">
                    {index + 1}
                  </div>
                </div>
                <p className="mt-4 text-sm font-semibold text-ink">{node}</p>
                {index < flowNodes.length - 1 && (
                  <ArrowRight
                    size={18}
                    className="absolute -right-3 top-1/2 hidden -translate-y-1/2 text-muted lg:block"
                    aria-hidden="true"
                  />
                )}
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

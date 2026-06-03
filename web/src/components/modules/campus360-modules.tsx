"use client";

import { useMemo, useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  Filter,
  Layers3,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import {
  campus360Modules,
  moduleAreas,
  modulesForRole,
  permissionLabel,
  roleDefinitions,
  roleDefinitionFor,
  statusLabel,
  type Campus360ModuleArea,
  type Campus360ModuleStatus,
  type Campus360PermissionLevel,
} from "@/lib/campus360-modules";
import { useAuth } from "@/lib/auth-context";
import { Badge } from "@/components/ui/badge";

type ModuleTargetTab = "dashboard" | "modules" | "records" | "campus" | "attendance" | "academics" | "fees" | "reports" | "student";

const statusTone: Record<Campus360ModuleStatus, string> = {
  live: "border-emerald-200 bg-emerald-50 text-emerald-700",
  configured: "border-blue-200 bg-blue-50 text-blue-700",
  foundation: "border-amber-200 bg-amber-50 text-amber-700",
};

const permissionTone: Record<Campus360PermissionLevel | "none", string> = {
  manage: "border-blue-200 bg-blue-50 text-blue-700",
  operate: "border-emerald-200 bg-emerald-50 text-emerald-700",
  view: "border-slate-200 bg-slate-50 text-slate-700",
  none: "border-rose-200 bg-rose-50 text-rose-700",
};

const areaTone: Record<Campus360ModuleArea, string> = {
  Admissions: "bg-blue-50 text-blue-800 border-blue-200",
  People: "bg-slate-50 text-slate-800 border-slate-200",
  Academics: "bg-blue-50 text-blue-800 border-blue-200",
  Operations: "bg-slate-50 text-slate-800 border-slate-200",
  Finance: "bg-emerald-50 text-emerald-800 border-emerald-200",
  Services: "bg-slate-50 text-slate-800 border-slate-200",
  Leadership: "bg-blue-50 text-blue-800 border-blue-200",
  Security: "bg-rose-50 text-rose-800 border-rose-200",
};

function roleName(role?: string) {
  if (!role) return "Role";
  if (role === "super_admin") return "Super Admin";
  return role
    .split("_")
    .map((part) => part[0]?.toUpperCase() + part.slice(1))
    .join(" ");
}

function workflowTarget(module: { id: string; area: Campus360ModuleArea }): ModuleTargetTab {
  if (module.id === "attendance-management") return "attendance";
  if (module.id === "fees-management") return "fees";
  if (module.id === "analytics-reports" || module.id === "director-dashboard") return "reports";
  if (module.id === "security-access-control" || module.id === "staff-employee-management") return "campus";
  if (module.area === "Admissions" || module.area === "People") return "records";
  if (module.area === "Academics") return "academics";
  if (module.area === "Finance") return "fees";
  if (module.area === "Leadership") return "reports";
  if (module.area === "Operations") return "attendance";
  return "modules";
}

export function Campus360Modules({
  allowedTabs = [],
  onNavigate,
}: {
  allowedTabs?: string[];
  onNavigate?: (tab: ModuleTargetTab) => void;
}) {
  const { user } = useAuth();
  const [query, setQuery] = useState("");
  const [area, setArea] = useState<Campus360ModuleArea | "all">("all");
  const [status, setStatus] = useState<Campus360ModuleStatus | "all">("all");
  const [scope, setScope] = useState<"role" | "all">("role");
  const [selectedModuleId, setSelectedModuleId] = useState<string | null>(null);

  const roleModules = useMemo(() => (user ? modulesForRole(user.role) : campus360Modules), [user]);
  const currentRole = user ? roleDefinitionFor(user.role) : undefined;
  const visibleModules = useMemo(() => {
    const source = scope === "role" ? roleModules : campus360Modules;
    const term = query.trim().toLowerCase();
    return source.filter((module) => {
      const matchesQuery = !term
        || module.title.toLowerCase().includes(term)
        || module.summary.toLowerCase().includes(term)
        || module.features.some((feature) => feature.toLowerCase().includes(term));
      const matchesArea = area === "all" || module.area === area;
      const matchesStatus = status === "all" || module.status === status;
      return matchesQuery && matchesArea && matchesStatus;
    });
  }, [area, query, roleModules, scope, status]);

  const counts = useMemo(() => ({
    all: campus360Modules.length,
    role: roleModules.length,
    live: campus360Modules.filter((module) => module.status === "live").length,
    configured: campus360Modules.filter((module) => module.status === "configured").length,
    foundation: campus360Modules.filter((module) => module.status === "foundation").length,
  }), [roleModules.length]);
  const roleCounts = useMemo(() => (
    roleDefinitions.map((role) => ({
      ...role,
      modules: modulesForRole(role.role).length,
    }))
  ), []);
  const selectedModule = useMemo(
    () => campus360Modules.find((module) => module.id === selectedModuleId) ?? null,
    [selectedModuleId],
  );

  return (
    <div className="space-y-6">
      <section className="surface overflow-hidden p-5 md:p-6">
        <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
          <div>
            <span className="section-kicker">
              <Layers3 size={14} />
              Modules
            </span>
            <h1 className="mt-4 text-3xl font-semibold tracking-tight text-ink md:text-4xl">
              Modules you can use
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-muted">
              This list is based on your role. Each module shows who owns it, what it includes, and your access level.
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-line/70 bg-white px-3 py-1 text-xs font-semibold capitalize text-muted">
                <ShieldCheck size={13} />
                Your access: {roleName(user?.role)}
              </span>
              <span className="rounded-full border border-line/70 bg-white px-3 py-1 text-xs font-semibold text-muted">
                {counts.role} modules you can use
              </span>
              <span className="rounded-full border border-line/70 bg-white px-3 py-1 text-xs font-semibold text-muted">
                {counts.all} total
              </span>
              {currentRole && (
                <span className="rounded-full border border-line/70 bg-white px-3 py-1 text-xs font-semibold text-muted">
                  {currentRole.access}
                </span>
              )}
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
            {[
              { label: "Ready", value: counts.live, icon: CheckCircle2 },
              { label: "Setup", value: counts.configured, icon: Sparkles },
              { label: "Planned", value: counts.foundation, icon: Layers3 },
            ].map(({ label, value, icon: Icon }) => (
              <div key={label} className="rounded-lg border border-line/70 bg-slate-50/80 px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">{label}</p>
                    <p className="mt-1 text-2xl font-semibold text-ink">{value}</p>
                  </div>
                  <span className="flex h-10 w-10 items-center justify-center rounded-md bg-white text-ink shadow-sm">
                    <Icon size={17} />
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="surface p-5">
          <div className="flex items-center gap-2">
            <Users size={17} className="text-accent" />
            <h2 className="font-semibold text-ink">Roles and responsibility</h2>
          </div>
          <div className="mt-4 grid gap-3">
            {roleCounts.map((role) => (
              <div
                key={role.role}
                className={`rounded-lg border px-4 py-3 ${
                  user?.role === role.role ? "border-blue-200 bg-blue-50/70" : "border-line/70 bg-white"
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-semibold text-ink">{role.label}</p>
                  <span className="rounded-md border border-line/70 bg-white px-2 py-0.5 text-xs font-semibold text-muted">
                    {role.modules} modules
                  </span>
                </div>
                <p className="mt-1 text-xs font-semibold uppercase tracking-[0.14em] text-muted">{role.access}</p>
                <p className="mt-2 text-sm leading-6 text-muted">{role.responsibility}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="surface p-5">
          <div className="flex items-center gap-2">
            <ShieldCheck size={17} className="text-accent" />
            <h2 className="font-semibold text-ink">Build standard</h2>
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {[
              ["Frontend", "Next.js, TypeScript, Tailwind CSS"],
              ["Backend", "Django REST API, SimpleJWT"],
              ["UI elements", "Forms, tables, filters, cards, dialogs, support panel"],
              ["Icons", "Lucide React icons for modules and actions"],
            ].map(([label, value]) => (
              <div key={label} className="rounded-lg border border-line/70 bg-white px-4 py-3">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">{label}</p>
                <p className="mt-1 text-sm font-semibold text-ink">{value}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="surface p-4">
        <div className="grid gap-3 lg:grid-cols-[1fr_auto_auto_auto] lg:items-center">
          <div className="relative">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search modules, features, or workflows"
              className="w-full rounded-lg border border-line/80 bg-white py-2.5 pl-9 pr-3 text-sm text-ink outline-none"
            />
          </div>

          <label className="flex w-full items-center gap-2 rounded-lg border border-line/70 bg-white px-3 py-2 text-sm text-muted lg:w-auto">
            <Filter size={15} />
            <select
              value={area}
              onChange={(event) => setArea(event.target.value as Campus360ModuleArea | "all")}
              className="min-h-0 min-w-0 flex-1 border-0 bg-transparent p-0 text-sm font-medium text-ink outline-none lg:flex-none"
            >
              <option value="all">All groups</option>
              {moduleAreas.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </label>

          <select
            value={status}
            onChange={(event) => setStatus(event.target.value as Campus360ModuleStatus | "all")}
            className="w-full rounded-lg border border-line/70 bg-white px-3 py-2 text-sm font-medium text-ink outline-none lg:w-auto"
          >
            <option value="all">All stages</option>
            <option value="live">Ready</option>
            <option value="configured">Setup</option>
            <option value="foundation">Planned</option>
          </select>

          <div className="grid grid-cols-2 rounded-lg border border-line/70 bg-white p-1 lg:inline-flex">
            {[
              { id: "role", label: "Permitted" },
              { id: "all", label: "All" },
            ].map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setScope(item.id as "role" | "all")}
                className={`h-8 rounded-md px-3 text-xs font-semibold transition ${
                  scope === item.id ? "bg-ink text-white" : "text-muted hover:bg-slate-50 hover:text-ink"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {visibleModules.map((module) => {
          const Icon = module.icon;
          const target = workflowTarget(module);
          const permission = user ? module.permissions[user.role] : undefined;
          const canOpenWorkflow = Boolean(permission && onNavigate && allowedTabs.includes(target));
          return (
            <article key={module.id} className="surface flex flex-col p-4 shadow-sm sm:p-5 md:min-h-[22rem]">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex min-w-0 items-center gap-3">
                  <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-ink text-white">
                    <Icon size={19} />
                  </span>
                  <div className="min-w-0">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">
                      Module {String(module.number).padStart(2, "0")}
                    </p>
                    <h2 className="mt-1 text-base font-semibold text-ink">{module.title}</h2>
                  </div>
                </div>
                <span className={`w-fit rounded-full border px-2.5 py-1 text-xs font-semibold ${statusTone[module.status]}`}>
                  {statusLabel(module.status)}
                </span>
              </div>

              <p className="mt-4 text-sm leading-6 text-muted">{module.summary}</p>
              <div className="mt-4 grid gap-3 rounded-lg border border-line/70 bg-slate-50/80 p-3">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">Owner</p>
                  <p className="mt-1 text-sm font-semibold text-ink">{module.owner}</p>
                </div>
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">Responsibility</p>
                  <p className="mt-1 text-sm leading-6 text-muted">{module.responsibility}</p>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${areaTone[module.area]}`}>
                  {module.area}
                </span>
                {user && (
                  <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${permissionTone[module.permissions[user.role] ?? "none"]}`}>
                    {permissionLabel(module.permissions[user.role])}
                  </span>
                )}
                {module.roles.slice(0, 3).map((role) => (
                  <Badge key={role} variant="neutral">{roleName(role)}</Badge>
                ))}
                {module.roles.length > 3 && <Badge variant="neutral">+{module.roles.length - 3}</Badge>}
              </div>

              <div className="mt-5 flex-1">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">What it includes</p>
                <ul className="mt-3 grid gap-2">
                  {module.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm leading-6 text-ink">
                      <CheckCircle2 size={15} className="mt-1 shrink-0 text-teal-700" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mt-5">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Screen elements</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {module.components.map((component) => (
                    <span key={component} className="rounded-md border border-line/70 bg-slate-50 px-2 py-1 text-xs font-medium text-muted">
                      {component}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-5 grid gap-2 border-t border-line/60 pt-4 sm:grid-cols-2">
                <button
                  type="button"
                  onClick={() => setSelectedModuleId(module.id)}
                  className="inline-flex h-10 items-center justify-center rounded-lg border border-line/70 bg-white px-3 text-xs font-semibold uppercase tracking-[0.12em] text-muted hover:bg-slate-50 hover:text-ink"
                >
                  Details
                </button>
                <button
                  type="button"
                  onClick={() => canOpenWorkflow ? onNavigate?.(target) : setSelectedModuleId(module.id)}
                  className={`inline-flex h-10 items-center justify-center gap-2 rounded-lg px-3 text-xs font-semibold uppercase tracking-[0.12em] ${
                    canOpenWorkflow
                      ? "bg-ink text-white hover:bg-slate-900"
                      : "border border-line/70 bg-slate-50 text-muted hover:bg-white hover:text-ink"
                  }`}
                >
                  {canOpenWorkflow ? "Open" : "Checklist"}
                  <ArrowRight size={15} />
                </button>
              </div>
            </article>
          );
        })}
      </section>

      {visibleModules.length === 0 && (
        <section className="surface px-5 py-12 text-center">
          <p className="font-semibold text-ink">No modules found.</p>
          <p className="mt-2 text-sm text-muted">Clear search or choose all groups.</p>
        </section>
      )}

      {selectedModule && (
        <section className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/50 p-2 backdrop-blur-sm sm:items-center sm:p-4">
          <div className="max-h-[calc(100dvh-1rem)] w-full max-w-3xl overflow-hidden rounded-lg border border-line/70 bg-white shadow-2xl">
            <div className="flex items-start justify-between gap-4 border-b border-line/70 bg-slate-50 px-5 py-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Module {String(selectedModule.number).padStart(2, "0")}</p>
                <h2 className="mt-1 text-xl font-semibold text-ink">{selectedModule.title}</h2>
              </div>
              <button type="button" onClick={() => setSelectedModuleId(null)} className="rounded-lg border border-line/70 bg-white px-3 py-2 text-sm font-semibold text-ink hover:bg-slate-50">
                Close
              </button>
            </div>
            <div className="max-h-[calc(100dvh-6rem)] overflow-y-auto p-5">
              <div className="grid gap-4 md:grid-cols-[0.85fr_1.15fr]">
                <div className="rounded-lg border border-line/70 bg-slate-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Owner</p>
                  <p className="mt-1 font-semibold text-ink">{selectedModule.owner}</p>
                  <p className="mt-4 text-xs font-semibold uppercase tracking-[0.16em] text-muted">Stage</p>
                  <p className="mt-1 text-sm text-ink">{statusLabel(selectedModule.status)}</p>
                  <p className="mt-4 text-xs font-semibold uppercase tracking-[0.16em] text-muted">Access</p>
                  <p className="mt-1 text-sm text-ink">{user ? permissionLabel(selectedModule.permissions[user.role]) : "Login required"}</p>
                </div>
                <div>
                  <p className="text-sm leading-7 text-muted">{selectedModule.summary}</p>
                  <p className="mt-4 text-sm font-semibold text-ink">Workflow checklist</p>
                  <div className="mt-3 grid gap-2">
                    {selectedModule.features.map((feature) => (
                      <div key={feature} className="flex items-start gap-2 rounded-lg border border-line/70 bg-white px-3 py-2 text-sm text-ink">
                        <CheckCircle2 size={15} className="mt-0.5 shrink-0 text-teal-700" />
                        <span>{feature}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-5 rounded-lg border border-line/70 bg-white p-4">
                <p className="text-sm font-semibold text-ink">Screen elements required</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {selectedModule.components.map((component) => (
                    <span key={component} className="rounded-md border border-line/70 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-muted">
                      {component}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

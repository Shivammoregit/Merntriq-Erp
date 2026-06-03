"use client";

import { useMemo, useState } from "react";
import {
  BarChart3,
  BookOpen,
  BriefcaseBusiness,
  ClipboardCheck,
  GraduationCap,
  Layers3,
  LayoutDashboard,
  ReceiptText,
  School,
  ShieldCheck,
  Users,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { LoginPage } from "@/components/auth/login-page";
import { Topbar } from "@/components/layout/topbar";
import { AcademicManagementPanel } from "@/components/academics/academic-management-panel";
import { AdminDashboard } from "@/components/admin/admin-dashboard";
import { AttendancePanel } from "@/components/attendance/attendance-panel";
import { CampusControlPanel } from "@/components/campus/campus-control-panel";
import { InstitutionOverview } from "@/components/dashboard/institution-overview";
import { FeesPaymentsDashboard } from "@/components/fees/fees-payments-dashboard";
import { Campus360Modules } from "@/components/modules/campus360-modules";
import { ReportsDashboard } from "@/components/reports/reports-dashboard";
import { SchoolOperationsPanel } from "@/components/operations/school-operations-panel";
import { StudentDashboard } from "@/components/student/student-dashboard";
import { SupportDock } from "@/components/support/support-dock";
import type { User, UserCampusScope } from "@/lib/api";

export type AppTab = "dashboard" | "modules" | "records" | "campus" | "attendance" | "operations" | "academics" | "fees" | "reports" | "student";
type AppDomain = "command" | "suite" | "administration" | "governance" | "operations" | "academics" | "finance" | "learner";

type NavItem = {
  id: AppTab;
  label: string;
  domain: AppDomain;
  domainLabel: string;
  responsibility: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
};

const APP_NAV: NavItem[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    domain: "command",
    domainLabel: "Academic",
    responsibility: "Overview and quick status",
    icon: LayoutDashboard,
  },
  {
    id: "modules",
    label: "Modules",
    domain: "suite",
    domainLabel: "Academic",
    responsibility: "Available ERP modules",
    icon: Layers3,
  },
  {
    id: "records",
    label: "Student Info",
    domain: "administration",
    domainLabel: "Academic",
    responsibility: "Students, classes, and users",
    icon: Users,
  },
  {
    id: "campus",
    label: "Administration",
    domain: "governance",
    domainLabel: "Academic",
    responsibility: "Access, devices, and approvals",
    icon: ShieldCheck,
  },
  {
    id: "attendance",
    label: "Attendance",
    domain: "operations",
    domainLabel: "Academic",
    responsibility: "Mark and review presence",
    icon: ClipboardCheck,
  },
  {
    id: "operations",
    label: "Operations",
    domain: "operations",
    domainLabel: "Operations",
    responsibility: "Staff, timetable, library, transport, and hostel",
    icon: BriefcaseBusiness,
  },
  {
    id: "academics",
    label: "LMS",
    domain: "academics",
    domainLabel: "LMS",
    responsibility: "Work, resources, and results",
    icon: BookOpen,
  },
  {
    id: "fees",
    label: "Pay Online",
    domain: "finance",
    domainLabel: "Pay Online",
    responsibility: "Fees and payments",
    icon: ReceiptText,
  },
  {
    id: "reports",
    label: "Examination",
    domain: "governance",
    domainLabel: "Examination",
    responsibility: "Reports and activity log",
    icon: BarChart3,
  },
  {
    id: "student",
    label: "Student Info",
    domain: "learner",
    domainLabel: "Academic",
    responsibility: "Student records and updates",
    icon: GraduationCap,
  },
];

function hasCampusRole(user: User, roles: UserCampusScope["role"][]) {
  return user.campuses?.some((campus) => roles.includes(campus.role)) ?? false;
}

function hasMembershipFlag(user: User, key: "can_manage_users" | "can_configure_attendance") {
  return user.campuses?.some((campus) => Boolean(campus[key])) ?? false;
}

function canAccessTab(user: User, tab: AppTab) {
  if (tab === "modules") return true;
  if (user.role === "super_admin") return tab !== "student";
  if (user.role === "student" || user.role === "parent") return tab === "student";
  if (user.role === "teacher") return ["dashboard", "attendance", "operations", "academics"].includes(tab);
  if (user.role !== "admin") return false;

  const isItAdmin = hasCampusRole(user, ["it_admin"]);
  const isAcademicAdmin = hasCampusRole(user, ["academic_admin"]);
  const isFinanceAdmin = hasCampusRole(user, ["finance_admin"]);
  const canManageUsers = hasMembershipFlag(user, "can_manage_users");
  const canConfigureAttendance = hasMembershipFlag(user, "can_configure_attendance");

  if (tab === "dashboard") return true;
  if (tab === "records") return isItAdmin || isAcademicAdmin || canManageUsers;
  if (tab === "campus") return isItAdmin || canManageUsers || canConfigureAttendance;
  if (tab === "attendance") return isItAdmin || isAcademicAdmin || canConfigureAttendance;
  if (tab === "operations") return true;
  if (tab === "academics") return isItAdmin || isAcademicAdmin;
  if (tab === "fees") return isItAdmin || isFinanceAdmin;
  if (tab === "reports") return isItAdmin || isFinanceAdmin;
  return false;
}

function roleDisplayName(user: User) {
  if (user.role === "super_admin") return "Super Admin";
  if (user.role === "parent") return "Parent / Guardian";
  return user.role
    .split("_")
    .map((part) => part[0]?.toUpperCase() + part.slice(1))
    .join(" ");
}

function accessScopeLabel(user: User, navItems: NavItem[]) {
  if (user.role === "super_admin") return "You can manage the full institution and every campus.";
  if (user.role === "teacher") return "You can manage attendance, class work, resources, and results for your classes.";
  if (user.role === "student") return "You can view your attendance, work, results, fees, and admit cards.";
  if (user.role === "parent") return "You can view linked student attendance, work, results, fees, transport, hostel, and school notices.";
  const scopes = user.campuses?.map((campus) => `${campus.code} ${campus.role.replace("_", " ")}`) ?? [];
  return scopes.length
    ? `You can use ${navItems.length} page${navItems.length === 1 ? "" : "s"} for ${scopes.join(", ")}.`
    : "You have campus-level access assigned by the organization.";
}

function accessPolicyLabel(user: User) {
  if (user.role === "super_admin") return "Full access";
  if (user.role === "admin") return "Admin access";
  if (user.role === "teacher") return "Teacher access";
  if (user.role === "parent") return "Family view";
  return "Student view";
}

function personalizeNavItem(item: NavItem, user: User): NavItem {
  if (user.role === "parent" && item.id === "student") {
    return {
      ...item,
      label: "Family Portal",
      responsibility: "Linked student records and updates",
    };
  }
  return item;
}

export function AppShell() {
  const { user, loading } = useAuth();
  const [activeTab, setActiveTab] = useState<AppTab | null>(null);

  const navItems = useMemo(() => {
    if (!user) return [];
    return APP_NAV
      .filter((item) => canAccessTab(user, item.id))
      .map((item) => personalizeNavItem(item, user));
  }, [user]);

  const allowedTabIds = useMemo(() => navItems.map((item) => item.id), [navItems]);
  const defaultTab = user && (user.role === "student" || user.role === "parent")
    ? navItems.find((item) => item.id === "student")?.id ?? navItems[0]?.id ?? ""
    : navItems[0]?.id ?? "";
  const currentTab = navItems.some((item) => item.id === activeTab) ? activeTab ?? "" : defaultTab;
  const canOpen = (tab: AppTab) => Boolean(user && currentTab === tab && canAccessTab(user, tab));
  const primaryCampus = user?.campuses?.find((campus) => campus.is_primary) ?? user?.campuses?.[0];
  const campusName = user?.role === "super_admin" ? "All campuses" : primaryCampus?.name ?? "Campus not assigned";
  const accessMode = user?.role === "student" || user?.role === "parent" ? "Read-only" : "Operational";

  if (loading) return null;

  if (!user) return <LoginPage />;

  return (
    <div className="modern-shell min-h-screen">
      <Topbar navItems={navItems} activeTab={currentTab} onTabChange={(id) => setActiveTab(id as AppTab)} />

      <main className="page-shell pb-28 pt-4 md:pt-5">
        {!activeTab && (
          <section className="mb-6 grid gap-4 xl:grid-cols-[1.35fr_0.65fr]">
            <div className="surface overflow-hidden p-5 md:p-6">
              <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
                <div className="min-w-0">
                  <span className="section-kicker">
                    <School size={14} />
                    {campusName}
                  </span>
                  <h1 className="display-font mt-4 text-2xl font-semibold tracking-tight text-ink md:text-3xl">
                    Welcome, {user.full_name || user.username}
                  </h1>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
                    {accessScopeLabel(user, navItems)}
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className="inline-flex items-center rounded-md border border-line/70 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-muted">
                      You can use
                    </span>
                    {navItems.map((item) => {
                      const Icon = item.icon;
                      return (
                        <span key={item.id} className="inline-flex items-center gap-1.5 rounded-md border border-line/70 bg-white px-2.5 py-1 text-xs font-semibold text-muted">
                          <Icon size={13} />
                          {item.label}
                        </span>
                      );
                    })}
                  </div>
                </div>

                <div className="flex shrink-0 items-center gap-3 rounded-lg border border-line/70 bg-slate-50/80 px-4 py-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-accent text-base font-bold text-white shadow-sm">
                    {user.full_name?.[0]?.toUpperCase() ?? user.username[0]?.toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-ink">{roleDisplayName(user)}</p>
                    <p className="truncate text-xs capitalize text-muted">{accessMode} ERP session</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
              {[
                {
                  label: "Campus",
                  value: user.role === "super_admin" ? "Network" : `${user.campuses?.length ?? 0} campus${(user.campuses?.length ?? 0) === 1 ? "" : "es"}`,
                  icon: School,
                },
                {
                  label: "Pages",
                  value: navItems.length,
                  icon: LayoutDashboard,
                },
                {
                  label: "Role",
                  value: accessPolicyLabel(user),
                  icon: ShieldCheck,
                },
              ].map(({ label, value, icon: Icon }) => (
                <div key={label} className="surface flex items-center justify-between gap-3 px-4 py-3">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">{label}</p>
                    <p className="mt-1 text-base font-semibold text-ink">{value}</p>
                  </div>
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-ink">
                    <Icon size={17} />
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {currentTab === "dashboard" && (user.role === "admin" || user.role === "super_admin" || user.role === "teacher") && (
          <InstitutionOverview
            role={user.role}
            allowedTabs={allowedTabIds}
            onNavigate={(tab) => {
              const target = (tab === "finance" ? "fees" : tab) as AppTab;
              if (canAccessTab(user, target)) setActiveTab(target);
            }}
          />
        )}
        {canOpen("modules") && (
          <Campus360Modules
            allowedTabs={allowedTabIds}
            onNavigate={(tab) => {
              if (canAccessTab(user, tab)) setActiveTab(tab);
            }}
          />
        )}
        {canOpen("records") && <AdminDashboard />}
        {canOpen("campus") && <CampusControlPanel />}
        {canOpen("attendance") && <AttendancePanel />}
        {canOpen("operations") && <SchoolOperationsPanel />}
        {canOpen("academics") && <AcademicManagementPanel />}
        {canOpen("fees") && <FeesPaymentsDashboard />}
        {canOpen("reports") && <ReportsDashboard />}
        {canOpen("student") && <StudentDashboard />}
      </main>
      <SupportDock />
      <footer className="erp-footer">
        (c) 2026 <strong>MentriQ360</strong>. All Rights Reserved.
      </footer>
    </div>
  );
}


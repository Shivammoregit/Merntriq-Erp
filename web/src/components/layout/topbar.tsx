"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  Bell,
  Building2,
  CalendarClock,
  ChevronDown,
  Check,
  CheckCheck,
  Grid3X3,
  Info,
  LogOut,
  Megaphone,
  Menu,
  MessageSquareWarning,
  Plus,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { BrandLogo } from "@/components/brand-logo";
import {
  announcementApi,
  supportTicketApi,
  type Announcement as ApiAnnouncement,
  type SupportTicket,
} from "@/lib/api";

const ROLE_COLOUR: Record<string, string> = {
  super_admin: "border-emerald-200 bg-emerald-50 text-emerald-700",
  admin: "border-blue-200 bg-blue-50 text-blue-700",
  account: "border-emerald-200 bg-emerald-50 text-emerald-700",
  teacher: "border-slate-200 bg-slate-50 text-slate-700",
  student: "border-slate-200 bg-slate-50 text-slate-700",
};

const FAQ_ITEMS = [
  {
    question: "Can I use one email address for multiple admission forms?",
    answer: "Yes. The student admission number remains the unique student identity. The same guardian email can be recorded on multiple student records.",
  },
  {
    question: "Is registration required before submitting an online admission form?",
    answer: "Yes. A login account keeps admission, document upload, approval, and class allocation traceable in the ERP audit flow.",
  },
  {
    question: "Can I use one mobile number for multiple student forms?",
    answer: "Yes. The same guardian mobile number can be reused for siblings while each student keeps a separate admission profile.",
  },
  {
    question: "Where can I check attendance, fees, homework, and results?",
    answer: "Students use the learner portal, including the parent view. Staff use Attendance, Pay Online, LMS, and Examination modules according to their role.",
  },
  {
    question: "How can I send a problem or message to support?",
    answer: "Use the Support button at the bottom of the ERP. The request goes to the super admin queue with category, priority, campus, and message.",
  },
  {
    question: "How do I correct student details after admission?",
    answer: "An admin with Student Info permission can edit student details from the Student Info module and the change is stored through the backend API.",
  },
];

interface NavItem {
  id: string;
  label: string;
  domainLabel?: string;
  responsibility?: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
}

type NotificationItem = {
  id: string;
  title: string;
  message: string;
  priority: "high" | "normal";
  time: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
};

function accessLabel(role?: string) {
  if (role === "super_admin") return "Full access";
  if (role === "admin") return "School admin";
  if (role === "account") return "Account access";
  if (role === "teacher") return "Teacher access";
  if (role === "student") return "Student view";
  return "Limited access";
}

function announcementTone(priority: NotificationItem["priority"]) {
  return priority === "high"
    ? "border-amber-200 bg-amber-50 text-amber-800"
    : "border-blue-200 bg-blue-50 text-blue-800";
}

function formatNotificationTime(value?: string) {
  if (!value) return "Today";
  try {
    return new Intl.DateTimeFormat("en", { day: "2-digit", month: "short" }).format(new Date(value));
  } catch {
    return "Today";
  }
}

export function Topbar({
  navItems,
  activeTab,
  onTabChange,
}: {
  navItems: NavItem[];
  activeTab: string;
  onTabChange: (id: string) => void;
}) {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const [launcherOpen, setLauncherOpen] = useState(false);
  const [faqOpen, setFaqOpen] = useState(false);
  const [activeFaqIndex, setActiveFaqIndex] = useState<number | null>(0);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [openDomain, setOpenDomain] = useState<string | null>(null);
  const [readAnnouncementIds, setReadAnnouncementIds] = useState<Set<string>>(new Set());
  const [remoteAnnouncements, setRemoteAnnouncements] = useState<ApiAnnouncement[]>([]);
  const [supportIssues, setSupportIssues] = useState<SupportTicket[]>([]);
  const [notificationError, setNotificationError] = useState("");

  const currentRole = user?.role;
  const roleLabel = currentRole?.replace("_", " ") ?? "";
  const roleColour = ROLE_COLOUR[currentRole ?? ""] ?? "border-slate-200 bg-slate-50 text-slate-600";
  const primaryScope = user?.campuses?.find((campus) => campus.is_primary) ?? user?.campuses?.[0];
  const campusLabel = user?.role === "super_admin"
    ? "All campuses"
    : primaryScope?.name ?? "Campus not assigned";
  const scopeLabel = user?.role === "super_admin"
    ? "all campuses"
    : primaryScope?.role ? primaryScope.role.replace("_", " ") : roleLabel;
  const groupedNav = useMemo(() => {
    const groups: { label: string; items: NavItem[] }[] = [];
    navItems.forEach((item) => {
      const label = item.domainLabel ?? "Workspace";
      const existing = groups.find((group) => group.label === label);
      if (existing) existing.items.push(item);
      else groups.push({ label, items: [item] });
    });
    return groups;
  }, [navItems]);
  const activeDomain = groupedNav.find((group) => group.items.some((item) => item.id === activeTab));
  const searchResults = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();
    if (!term) return navItems;
    return navItems.filter((item) =>
      [item.label, item.domainLabel, item.responsibility]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(term),
    );
  }, [navItems, searchTerm]);

  useEffect(() => {
    if (!user) return;
    let active = true;
    setNotificationError("");

    const supportPromise = user.role === "super_admin"
      ? supportTicketApi.list({ status: "open" })
      : Promise.resolve<SupportTicket[]>([]);

    Promise.all([announcementApi.list(), supportPromise])
      .then(([apiAnnouncements, apiSupportIssues]) => {
        if (!active) return;
        setRemoteAnnouncements(apiAnnouncements);
        setSupportIssues(apiSupportIssues);
      })
      .catch(() => {
        if (active) setNotificationError("Unable to sync live notifications.");
      });

    return () => {
      active = false;
    };
  }, [user]);

  const announcements = useMemo<NotificationItem[]>(() => {
    const items: NotificationItem[] = [
      ...remoteAnnouncements.map((item) => ({
        id: `announcement-${item.id}`,
        title: item.title,
        message: item.message,
        priority: "normal" as const,
        time: formatNotificationTime(item.publish_on || item.created_at),
        icon: Megaphone,
      })),
      ...supportIssues.map((ticket) => ({
        id: `support-${ticket.id}`,
        title: `Support issue: ${ticket.subject}`,
        message: `${ticket.created_by_name} raised a ${ticket.priority} ${ticket.category.replace("_", " ")} request.`,
        priority: ticket.priority === "normal" ? "normal" as const : "high" as const,
        time: formatNotificationTime(ticket.created_at),
        icon: MessageSquareWarning,
      })),
      {
        id: "campus-context",
        title: currentRole === "super_admin" ? "Network-wide campus view" : "Campus workspace active",
        message: currentRole === "super_admin"
          ? "You are viewing all campuses. Use campus filters before bulk actions or exports."
          : `${campusLabel} is your active ERP workspace for permitted modules.`,
        priority: "high",
        time: "Now",
        icon: Building2,
      },
      {
        id: "session-security",
        title: "Session security enabled",
        message: "Inactive sessions are automatically signed out to protect student and institutional data.",
        priority: "normal",
        time: "Today",
        icon: ShieldCheck,
      },
    ];

    if (currentRole === "super_admin" || currentRole === "admin") {
      items.push({
        id: "bulk-excel",
        title: "Bulk upload and Excel export",
        message: "Student and teacher bulk upload, templates, and Excel export are available inside Registry.",
        priority: "high",
        time: "Today",
        icon: Megaphone,
      });
    }

    if (currentRole === "teacher") {
      items.push({
        id: "attendance-window",
        title: "Attendance edit window",
        message: "Attendance can be updated only for today and the previous 3 days.",
        priority: "high",
        time: "Today",
        icon: CalendarClock,
      });
    }

    if (currentRole === "student") {
      items.push({
        id: "learner-updates",
        title: "Student and parent view available",
        message: "Attendance, assigned work, results, resources, fees, and admit cards are available in the student portal.",
        priority: "normal",
        time: "Today",
        icon: Info,
      });
    }

    return items;
  }, [campusLabel, currentRole, remoteAnnouncements, supportIssues]);
  const unreadAnnouncements = announcements.filter((item) => !readAnnouncementIds.has(item.id));

  function navigate(id: string) {
    onTabChange(id);
    setOpenDomain(null);
    setMenuOpen(false);
    setNotificationOpen(false);
    setLauncherOpen(false);
    setFaqOpen(false);
    setSearchOpen(false);
  }

  function openSupportPanel() {
    window.dispatchEvent(new CustomEvent("mentriq360-open-support"));
    setSearchOpen(false);
    setNotificationOpen(false);
    setLauncherOpen(false);
    setFaqOpen(false);
  }

  return (
    <header className="mastersoft-topbar sticky top-0 z-40">
      <div className="flex min-h-[50px] w-full items-center justify-between gap-2 px-2 sm:gap-3 sm:px-3">
        <div className="flex min-w-0 shrink items-center gap-3 sm:gap-4">
          <BrandLogo
            className="hidden sm:flex"
            logoUrl={primaryScope?.logo_url}
            label={primaryScope?.name ?? "Mentriq360"}
            subtitle={primaryScope?.code ?? "Campus ERP"}
          />
          <BrandLogo
            compact
            className="sm:hidden"
            logoUrl={primaryScope?.logo_url}
            label={primaryScope?.name ?? "Mentriq360"}
            subtitle={primaryScope?.code ?? "Campus ERP"}
          />
        </div>

        <nav className="hidden min-w-0 flex-1 items-center justify-start gap-1 overflow-visible px-2 md:flex" aria-label="Main navigation">
          {groupedNav.map((group) => (
            <div key={group.label} className="relative">
              {group.items.length === 1 ? (
                group.items.map(({ id, label, responsibility, icon: Icon }) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => navigate(id)}
                  title={responsibility}
                  aria-current={activeTab === id ? "page" : undefined}
                  className={`group flex h-9 items-center gap-1.5 whitespace-nowrap rounded-md px-3 text-[15px] font-medium transition ${
                    activeTab === id
                      ? "bg-accent-soft text-accent-strong shadow-sm"
                      : "text-slate-600 hover:bg-slate-100 hover:text-ink"
                  }`}
                >
                  <Icon size={15} className={activeTab === id ? "text-accent-strong" : "text-slate-500 group-hover:text-ink"} />
                  {label}
                </button>
                ))
              ) : (
                <>
                  <button
                    type="button"
                    onClick={() => {
                      setOpenDomain((current) => current === group.label ? null : group.label);
                      setNotificationOpen(false);
                      setUserMenuOpen(false);
                      setLauncherOpen(false);
                      setFaqOpen(false);
                    }}
                    aria-expanded={openDomain === group.label}
                    className={`group flex h-9 items-center gap-1.5 whitespace-nowrap rounded-md px-3 text-[15px] font-medium transition duration-200 ease-out ${
                      activeDomain?.label === group.label
                        ? "bg-accent-soft text-accent-strong shadow-sm"
                        : "text-slate-600 hover:bg-slate-100 hover:text-ink"
                    }`}
                  >
                    <ShieldCheck size={15} className={activeDomain?.label === group.label ? "text-accent-strong" : "text-slate-500 group-hover:text-ink"} />
                    {group.label}
                    <ChevronDown size={14} className={`transition ${openDomain === group.label ? "rotate-180" : ""}`} />
                  </button>
                  {openDomain === group.label && (
                    <div className="absolute left-0 top-full z-30 mt-2 w-[min(18rem,calc(100vw-1rem))] rounded-lg border border-line/70 bg-white/95 p-1.5 shadow-xl backdrop-blur-xl">
                      {group.items.map(({ id, label, responsibility, icon: Icon }) => (
                        <button
                          key={id}
                          type="button"
                          onClick={() => navigate(id)}
                          className={`flex w-full items-start gap-3 rounded-md px-3 py-2.5 text-left transition duration-200 ease-out ${
                            activeTab === id ? "bg-slate-100 text-ink" : "text-slate-600 hover:bg-slate-50 hover:text-ink"
                          }`}
                        >
                          <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-accent-soft text-accent-strong">
                            <Icon size={15} />
                          </span>
                          <span className="min-w-0 flex-1">
                            <span className="block text-sm font-semibold">{label}</span>
                            {responsibility && <span className="mt-0.5 block text-xs leading-5 text-muted">{responsibility}</span>}
                          </span>
                          {activeTab === id && <Check size={15} className="mt-1 text-emerald-600" />}
                        </button>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          ))}
        </nav>

        <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
          <div className="hidden min-w-0 items-center gap-2 border-l border-line/80 px-3 py-1 text-sm 2xl:flex">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-white text-ink shadow-sm">
              <Building2 size={15} />
            </span>
            <span className="min-w-0">
              <span className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-muted">Campus</span>
              <span className="block max-w-[10rem] truncate text-sm font-semibold text-ink 2xl:max-w-[12rem]">{campusLabel}</span>
            </span>
          </div>

          <div className="relative hidden sm:block">
            <button
              type="button"
              aria-label="Search"
              aria-expanded={searchOpen}
              onClick={() => {
                setSearchOpen((open) => !open);
                setNotificationOpen(false);
                setUserMenuOpen(false);
                setOpenDomain(null);
                setLauncherOpen(false);
                setFaqOpen(false);
              }}
              className="flex h-9 w-9 items-center justify-center rounded-md border border-line/80 bg-white text-muted shadow-sm transition hover:bg-slate-50 hover:text-ink"
            >
              <Search size={17} />
            </button>
            {searchOpen && (
              <div className="absolute right-0 top-full z-30 mt-2 w-[min(30rem,calc(100vw-1rem))] rounded-lg border border-line/70 bg-white p-3 shadow-xl">
                <label htmlFor="erp-global-search" className="relative block">
                  <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                  <input
                    id="erp-global-search"
                    value={searchTerm}
                    onChange={(event) => setSearchTerm(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && searchResults[0]) navigate(searchResults[0].id);
                    }}
                    autoFocus
                    placeholder="Search module, workflow, role, or responsibility"
                    className="w-full rounded-md border border-line/80 bg-slate-50 py-2.5 pl-9 pr-3 text-sm text-ink outline-none focus:border-accent"
                  />
                </label>

                <div className="mt-3 grid max-h-72 gap-1 overflow-y-auto">
                  {searchResults.map(({ id, label, domainLabel, responsibility, icon: Icon }) => (
                    <button
                      key={id}
                      type="button"
                      onClick={() => navigate(id)}
                      className="flex w-full items-start gap-3 rounded-md px-3 py-2.5 text-left hover:bg-slate-50"
                    >
                      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-accent-soft text-accent-strong">
                        <Icon size={15} />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm font-semibold text-ink">{label}</span>
                        <span className="mt-0.5 block text-xs leading-5 text-muted">{domainLabel ?? "Workspace"} - {responsibility ?? "Open workflow"}</span>
                      </span>
                      {activeTab === id && <Check size={15} className="mt-1 text-emerald-600" />}
                    </button>
                  ))}
                  {searchResults.length === 0 && (
                    <div className="rounded-md border border-line/70 bg-slate-50 px-3 py-5 text-center text-sm text-muted">
                      No matching workflow found.
                    </div>
                  )}
                </div>

                <div className="mt-3 grid gap-2 border-t border-line/60 pt-3 sm:grid-cols-3">
                  <button type="button" onClick={openSupportPanel} className="rounded-md border border-line/70 bg-white px-3 py-2 text-xs font-semibold text-ink hover:bg-slate-50">
                    Support
                  </button>
                  <button type="button" onClick={() => { setNotificationOpen(true); setSearchOpen(false); }} className="rounded-md border border-line/70 bg-white px-3 py-2 text-xs font-semibold text-ink hover:bg-slate-50">
                    Updates
                  </button>
                  <button type="button" onClick={() => { setFaqOpen(true); setSearchOpen(false); }} className="rounded-md border border-line/70 bg-white px-3 py-2 text-xs font-semibold text-ink hover:bg-slate-50">
                    FAQs
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="relative hidden sm:block">
            <button
              type="button"
              aria-expanded={faqOpen}
              onClick={() => {
                setFaqOpen((open) => !open);
                setNotificationOpen(false);
                setUserMenuOpen(false);
                setOpenDomain(null);
                setLauncherOpen(false);
              }}
              className="flex h-9 items-center justify-center rounded-md border border-line/80 bg-white px-3 text-sm font-medium text-rose-600 shadow-sm transition hover:bg-slate-50"
            >
              FAQs
            </button>
            {faqOpen && (
              <div className="absolute right-0 top-full z-30 mt-2 w-[min(36rem,calc(100vw-1rem))] rounded-lg border border-line/70 bg-white p-4 shadow-xl">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <h2 className="text-lg font-semibold text-ink">Frequently Asked Questions</h2>
                  <button
                    type="button"
                    onClick={() => setFaqOpen(false)}
                    className="flex h-9 w-9 items-center justify-center rounded-md border border-line/70 text-muted hover:bg-slate-50 hover:text-ink"
                    aria-label="Close FAQs"
                  >
                    <X size={16} />
                  </button>
                </div>
                <div className="max-h-[28rem] overflow-y-auto pr-1">
                  {FAQ_ITEMS.map((item, index) => {
                    const isOpen = activeFaqIndex === index;
                    return (
                    <button
                      key={item.question}
                      type="button"
                      onClick={() => setActiveFaqIndex((current) => current === index ? null : index)}
                      className="block w-full border-b border-line/70 bg-slate-50 px-4 py-3 text-left hover:bg-white"
                    >
                      <span className="flex items-center justify-between gap-4 text-sm font-medium text-blue-700">
                        <span>{index + 1}. {item.question}</span>
                        <Plus size={18} className={`shrink-0 transition ${isOpen ? "rotate-45" : ""}`} />
                      </span>
                      {isOpen && <span className="mt-2 block text-sm leading-6 text-muted">{item.answer}</span>}
                    </button>
                  );})}
                </div>
              </div>
            )}
          </div>

          <div className="relative">
            <button
              type="button"
              aria-label="Updates"
              aria-expanded={notificationOpen}
              onClick={() => {
                setNotificationOpen((open) => !open);
                setUserMenuOpen(false);
                setOpenDomain(null);
                setLauncherOpen(false);
                setFaqOpen(false);
              }}
              className="relative flex h-9 w-9 items-center justify-center rounded-md border border-line/80 bg-white text-muted shadow-sm transition duration-200 ease-out hover:bg-slate-50 hover:text-ink"
            >
              <Bell size={16} />
              {unreadAnnouncements.length > 0 && (
                <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-rose-600 px-1 text-[10px] font-bold text-white ring-2 ring-white">
                  {unreadAnnouncements.length}
                </span>
              )}
            </button>

            {notificationOpen && (
              <div className="absolute right-0 top-full z-30 mt-2 w-[min(24rem,calc(100vw-0.75rem))] rounded-lg border border-line/70 bg-white/95 p-2 shadow-xl backdrop-blur-xl">
                <div className="flex items-start justify-between gap-3 rounded-md bg-slate-50 px-3 py-3">
                  <div>
                    <p className="flex items-center gap-2 text-sm font-semibold text-ink">
                      <Megaphone size={15} />
                      Updates
                    </p>
                    <p className="mt-1 text-xs text-muted">{unreadAnnouncements.length} unread of {announcements.length}</p>
                    {notificationError && <p className="mt-1 text-xs text-rose-600">{notificationError}</p>}
                  </div>
                  <button
                    type="button"
                    onClick={() => setReadAnnouncementIds(new Set(announcements.map((item) => item.id)))}
                    className="inline-flex items-center gap-1.5 rounded-md border border-line/70 bg-white px-2.5 py-1.5 text-xs font-semibold text-muted hover:text-ink"
                  >
                    <CheckCheck size={13} />
                    Mark read
                  </button>
                </div>

                <div className="mt-2 max-h-[24rem] overflow-y-auto pr-1">
                  {announcements.map(({ id, title, message, priority, time, icon: Icon }) => {
                    const isUnread = !readAnnouncementIds.has(id);
                    return (
                      <button
                        key={id}
                        type="button"
                        onClick={() => setReadAnnouncementIds((current) => new Set(current).add(id))}
                        className="flex w-full items-start gap-3 rounded-md px-3 py-3 text-left transition duration-200 ease-out hover:bg-slate-50"
                      >
                        <span className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-md border ${announcementTone(priority)}`}>
                          {priority === "high" ? <AlertCircle size={16} /> : <Icon size={16} />}
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="flex items-start justify-between gap-2">
                            <span className="text-sm font-semibold text-ink">{title}</span>
                            {isUnread && <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-rose-500" />}
                          </span>
                          <span className="mt-1 block text-xs leading-5 text-muted">{message}</span>
                          <span className="mt-2 block text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">{time}</span>
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          <div className="relative hidden sm:block">
            <button
              type="button"
              aria-label="Open quick apps"
              aria-expanded={launcherOpen}
              onClick={() => {
                setLauncherOpen((open) => !open);
                setNotificationOpen(false);
                setUserMenuOpen(false);
                setOpenDomain(null);
                setFaqOpen(false);
              }}
              className="flex h-9 w-9 items-center justify-center rounded-md border border-line/80 bg-white text-accent shadow-sm transition hover:bg-slate-50"
            >
              <Grid3X3 size={17} />
            </button>
            {launcherOpen && (
              <div className="absolute right-0 top-full z-30 mt-2 w-[min(28rem,calc(100vw-1rem))] rounded-lg border border-line/70 bg-white p-5 shadow-xl">
                <div className="grid grid-cols-3 gap-5">
                  {navItems.slice(0, 9).map(({ id, label, icon: Icon }) => (
                    <button
                      key={id}
                      type="button"
                      onClick={() => navigate(id)}
                      className="flex flex-col items-center gap-2 rounded-md p-2 text-center text-sm text-muted hover:bg-slate-50 hover:text-ink"
                    >
                      <Icon size={26} className="text-accent" />
                      <span>{label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="relative">
            <button
              type="button"
              id="user-menu-button"
              onClick={() => {
                setUserMenuOpen(!userMenuOpen);
                setOpenDomain(null);
                setNotificationOpen(false);
                setLauncherOpen(false);
                setFaqOpen(false);
              }}
              aria-expanded={userMenuOpen}
              className="flex h-9 items-center gap-2 rounded-md border border-line/80 bg-white px-1.5 text-sm shadow-sm transition duration-200 ease-out hover:bg-slate-50"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent text-xs font-bold text-white">
                {user?.full_name?.[0]?.toUpperCase() ?? user?.username?.[0]?.toUpperCase() ?? "U"}
              </div>
              <span className="hidden min-w-0 xl:block">
                <span className="block max-w-32 truncate text-sm font-semibold leading-4 text-ink">
                  {user?.full_name || user?.username}
                </span>
                <span className="block text-[11px] capitalize leading-4 text-muted">{accessLabel(user?.role)}</span>
              </span>
              <ChevronDown size={14} className="text-muted" />
            </button>

            {userMenuOpen && (
              <div className="absolute right-0 top-full z-30 mt-2 w-[min(20rem,calc(100vw-0.75rem))] rounded-lg border border-line/70 bg-white/95 p-2 shadow-xl backdrop-blur-xl">
                <div className="rounded-md bg-slate-50 px-3 py-3">
                  <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-muted">Account</p>
                  <div className="flex items-start gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-accent text-sm font-bold text-white">
                      {user?.full_name?.[0]?.toUpperCase() ?? user?.username?.[0]?.toUpperCase() ?? "U"}
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-ink">{user?.full_name || user?.username}</p>
                      <p className="truncate text-xs text-muted">{user?.email || user?.username}</p>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold capitalize ${roleColour}`}>
                          {scopeLabel}
                        </span>
                        <span className="rounded-full border border-line/70 bg-white px-2 py-0.5 text-xs font-semibold text-muted">
                          {accessLabel(user?.role)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <p className="mt-3 flex items-center gap-1.5 text-xs font-semibold text-ink">
                    <Building2 size={12} />
                    {campusLabel}
                  </p>
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                    <div className="rounded-md border border-line/70 bg-white px-2.5 py-2">
                      <span className="block font-semibold uppercase tracking-[0.12em] text-muted">Username</span>
                      <span className="mt-1 block truncate font-medium text-ink">{user?.username}</span>
                    </div>
                    <div className="rounded-md border border-line/70 bg-white px-2.5 py-2">
                      <span className="block font-semibold uppercase tracking-[0.12em] text-muted">Role</span>
                      <span className="mt-1 block truncate font-medium capitalize text-ink">{roleLabel}</span>
                    </div>
                  </div>
                </div>
                {user?.campuses && user.campuses.length > 0 && (
                  <div className="border-b border-line/60 px-2 py-3">
                    <p className="text-xs font-semibold uppercase tracking-widest text-muted">Campuses</p>
                    <div className="mt-2 grid gap-1.5">
                      {user.campuses.map((campus) => (
                        <div key={`${campus.id}-${campus.role}`} className="flex items-center justify-between gap-2 rounded-md bg-slate-50 px-2.5 py-2 text-xs">
                          <span className="font-medium text-ink">{campus.code}</span>
                          <span className="capitalize text-muted">{campus.role.replace("_", " ")}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => { logout(); setUserMenuOpen(false); }}
                  className="mt-1 flex w-full items-center gap-2 rounded-md px-3 py-2.5 text-sm font-medium text-rose-600 transition hover:bg-rose-50"
                >
                  <LogOut size={14} />
                  Sign out
                </button>
              </div>
            )}
          </div>

          <button
            type="button"
            aria-label="Open menu"
            onClick={() => {
              setMenuOpen(true);
              setNotificationOpen(false);
              setUserMenuOpen(false);
              setOpenDomain(null);
              setLauncherOpen(false);
              setFaqOpen(false);
            }}
            className="flex h-9 w-9 items-center justify-center rounded-md border border-line/80 bg-white text-muted shadow-sm transition duration-200 ease-out hover:bg-slate-50 hover:text-ink md:hidden"
          >
            <Menu size={18} />
          </button>
        </div>
      </div>

      {/* Mobile drawer */}
      {menuOpen && (
        <div className="fixed inset-0 z-50 flex h-dvh flex-col bg-white md:hidden" style={{ animation: "drawer-in 180ms ease-out both" }}>
          <div className="h-1 bg-gradient-to-r from-teal-600 via-blue-600 to-slate-900" />
          <div className="flex items-center justify-between border-b border-line/70 px-4 py-3">
            <BrandLogo compact />
            <button
              type="button"
              onClick={() => setMenuOpen(false)}
              className="flex h-10 w-10 items-center justify-center rounded-lg border border-line/70 text-muted"
              aria-label="Close menu"
            >
              <X size={18} />
            </button>
          </div>
          <div className="border-b border-line/70 bg-slate-50 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted">Campus</p>
            <p className="mt-1 font-semibold text-ink">{campusLabel}</p>
          </div>
          <button
            type="button"
            onClick={() => setNotificationOpen((open) => !open)}
            className="mx-4 mt-4 flex items-center justify-between rounded-lg border border-line/70 bg-white px-4 py-3 text-left shadow-sm"
          >
            <span>
              <span className="flex items-center gap-2 text-sm font-semibold text-ink">
                <Bell size={15} />
                Updates
              </span>
              <span className="mt-1 block text-xs text-muted">{unreadAnnouncements.length} unread</span>
            </span>
            <span className="rounded-full bg-rose-600 px-2 py-0.5 text-xs font-bold text-white">{unreadAnnouncements.length}</span>
          </button>
          {notificationOpen && (
            <div className="mx-4 mt-2 max-h-52 overflow-y-auto rounded-lg border border-line/70 bg-white p-2 shadow-sm">
              {announcements.map(({ id, title, message, priority }) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => setReadAnnouncementIds((current) => new Set(current).add(id))}
                  className="block w-full rounded-md px-3 py-2 text-left hover:bg-slate-50"
                >
                  <span className="flex items-center justify-between gap-3">
                    <span className="text-sm font-semibold text-ink">{title}</span>
                    {priority === "high" && <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold uppercase text-amber-700">High</span>}
                  </span>
                  <span className="mt-1 block text-xs leading-5 text-muted">{message}</span>
                </button>
              ))}
            </div>
          )}
          <nav className="flex flex-1 flex-col gap-4 overflow-y-auto px-4 py-5" aria-label="Main navigation">
            {groupedNav.map((group) => (
              <div key={group.label}>
                <p className="px-2 text-xs font-semibold uppercase tracking-widest text-muted">{group.label}</p>
                <div className="mt-2 grid gap-2">
                  {group.items.map(({ id, label, responsibility, icon: Icon }) => (
                    <button
                      key={id}
                      type="button"
                      onClick={() => navigate(id)}
                      className={`flex w-full items-start gap-3 rounded-lg px-4 py-3 text-left text-base font-medium transition ${
                        activeTab === id
                          ? "bg-accent text-white shadow-sm"
                          : "text-ink hover:bg-slate-100"
                      }`}
                    >
                      <span className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-md ${activeTab === id ? "bg-white/10" : "bg-slate-100"}`}>
                        <Icon size={18} />
                      </span>
                      <span className="min-w-0">
                        <span className="block">{label}</span>
                        {responsibility && (
                          <span className={`mt-0.5 block text-xs font-normal ${activeTab === id ? "text-white/70" : "text-muted"}`}>
                            {responsibility}
                          </span>
                        )}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </nav>
          <div className="border-t border-line/60 p-4">
            <button
              type="button"
              onClick={logout}
              className="flex w-full items-center gap-3 rounded-lg px-4 py-3 text-base font-medium text-rose-600 hover:bg-rose-50"
            >
              <LogOut size={18} />
              Sign out
            </button>
          </div>
        </div>
      )}
    </header>
  );
}

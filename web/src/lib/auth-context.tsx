"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  authApi,
  clearTokens,
  hasTokens,
  SESSION_EXPIRED_EVENT,
  storeTokens,
  storeTenantCampusCode,
  type User,
  type UserRole,
} from "./api";

const LAST_ACTIVITY_KEY = "erp_last_activity";
const IDLE_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_SESSION_IDLE_MINUTES ?? "30") * 60 * 1000;
const SESSION_VALIDATE_MS = Number(process.env.NEXT_PUBLIC_SESSION_VALIDATE_SECONDS ?? "300") * 1000;
const ACTIVITY_EVENTS = ["click", "keydown", "mousemove", "scroll", "touchstart", "visibilitychange"];

function markActivity() {
  localStorage.setItem(LAST_ACTIVITY_KEY, String(Date.now()));
}

function isIdleExpired() {
  const lastActivity = Number(localStorage.getItem(LAST_ACTIVITY_KEY) ?? Date.now());
  return Date.now() - lastActivity > IDLE_TIMEOUT_MS;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string, captchaId: string, captchaAnswer: string, campusCode?: string) => Promise<void>;
  logout: () => void;
  isRole: (...roles: UserRole[]) => boolean;
}

const AuthCtx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Bootstrap from stored token on page load
  useEffect(() => {
    if (!hasTokens()) { setLoading(false); return; }
    if (isIdleExpired()) {
      clearTokens();
      localStorage.removeItem(LAST_ACTIVITY_KEY);
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then((currentUser) => {
        setUser(currentUser);
        markActivity();
      })
      .catch(() => {
        clearTokens();
        localStorage.removeItem(LAST_ACTIVITY_KEY);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (username: string, password: string, captchaId: string, captchaAnswer: string, campusCode = "") => {
    const data = await authApi.login(username, password, captchaId, captchaAnswer, campusCode);
    storeTokens(data.access, data.refresh);
    storeTenantCampusCode(campusCode);
    markActivity();
    setUser(data.user);
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    localStorage.removeItem(LAST_ACTIVITY_KEY);
    setUser(null);
  }, []);

  useEffect(() => {
    function expireSession() {
      setUser(null);
      localStorage.removeItem(LAST_ACTIVITY_KEY);
    }

    window.addEventListener(SESSION_EXPIRED_EVENT, expireSession);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, expireSession);
  }, []);

  useEffect(() => {
    if (!user) return;

    const recordActivity = () => markActivity();
    ACTIVITY_EVENTS.forEach((event) => window.addEventListener(event, recordActivity, { passive: true }));

    const idleTimer = window.setInterval(() => {
      if (isIdleExpired()) logout();
    }, 30_000);

    const validationTimer = window.setInterval(() => {
      authApi.me().then(setUser).catch(logout);
    }, SESSION_VALIDATE_MS);

    return () => {
      ACTIVITY_EVENTS.forEach((event) => window.removeEventListener(event, recordActivity));
      window.clearInterval(idleTimer);
      window.clearInterval(validationTimer);
    };
  }, [logout, user]);

  const isRole = useCallback(
    (...roles: UserRole[]) => !!user && roles.includes(user.role),
    [user]
  );

  const value = useMemo(
    () => ({ user, loading, login, logout, isRole }),
    [user, loading, login, logout, isRole]
  );

  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthCtx);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

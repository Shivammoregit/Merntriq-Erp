const LOCAL_API_PORT = process.env.NEXT_PUBLIC_LOCAL_API_PORT ?? "8000";
const PRODUCTION_API_BASE = "https://backend-nu-self-91.vercel.app/api/v1";
const LOOPBACK_HOSTS = new Set(["localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"]);

function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, "");
}

function localApiBase(hostname = "localhost") {
  const host = hostname === "[::1]" || hostname === "::1" ? "[::1]" : hostname;
  return `http://${host}:${LOCAL_API_PORT}/api/v1`;
}

function resolveApiBaseUrl() {
  const configuredBase = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (configuredBase) return trimTrailingSlash(configuredBase);
  if (typeof window === "undefined") {
    return process.env.NODE_ENV === "production" ? PRODUCTION_API_BASE : localApiBase();
  }

  try {
    const pageHost = window.location.hostname;
    if (LOOPBACK_HOSTS.has(pageHost)) return localApiBase(pageHost);
    if (window.location.protocol === "http:" && window.location.port) {
      return localApiBase(pageHost);
    }
    return PRODUCTION_API_BASE;
  } catch {
    return process.env.NODE_ENV === "production" ? PRODUCTION_API_BASE : localApiBase();
  }
}

const apiBaseUrl = resolveApiBaseUrl();

export const appConfig = {
  apiBaseUrl,
  apiDocsUrl: apiBaseUrl.replace("/api/v1", "/api/docs/"),
  apiHealthUrl: `${apiBaseUrl}/health/`
};

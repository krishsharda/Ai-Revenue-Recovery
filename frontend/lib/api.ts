import type {
  AnalyticsResponse,
  AppConfig,
  AppSettings,
  DashboardResponse,
  ExecuteResult,
  PaginatedAudit,
  PaginatedCases,
  RecoveryCaseDetail,
  SimulationResult,
  TestEmailResult,
} from "./types";

// Single-origin design: the whole app lives behind one URL. Browsers call the
// relative `/api`, which Vercel routes to the API service (see vercel.json) —
// or, in local development, which Next proxies to the uvicorn dev server.
//
// Server components have no origin to be relative to, so they need an absolute
// URL. In preference order:
//   · BACKEND_ORIGIN — explicit override for local dev, or an API hosted
//     somewhere else entirely.
//   · API_SERVICE_URL — injected by the service binding in vercel.json. This
//     reaches the API service over Vercel's internal network, which skips
//     Deployment Protection (a public round-trip would be rejected with a 401
//     on protected preview deployments) and stays deployment-aware, so a
//     preview talks to its own API rather than production's.
//   · VERCEL_URL — public fallback if the binding is unavailable.
//   · Otherwise the local uvicorn default.
function resolveServerBase(): string {
  const explicit = process.env.BACKEND_ORIGIN;
  if (explicit) return `${explicit.replace(/\/$/, "")}/api`;
  const binding = process.env.API_SERVICE_URL;
  if (binding) return `${binding.replace(/\/$/, "")}/api`;
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}/api`;
  return "http://127.0.0.1:8000/api";
}

export const API_BASE = typeof window === "undefined" ? resolveServerBase() : "/api";

// Admin-guarded endpoints (reseed, reset, test email) expect an X-Admin-Token.
// The operator pastes their own token in Settings; it is held for the browser
// session only and is never bundled into the app, so no secret ships to the
// client. Server-side rendering never calls these endpoints.
const ADMIN_TOKEN_KEY = "arr.adminToken";

export function getAdminToken(): string {
  if (typeof window === "undefined") return "";
  try {
    return window.sessionStorage.getItem(ADMIN_TOKEN_KEY) || "";
  } catch {
    return ""; // private mode / storage blocked
  }
}

export function setAdminToken(token: string): void {
  if (typeof window === "undefined") return;
  try {
    if (token) window.sessionStorage.setItem(ADMIN_TOKEN_KEY, token);
    else window.sessionStorage.removeItem(ADMIN_TOKEN_KEY);
  } catch {
    /* storage unavailable — the token simply won't persist across reloads */
  }
}

/** FastAPI reports errors as `{"detail": ...}`; surface that instead of raw JSON. */
function extractDetail(body: string, status: number): string {
  try {
    const parsed = JSON.parse(body);
    const detail = parsed?.detail;
    if (typeof detail === "string" && detail) return detail;
    // 422 validation errors arrive as a list of {loc, msg, type}.
    if (Array.isArray(detail) && detail.length) {
      const first = detail[0];
      if (typeof first?.msg === "string") return first.msg;
    }
  } catch {
    /* not JSON — fall through to the raw text */
  }
  return body.trim().slice(0, 200) || `Request failed with status ${status}.`;
}

async function request<T>(path: string, init?: RequestInit & { admin?: boolean }): Promise<T> {
  const { admin, ...rest } = init || {};
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((init?.headers as Record<string, string>) || {}),
  };
  if (admin) {
    const token = getAdminToken();
    if (token) headers["X-Admin-Token"] = token;
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...rest, headers, cache: "no-store" });
  } catch {
    // Network-level failure (backend down, DNS, CORS) — fetch gives no status.
    throw new Error("Can't reach the API. Check that the backend is running.");
  }
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(extractDetail(text, res.status));
  }
  return res.json() as Promise<T>;
}

export const api = {
  config: () => request<AppConfig>("/config"),
  health: () => request<Record<string, unknown>>("/health"),
  dashboard: () => request<DashboardResponse>("/dashboard"),
  analytics: () => request<AnalyticsResponse>("/analytics"),

  cases: (params: Record<string, string | number | undefined> = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") qs.set(k, String(v));
    });
    const q = qs.toString();
    return request<PaginatedCases>(`/recovery-cases${q ? `?${q}` : ""}`);
  },
  case: (id: number) => request<RecoveryCaseDetail>(`/recovery-cases/${id}`),
  analyzeCase: (id: number) =>
    request<RecoveryCaseDetail>(`/recovery-cases/${id}/analyze`, { method: "POST" }),
  executeCase: (id: number, body: { simulate?: boolean; force?: boolean } = {}) =>
    request<ExecuteResult>(`/recovery-cases/${id}/execute`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  auditLogs: (params: Record<string, string | number | undefined> = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") qs.set(k, String(v));
    });
    const q = qs.toString();
    return request<PaginatedAudit>(`/audit-logs${q ? `?${q}` : ""}`);
  },

  runSimulation: (body: { num_cases: number; seed?: number; persist?: boolean }) =>
    request<SimulationResult>("/simulation/run", { method: "POST", body: JSON.stringify(body) }),

  settings: () => request<AppSettings>("/settings"),
  sendTestEmail: (to: string) =>
    request<TestEmailResult>("/settings/email/test", {
      method: "POST",
      body: JSON.stringify({ to }),
      admin: true,
    }),
};

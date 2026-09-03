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

// The app deliberately holds no admin credential. `/settings/email/test` is the
// only guarded endpoint left, and the browser is not given a way to satisfy
// that guard — on a deployment the test send is simply reported as unavailable
// (see `email.test_allowed` from `/api/settings`) rather than offering a button
// that can only fail. Locally the guard is inactive, so it just works.

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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((init?.headers as Record<string, string>) || {}),
  };

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, headers, cache: "no-store" });
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

// `/config` reports which integrations are wired up — process-level metadata
// that doesn't change while the tab is open. The Topbar renders inside every
// page rather than in the shared layout, so each navigation remounted it and
// refetched: an extra round trip per route change, plus a visible flash of
// empty status pills. Caching the in-flight promise collapses that to one
// request per browser session, and a failure clears the cache so a later mount
// can retry.
let configPromise: Promise<AppConfig> | null = null;

function configCached(): Promise<AppConfig> {
  if (typeof window === "undefined") return request<AppConfig>("/config");
  if (!configPromise) {
    configPromise = request<AppConfig>("/config").catch((err) => {
      configPromise = null;
      throw err;
    });
  }
  return configPromise;
}

export const api = {
  config: () => request<AppConfig>("/config"),
  /** Session-cached `/config` — prefer this in components that mount per route. */
  configCached,
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

  runSimulation: (body: { num_cases: number; seed?: number; persist?: boolean; use_llm?: boolean }) =>
    request<SimulationResult>("/simulation/run", { method: "POST", body: JSON.stringify(body) }),

  settings: () => request<AppSettings>("/settings"),
  sendTestEmail: (to: string) =>
    request<TestEmailResult>("/settings/email/test", {
      method: "POST",
      body: JSON.stringify({ to }),
    }),
};

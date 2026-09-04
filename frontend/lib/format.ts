// Currency + label formatting helpers (Indian numbering).

export function formatINRShort(amount: number): string {
  if (amount >= 1e7) return `₹${(amount / 1e7).toFixed(2)}Cr`;
  if (amount >= 1e5) return `₹${(amount / 1e5).toFixed(2)}L`;
  if (amount >= 1e3) return `₹${(amount / 1e3).toFixed(1)}K`;
  return `₹${Math.round(amount).toLocaleString("en-IN")}`;
}

export function formatINR(amount: number): string {
  return `₹${Math.round(amount).toLocaleString("en-IN")}`;
}

export function formatPct(value: number, digits = 0): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatProbability(value: number): string {
  if (value > 0 && value < 0.01) return `${(value * 100).toFixed(2)}%`;
  return formatPct(value);
}

export function formatRelative(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function formatTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function titleCase(s: string | null | undefined): string {
  if (!s) return "";
  return s
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export const RISK_STYLES: Record<string, string> = {
  CRITICAL: "bg-danger/12 text-danger border-danger/25",
  HIGH: "bg-warning/12 text-warning border-warning/25",
  MEDIUM: "bg-info/12 text-info border-info/25",
  LOW: "bg-muted text-muted-foreground border-border",
};

export const STATUS_STYLES: Record<string, string> = {
  RECOVERED: "bg-success/12 text-success border-success/25",
  IN_RECOVERY: "bg-info/12 text-info border-info/25",
  RECOMMENDED: "bg-accent/12 text-accent border-accent/25",
  ANALYZING: "bg-accent/10 text-accent border-accent/20",
  OPEN: "bg-muted text-muted-foreground border-border",
  DO_NOTHING: "bg-muted text-muted-foreground border-border",
  FAILED: "bg-danger/12 text-danger border-danger/25",
  CLOSED: "bg-muted text-muted-foreground border-border",
  ABANDONED: "bg-muted text-muted-foreground border-border",
};

export const ACTION_STYLES: Record<string, string> = {
  RETRY_PAYMENT: "bg-info/12 text-info border-info/25",
  SCHEDULE_RETRY: "bg-info/10 text-info border-info/20",
  PAYMENT_LINK: "bg-accent/12 text-accent border-accent/25",
  ALTERNATE_PAYMENT_METHOD: "bg-success/12 text-success border-success/25",
  EMAIL: "bg-warning/12 text-warning border-warning/25",
  WHATSAPP: "bg-success/12 text-success border-success/25",
  HUMAN_ESCALATION: "bg-danger/12 text-danger border-danger/25",
  DO_NOTHING: "bg-muted text-muted-foreground border-border",
};

export function probabilityColor(p: number): string {
  if (p >= 0.7) return "text-success";
  if (p >= 0.4) return "text-warning";
  return "text-danger";
}

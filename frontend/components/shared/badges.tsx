import { Badge } from "@/components/ui/badge";
import { ACTION_STYLES, RISK_STYLES, STATUS_STYLES, titleCase } from "@/lib/format";
import { cn } from "@/lib/utils";

export function RiskBadge({ risk }: { risk: string }) {
  return <Badge className={cn("whitespace-nowrap", RISK_STYLES[risk] || RISK_STYLES.LOW)}>{risk}</Badge>;
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge className={cn("whitespace-nowrap", STATUS_STYLES[status] || STATUS_STYLES.OPEN)}>
      {titleCase(status)}
    </Badge>
  );
}

export function ActionBadge({ action }: { action: string | null | undefined }) {
  if (!action) return <span className="text-xs text-muted-foreground">—</span>;
  return (
    <Badge className={cn("whitespace-nowrap", ACTION_STYLES[action] || ACTION_STYLES.DO_NOTHING)}>
      {titleCase(action)}
    </Badge>
  );
}

export function ExecutionModeBadge({ mode }: { mode: string }) {
  const realRzp = mode === "REAL_RAZORPAY_TEST";
  const realEmail = mode === "REAL_RESEND_EMAIL";
  const real = realRzp || realEmail;
  return (
    <Badge
      className={cn(
        "whitespace-nowrap",
        real ? "bg-success/12 text-success border-success/25" : "bg-warning/12 text-warning border-warning/25"
      )}
    >
      {realEmail ? "Real · Email Sent" : realRzp ? "Real · Razorpay Test" : "Simulated"}
    </Badge>
  );
}

export function ProbabilityBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = value >= 0.7 ? "bg-success" : value >= 0.4 ? "bg-warning" : "bg-danger";
  return (
    <div className="flex min-w-[112px] items-center gap-2.5">
      <div className="h-1 flex-1 overflow-hidden rounded-full bg-muted">
        <div className={cn("h-full rounded-full", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-9 text-right font-mono text-[12px] font-medium tabular-nums">{pct}%</span>
    </div>
  );
}

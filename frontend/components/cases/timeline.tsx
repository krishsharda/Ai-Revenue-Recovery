import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  Circle,
  Flag,
  Gauge,
  Link2,
  PauseCircle,
  Send,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import type { EventOut } from "@/lib/types";
import { formatTime } from "@/lib/format";

const ICONS: Record<string, { icon: any; color: string }> = {
  alert: { icon: AlertTriangle, color: "text-danger bg-danger/10" },
  shield: { icon: ShieldCheck, color: "text-info bg-info/10" },
  gauge: { icon: Gauge, color: "text-primary bg-primary/10" },
  brain: { icon: BrainCircuit, color: "text-primary bg-primary/10" },
  send: { icon: Send, color: "text-info bg-info/10" },
  check: { icon: CheckCircle2, color: "text-success bg-success/10" },
  x: { icon: XCircle, color: "text-danger bg-danger/10" },
  pause: { icon: PauseCircle, color: "text-muted-foreground bg-muted" },
  link: { icon: Link2, color: "text-primary bg-primary/10" },
  flag: { icon: Flag, color: "text-muted-foreground bg-muted" },
};

export function Timeline({ events }: { events: EventOut[] }) {
  if (events.length === 0) {
    return <p className="text-sm text-muted-foreground">No timeline events yet.</p>;
  }
  return (
    <ol className="relative space-y-4">
      {events.map((e, i) => {
        const meta = (e.icon && ICONS[e.icon]) || { icon: Circle, color: "text-muted-foreground bg-muted" };
        const Icon = meta.icon;
        const last = i === events.length - 1;
        return (
          <li key={e.id} className="relative flex gap-3">
            {!last && <span className="absolute left-[15px] top-8 h-[calc(100%-8px)] w-px bg-border" />}
            <div className={`z-10 grid h-8 w-8 shrink-0 place-items-center rounded-full ${meta.color}`}>
              <Icon className="h-4 w-4" />
            </div>
            <div className="flex-1 pb-1">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium">{e.label}</p>
                <span className="shrink-0 text-[11px] tabular-nums text-muted-foreground">
                  {formatTime(e.created_at)}
                </span>
              </div>
              {e.detail && <p className="mt-0.5 text-xs text-muted-foreground">{e.detail}</p>}
              <p className="mt-0.5 text-[10px] uppercase tracking-wider text-muted-foreground/70">
                {e.actor}
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

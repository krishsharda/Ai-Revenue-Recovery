import type { FunnelStage } from "@/lib/types";
import { formatINRShort } from "@/lib/format";

export function RecoveryFunnel({ stages }: { stages: FunnelStage[] }) {
  const max = Math.max(1, ...stages.map((s) => s.amount));
  return (
    <div className="space-y-2.5">
      {stages.map((s, i) => {
        const pct = Math.max(6, (s.amount / max) * 100);
        const isRecovered = i === stages.length - 1;
        return (
          <div key={s.stage} className="group">
            <div className="mb-1.5 flex items-center justify-between text-xs">
              <span className="font-medium text-muted-foreground">{s.stage}</span>
              <span className="font-mono tabular-nums">
                <span className="font-semibold text-foreground">{formatINRShort(s.amount)}</span>
                <span className="ml-2 text-muted-foreground">{s.count}</span>
              </span>
            </div>
            <div className="h-7 w-full overflow-hidden rounded-md bg-muted">
              <div
                className={`h-full rounded-md transition-all duration-500 ${
                  isRecovered
                    ? "bg-gradient-to-r from-[hsl(158_64%_40%)] to-[hsl(158_64%_55%)]"
                    : "bg-gradient-to-r from-[hsl(205_96%_42%)] to-[hsl(205_96%_60%)]"
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

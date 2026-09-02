import type { InterventionPerformance } from "@/lib/types";
import { titleCase } from "@/lib/format";
import { ACTION_COLORS } from "@/components/charts/palette";

export function PerfBars({ data }: { data: InterventionPerformance[] }) {
  if (data.length === 0) {
    return <p className="text-sm text-muted-foreground">No intervention data yet. Run a simulation.</p>;
  }
  return (
    <div className="space-y-3">
      {data.map((d) => {
        const naRate = d.success_rate === null;
        const pct = naRate ? 0 : Math.round((d.success_rate || 0) * 100);
        const color = ACTION_COLORS[d.action_type.split(" · ")[0]] || "hsl(245 78% 66%)";
        return (
          <div key={d.action_type}>
            <div className="mb-1.5 flex items-center justify-between text-xs">
              <span className="font-medium">{titleCase(d.action_type)}</span>
              <span className="font-mono tabular-nums text-muted-foreground">
                {naRate ? (
                  <span>N/A</span>
                ) : (
                  <span className="font-semibold text-foreground">{pct}%</span>
                )}
                <span className="ml-2">n={d.attempts}</span>
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${naRate ? 100 : pct}%`, background: naRate ? "hsl(214 20% 84%)" : color }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

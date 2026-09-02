import { Check, TrendingUp } from "lucide-react";
import { formatINR } from "@/lib/format";
import { ACTION_COLORS } from "@/components/charts/palette";
import { cn } from "@/lib/utils";
import type { InterventionOption } from "@/lib/types";

export function StrategyComparison({
  options,
  reason,
}: {
  options: InterventionOption[];
  reason?: string | null;
}) {
  if (!options?.length) return null;
  const maxEV = Math.max(1, ...options.map((o) => o.expected_value));
  const recommended = options.find((o) => o.recommended);

  return (
    <div>
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h3 className="font-display text-[15px] font-semibold tracking-tight">
            Expected Recovery by Strategy
          </h3>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Expected Value = Transaction Amount × Recovery Probability. The engine picks the
            strategy that maximises recovered rupees, not just any reminder.
          </p>
        </div>
        <span className="eyebrow shrink-0">AI Decision</span>
      </div>

      <div className="space-y-2.5">
        {options.map((o) => {
          const color = ACTION_COLORS[o.action_type] || "hsl(217 91% 56%)";
          const w = Math.max(3, (o.expected_value / maxEV) * 100);
          return (
            <div
              key={o.action_type}
              className={cn(
                "rounded-xl border px-3.5 py-2.5 transition-colors",
                o.recommended
                  ? "border-accent/40 bg-accent/[0.06]"
                  : "border-border bg-muted/30"
              )}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="text-[13.5px] font-medium">{o.label}</span>
                  {o.recommended && (
                    <span className="inline-flex items-center gap-1 rounded-md bg-accent px-1.5 py-0.5 font-mono text-[9.5px] font-semibold uppercase tracking-[0.08em] text-accent-foreground">
                      <Check className="h-2.5 w-2.5" /> Recommended
                    </span>
                  )}
                  {!o.recommended && o.is_best_value && (
                    <span className="inline-flex items-center gap-1 rounded-md border border-success/30 bg-success/10 px-1.5 py-0.5 font-mono text-[9.5px] font-medium uppercase tracking-[0.08em] text-success">
                      <TrendingUp className="h-2.5 w-2.5" /> Top value
                    </span>
                  )}
                </div>
                <div className="text-right">
                  <span className="font-mono text-[14px] font-semibold tabular-nums">
                    {formatINR(o.expected_value)}
                  </span>
                  <span className="ml-2 font-mono text-[11px] text-muted-foreground tabular-nums">
                    {Math.round(o.success_probability * 100)}%
                  </span>
                </div>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                  <div className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${w}%`, background: color }} />
                </div>
                {o.note && (
                  <span className="shrink-0 font-mono text-[10px] text-muted-foreground">{o.note}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {recommended && (
        <div className="mt-4 rounded-xl border border-accent/20 bg-accent/[0.04] px-4 py-3">
          <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
            Why {recommended.label}?
          </p>
          <p className="mt-1 text-[13px] leading-relaxed">
            {reason ||
              `Selected for the strongest expected recovery given the failure reason, customer history, and historical intervention performance.`}
          </p>
        </div>
      )}
    </div>
  );
}

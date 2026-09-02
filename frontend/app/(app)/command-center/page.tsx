import Link from "next/link";
import { ArrowRight, ArrowUpRight, Sparkles, Target } from "lucide-react";
import { Topbar } from "@/components/layout/topbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiErrorState } from "@/components/shared/states";
import { ActionBadge } from "@/components/shared/badges";
import { Avatar } from "@/components/shared/avatar";
import { RadialGauge } from "@/components/shared/radial-gauge";
import { api } from "@/lib/api";
import { formatINR, formatINRShort, titleCase } from "@/lib/format";
import { ACTION_COLORS } from "@/components/charts/palette";
import type { DashboardResponse } from "@/lib/types";

export const dynamic = "force-dynamic";

const GRID_TEXTURE =
  "linear-gradient(hsl(222 47% 11% / 0.035) 1px, transparent 1px), linear-gradient(90deg, hsl(222 47% 11% / 0.035) 1px, transparent 1px)";

export default async function CommandCenterPage() {
  let data: DashboardResponse;
  try {
    data = await api.dashboard();
  } catch (e) {
    return (
      <>
        <Topbar title="Recovery Command Center" />
        <div className="p-5">
          <ApiErrorState error={(e as Error).message} />
        </div>
      </>
    );
  }

  const maxAction = Math.max(1, ...data.action_counts.map((a) => a.count));

  return (
    <>
      <Topbar title="Recovery Command Center" subtitle="Every at-risk rupee, one decision surface" />
      <div className="space-y-5 p-5 sm:p-6">
        {/* ── Cinematic masthead ─────────────────────────────────────────── */}
        <section
          className="relative overflow-hidden rounded-[20px] border border-border bg-card p-6 animate-fade-up sheen sm:p-8"
          style={{ animationDelay: "40ms" }}
        >
          {/* soft glows */}
          <div className="pointer-events-none absolute -right-24 -top-32 h-80 w-80 rounded-full bg-[radial-gradient(circle,hsl(217_91%_58%/0.10),transparent_70%)] blur-2xl" />
          <div className="pointer-events-none absolute -bottom-40 left-1/3 h-80 w-80 rounded-full bg-[radial-gradient(circle,hsl(152_58%_45%/0.07),transparent_70%)] blur-2xl" />
          {/* grid texture */}
          <div
            className="pointer-events-none absolute inset-0 opacity-40 [mask-image:radial-gradient(120%_100%_at_0%_0%,black,transparent_70%)]"
            style={{ backgroundImage: GRID_TEXTURE, backgroundSize: "34px 34px" }}
          />

          <div className="relative flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between">
            <div className="max-w-xl">
              <p className="eyebrow inline-flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse-soft shadow-[0_0_8px_hsl(var(--success))]" />
                Live operations · Razorpay Test Mode
              </p>
              <h1 className="mt-4 font-display text-[40px] font-semibold leading-[1.02] tracking-tightest sm:text-[52px]">
                Winning back
                <br />
                <span className="text-gradient">{formatINRShort(data.revenue_recovered)}</span>
              </h1>
              <p className="mt-4 max-w-md text-[14px] leading-relaxed text-muted-foreground">
                {data.recovery_rate.toFixed(1)}% of at-risk revenue already recovered across{" "}
                <span className="text-foreground">{data.active_cases}</span> live cases — each decided by
                AI, cleared by guardrails, measured in real rupees.
              </p>
              <div className="mt-6 flex flex-wrap items-center gap-3">
                <Link
                  href="/cases"
                  className="inline-flex items-center gap-2 rounded-[10px] bg-primary px-4 py-2.5 text-[13px] font-semibold text-primary-foreground transition-all hover:brightness-95"
                >
                  Review recovery cases <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="/simulation"
                  className="inline-flex items-center gap-2 rounded-[10px] border border-border bg-muted/50 px-4 py-2.5 text-[13px] font-medium transition-colors hover:bg-muted"
                >
                  <Sparkles className="h-4 w-4 text-accent" /> Run simulation
                </Link>
              </div>
            </div>

            {/* gauge */}
            <div className="relative grid shrink-0 place-items-center">
              <div className="absolute h-56 w-56 rounded-full bg-[radial-gradient(circle,hsl(217_91%_58%/0.10),transparent_70%)] blur-xl" />
              <RadialGauge
                value={data.recovery_rate / 100}
                size={210}
                stroke={14}
                label={`${data.recovery_rate.toFixed(1)}%`}
                sublabel="recovery rate"
                color="hsl(217 91% 56%)"
              />
            </div>
          </div>

          {/* satellite stats */}
          <div className="relative mt-8 grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-border bg-muted/50 sm:grid-cols-4">
            <HeroStat label="Revenue at Risk" value={formatINRShort(data.revenue_at_risk)} tone="text-danger" />
            <HeroStat label="Revenue Recovered" value={formatINRShort(data.revenue_recovered)} tone="text-success" />
            <HeroStat label="Active Cases" value={data.active_cases.toLocaleString()} />
            <HeroStat label="Total Cases" value={data.total_cases.toLocaleString()} />
          </div>
        </section>

        {/* ── AI Actions + Top Opportunities ─────────────────────────────── */}
        <div className="grid gap-5 lg:grid-cols-2">
          <Card className="animate-fade-up" style={{ animationDelay: "120ms" }}>
            <CardHeader>
              <CardTitle>AI Actions</CardTitle>
              <p className="text-xs text-muted-foreground">
                What the engine decided across {data.total_cases} cases.
              </p>
            </CardHeader>
            <CardContent className="space-y-3.5">
              {data.action_counts.length === 0 && (
                <p className="text-sm text-muted-foreground">No decisions yet.</p>
              )}
              {data.action_counts.map((a) => {
                const color = ACTION_COLORS[a.action_type] || "hsl(205 96% 60%)";
                return (
                  <div key={a.action_type} className="flex items-center gap-3">
                    <span className="w-44 shrink-0 text-[13px] font-medium">{titleCase(a.action_type)}</span>
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${(a.count / maxAction) * 100}%`, background: color }}
                      />
                    </div>
                    <span className="w-10 shrink-0 text-right font-mono text-[13px] font-semibold tabular-nums">
                      {a.count}
                    </span>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          <Card className="animate-fade-up" style={{ animationDelay: "180ms" }}>
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle>Top Recovery Opportunities</CardTitle>
              <Link href="/cases" className="inline-flex items-center gap-1 font-mono text-[11px] uppercase tracking-[0.1em] text-accent hover:underline">
                All cases <ArrowUpRight className="h-3 w-3" />
              </Link>
            </CardHeader>
            <CardContent className="space-y-2">
              {data.top_opportunities.map((o, i) => (
                <Link
                  key={o.case_id}
                  href={`/cases/${o.case_id}`}
                  className="group flex items-center justify-between rounded-xl border border-border bg-muted/40 px-3.5 py-3 transition-colors hover:border-accent/30 hover:bg-muted"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <span className="w-5 shrink-0 font-mono text-[11px] tabular-nums text-muted-foreground/60">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <Avatar name={o.customer_name} size="sm" />
                    <div className="min-w-0">
                      <p className="truncate text-[13.5px] font-medium">{o.customer_name}</p>
                      <p className="font-mono text-[11px] text-muted-foreground">{formatINR(o.amount)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-mono text-[15px] font-semibold tabular-nums text-success">
                        {Math.round(o.recovery_probability * 100)}%
                      </p>
                      <p className="font-mono text-[9px] uppercase tracking-[0.16em] text-muted-foreground">recovery</p>
                    </div>
                    <ActionBadge action={o.recommended_action} />
                  </div>
                </Link>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* ── Principle strip ────────────────────────────────────────────── */}
        <Card
          className="overflow-hidden bg-[linear-gradient(100deg,hsl(var(--card)),hsl(205_96%_45%/0.06))] animate-fade-up"
          style={{ animationDelay: "240ms" }}
        >
          <CardContent className="flex flex-col items-center justify-between gap-4 p-5 md:flex-row">
            <div className="flex items-center gap-3.5">
              <div className="grid h-10 w-10 place-items-center rounded-xl border border-border bg-muted/60">
                <Target className="h-5 w-5 text-accent" />
              </div>
              <div>
                <p className="font-display font-semibold tracking-tight">AI decides · Rules control · System executes</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Every recommendation passes the guardrail engine before any money moves.
                </p>
              </div>
            </div>
            <Link
              href="/simulation"
              className="shrink-0 rounded-[10px] bg-primary px-4 py-2.5 text-[13px] font-semibold text-primary-foreground transition-all hover:brightness-95"
            >
              Run recovery simulation
            </Link>
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function HeroStat({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="bg-card px-4 py-4">
      <p className="eyebrow">{label}</p>
      <p className={`mt-2 font-display text-[24px] font-semibold leading-none tabular-nums ${tone || ""}`}>
        {value}
      </p>
    </div>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Activity, Database, Loader2, Play, Sparkles } from "lucide-react";
import { Topbar } from "@/components/layout/topbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RecoveryFunnel } from "@/components/charts/recovery-funnel";
import { InterventionBar } from "@/components/charts/intervention-bar";
import { api } from "@/lib/api";
import { formatINRShort } from "@/lib/format";
import type { SimulationResult } from "@/lib/types";

const PRESETS = [100, 500, 1000];

export default function SimulationPage() {
  const router = useRouter();
  const [numCases, setNumCases] = useState(1000);
  const [persist, setPersist] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.runSimulation({ num_cases: numCases, persist });
      setResult(res);
      if (persist) router.refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Topbar title="Recovery Simulation" subtitle="Batch demo mode — every metric computed live" />
      <div className="space-y-5 p-5">
        {/* Controls */}
        <Card>
          <CardContent className="flex flex-col gap-5 p-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-4">
              <div>
                <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Number of cases: <span className="text-foreground">{numCases.toLocaleString()}</span>
                </label>
                <input
                  type="range"
                  min={50}
                  max={2000}
                  step={50}
                  value={numCases}
                  onChange={(e) => setNumCases(Number(e.target.value))}
                  className="mt-2 w-full max-w-md accent-[hsl(var(--primary))]"
                />
                <div className="mt-2 flex gap-2">
                  {PRESETS.map((p) => (
                    <button
                      key={p}
                      onClick={() => setNumCases(p)}
                      className={`rounded-lg border px-3 py-1 text-xs font-medium transition-colors ${
                        numCases === p
                          ? "border-primary/40 bg-primary/15 text-foreground"
                          : "border-border bg-muted/30 text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {p.toLocaleString()}
                    </button>
                  ))}
                </div>
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={persist}
                  onChange={(e) => setPersist(e.target.checked)}
                  className="h-4 w-4 accent-[hsl(var(--primary))]"
                />
                <Database className="h-4 w-4 text-muted-foreground" />
                Persist generated cases to the database
              </label>
            </div>
            <button
              onClick={run}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/20 transition-all hover:bg-primary/90 disabled:opacity-60"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              {loading ? "Running…" : "Run Recovery Simulation"}
            </button>
          </CardContent>
        </Card>

        {error && (
          <Card className="border-danger/30 bg-danger/5 p-4 text-sm text-danger">{error}</Card>
        )}

        {!result && !loading && (
          <Card className="p-12 text-center">
            <div className="mx-auto grid h-12 w-12 place-items-center rounded-xl bg-primary/10 text-primary">
              <Sparkles className="h-6 w-6" />
            </div>
            <p className="mt-4 font-medium">Generate a batch of realistic revenue-loss cases</p>
            <p className="mx-auto mt-1 max-w-md text-sm text-muted-foreground">
              Each case flows through the full pipeline: ML probability → AI decision → guardrails →
              measured outcome. Metrics below are computed from the run, never hardcoded.
            </p>
          </Card>
        )}

        {result && (
          <>
            <div className="flex items-center gap-2 rounded-xl border border-warning/30 bg-warning/[0.06] px-4 py-2.5">
              <span className="inline-flex items-center gap-1.5 rounded-md bg-warning px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-white">
                Demo / Simulation
              </span>
              <p className="text-[12.5px] text-muted-foreground">
                Projected results on a synthetic batch — <span className="font-medium text-foreground">not real
                historical business data</span>. Every number is computed live from this run.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
              <Metric label="Cases" value={result.num_cases.toLocaleString()} />
              <Metric label="Simulated Revenue at Risk" value={formatINRShort(result.revenue_at_risk)} accent="danger" />
              <Metric label="AI Analyzed" value={result.ai_analyzed.toLocaleString()} accent="primary" />
              <Metric label="Recovery Attempts" value={result.recovery_attempts.toLocaleString()} accent="info" />
              <Metric label="Simulated Revenue Recovered" value={formatINRShort(result.revenue_recovered)} accent="success" />
              <Metric label="Simulated Recovery Rate" value={`${result.recovery_rate.toFixed(1)}%`} accent="success" />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Intervention Performance</CardTitle>
                  <p className="text-xs text-muted-foreground">
                    {result.do_nothing_count.toLocaleString()} cases were deliberately left alone (Do Nothing).
                  </p>
                </CardHeader>
                <CardContent>
                  <div className="h-[260px]">
                    <InterventionBar data={result.intervention_performance} />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recovery Funnel</CardTitle>
                </CardHeader>
                <CardContent>
                  <RecoveryFunnel stages={result.funnel} />
                </CardContent>
              </Card>
            </div>

            {result.persisted && (
              <Card className="flex items-center gap-3 border-success/30 bg-success/5 p-4">
                <Activity className="h-5 w-5 text-success" />
                <p className="text-sm">
                  Cases persisted to the database — the dashboard, cases, and audit trail now include this run.
                </p>
              </Card>
            )}
          </>
        )}
      </div>
    </>
  );
}

function Metric({
  label,
  value,
  accent = "primary",
}: {
  label: string;
  value: string;
  accent?: "primary" | "success" | "danger" | "info";
}) {
  const color = {
    primary: "text-primary",
    success: "text-success",
    danger: "text-danger",
    info: "text-info",
  }[accent];
  return (
    <Card className="p-4">
      <p className="eyebrow">{label}</p>
      <p className={`mt-2.5 font-display text-[26px] font-semibold leading-none tabular-nums ${color}`}>{value}</p>
    </Card>
  );
}

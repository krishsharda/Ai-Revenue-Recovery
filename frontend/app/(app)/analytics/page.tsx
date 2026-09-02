import { Topbar } from "@/components/layout/topbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiErrorState } from "@/components/shared/states";
import { RecoveryFunnel } from "@/components/charts/recovery-funnel";
import { ActionDistribution } from "@/components/charts/action-distribution";
import { RiskDonut } from "@/components/charts/risk-donut";
import { PerfBars } from "@/components/shared/perf-bars";
import { api } from "@/lib/api";
import { formatINR, titleCase } from "@/lib/format";
import type { AnalyticsResponse } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function AnalyticsPage() {
  let data: AnalyticsResponse;
  try {
    data = await api.analytics();
  } catch (e) {
    return (
      <>
        <Topbar title="Analytics" />
        <div className="p-5">
          <ApiErrorState error={(e as Error).message} />
        </div>
      </>
    );
  }

  return (
    <>
      <Topbar title="Analytics" subtitle="Intervention performance, funnel, and recovery memory" />
      <div className="space-y-4 p-5">
        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Intervention Performance</CardTitle>
              <p className="text-xs text-muted-foreground">
                Recovery success rate by action. Do-Nothing is intentional (N/A).
              </p>
            </CardHeader>
            <CardContent>
              <PerfBars data={data.intervention_performance} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Risk Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[220px]">
                <RiskDonut data={data.risk_distribution} />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Recovery Funnel</CardTitle>
            </CardHeader>
            <CardContent>
              <RecoveryFunnel stages={data.funnel} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Action Mix</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[240px]">
                <ActionDistribution data={data.action_counts} />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recovery memory */}
        <Card>
          <CardHeader>
            <CardTitle>Recovery Memory</CardTitle>
            <p className="text-xs text-muted-foreground">
              Outcome-based recovery intelligence — historical success rates by root cause + action
              feed future recommendations and the expected-value comparison. Measured statistics, not
              reinforcement learning.
            </p>
          </CardHeader>
          <CardContent>
            {data.recovery_memory.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No learned outcomes yet — execute cases or run a persisted simulation.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-muted-foreground">
                      <th className="py-2 font-medium">Action · Root cause</th>
                      <th className="py-2 font-medium">Attempts</th>
                      <th className="py-2 font-medium">Successes</th>
                      <th className="py-2 font-medium">Success rate</th>
                      <th className="py-2 font-medium">Recovered</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.recovery_memory.map((m, idx) => (
                      <tr key={`${m.action_type}-${idx}`} className="border-b border-border/50 last:border-0">
                        <td className="py-2.5 font-medium">{titleCase(m.action_type)}</td>
                        <td className="py-2.5 tabular-nums">{m.attempts}</td>
                        <td className="py-2.5 tabular-nums">{m.successes}</td>
                        <td className="py-2.5 tabular-nums font-semibold">
                          {m.success_rate === null ? "N/A" : `${Math.round(m.success_rate * 100)}%`}
                        </td>
                        <td className="py-2.5 tabular-nums">{formatINR(m.recovered_amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}

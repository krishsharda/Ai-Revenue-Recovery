import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Layers,
  Percent,
  ShoppingCart,
  TrendingUp,
  Wallet,
} from "lucide-react";
import { Topbar } from "@/components/layout/topbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/shared/stat-card";
import { ApiErrorState, SectionHeader } from "@/components/shared/states";
import { RecoveryFunnel } from "@/components/charts/recovery-funnel";
import { ActionDistribution } from "@/components/charts/action-distribution";
import { ActionBadge, ProbabilityBar, RiskBadge } from "@/components/shared/badges";
import { Avatar } from "@/components/shared/avatar";
import { api } from "@/lib/api";
import { formatINR, formatINRShort } from "@/lib/format";
import type { DashboardResponse } from "@/lib/types";

export const dynamic = "force-dynamic";

const METRIC_META: Record<string, { icon: any; accent: any }> = {
  "Revenue at Risk": { icon: AlertTriangle, accent: "danger" },
  "Revenue Recovered": { icon: Wallet, accent: "success" },
  "Recovery Rate": { icon: Percent, accent: "primary" },
  "Active Recovery Cases": { icon: Activity, accent: "info" },
};

const LOSS_ICON: Record<string, any> = {
  PAYMENT_FAILURE: AlertTriangle,
  CHECKOUT_ABANDONMENT: ShoppingCart,
  SUBSCRIPTION_FAILURE: Activity,
  OVERDUE_INVOICE: Layers,
};

export default async function DashboardPage() {
  let data: DashboardResponse;
  try {
    data = await api.dashboard();
  } catch (e) {
    return (
      <>
        <Topbar title="Overview" subtitle="Revenue recovery at a glance" />
        <div className="p-5">
          <ApiErrorState error={(e as Error).message} />
        </div>
      </>
    );
  }

  return (
    <>
      <Topbar title="Overview" subtitle="Revenue recovery at a glance · Razorpay Test Mode" />
      <div className="space-y-6 p-5">
        {/* Metric cards */}
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {data.metrics.map((m) => {
            const meta = METRIC_META[m.label] || { icon: TrendingUp, accent: "primary" };
            return (
              <StatCard
                key={m.label}
                label={m.label}
                value={m.display}
                sublabel={m.sublabel}
                icon={meta.icon}
                accent={meta.accent}
              />
            );
          })}
        </div>

        {/* Funnel + action distribution */}
        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Recovery Funnel</CardTitle>
              <p className="text-xs text-muted-foreground">
                Revenue flowing from at-risk to recovered — actual amounts at each stage.
              </p>
            </CardHeader>
            <CardContent>
              <RecoveryFunnel stages={data.funnel} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>AI Action Mix</CardTitle>
              <p className="text-xs text-muted-foreground">Next-best action chosen per case.</p>
            </CardHeader>
            <CardContent>
              <div className="h-[240px]">
                <ActionDistribution data={data.action_counts} />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Loss-type breakdown */}
        <div>
          <SectionHeader title="Revenue loss by type" hint="Amount currently at risk" />
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {data.loss_type_breakdown.map((b) => {
              const Icon = LOSS_ICON[b.loss_type] || AlertTriangle;
              return (
                <Card key={b.loss_type} className="p-4 transition-colors hover:border-foreground/20">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Icon className="h-3.5 w-3.5" />
                    <span className="eyebrow">{b.label}</span>
                  </div>
                  <p className="mt-3 font-display text-[26px] font-semibold leading-none tabular-nums">
                    {formatINRShort(b.amount_at_risk)}
                  </p>
                  <p className="mt-1.5 text-[11.5px] text-muted-foreground">
                    {b.count} active case{b.count === 1 ? "" : "s"}
                  </p>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Email recovery (real Resend stats) */}
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>Email Recovery</CardTitle>
            <span
              className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.12em] ${
                data.email.configured
                  ? "border-success/25 bg-success/10 text-success"
                  : "border-border bg-muted/60 text-muted-foreground"
              }`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${data.email.configured ? "bg-success" : "bg-muted-foreground"}`} />
              {data.email.configured ? "Resend Connected" : "Resend Not Configured"}
            </span>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <EmailStat label="Emails Sent" value={data.email.sent.toLocaleString()} tone="text-success" />
              <EmailStat label="Emails Failed" value={data.email.failed.toLocaleString()} tone="text-danger" />
              <EmailStat label="Cases Converted" value={data.email.recoveries.toLocaleString()} />
              <EmailStat label="Recovered via Email" value={formatINRShort(data.email.recovered_amount)} tone="text-success" />
            </div>
            {!data.email.configured && (
              <p className="mt-4 text-[12px] text-muted-foreground">
                Real emails are disabled. Add <code className="rounded bg-muted px-1 py-0.5 font-mono text-[11px]">RESEND_API_KEY</code>{" "}
                and <code className="rounded bg-muted px-1 py-0.5 font-mono text-[11px]">EMAIL_FROM</code>, then manage it in{" "}
                <Link href="/settings" className="text-primary hover:underline">Settings</Link>.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Top opportunities */}
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>Top Recovery Opportunities</CardTitle>
            <Link href="/cases" className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline">
              View all cases <ArrowUpRight className="h-3 w-3" />
            </Link>
          </CardHeader>
          <CardContent className="pt-1">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-muted-foreground">
                    <th className="pb-2 font-medium">Customer</th>
                    <th className="pb-2 font-medium">Amount</th>
                    <th className="pb-2 font-medium">Risk</th>
                    <th className="pb-2 font-medium">Recovery Probability</th>
                    <th className="pb-2 font-medium">AI Recommendation</th>
                    <th className="pb-2" />
                  </tr>
                </thead>
                <tbody>
                  {data.top_opportunities.map((o) => (
                    <tr key={o.case_id} className="border-b border-border/60 last:border-0">
                      <td className="py-3">
                        <span className="flex items-center gap-2.5">
                          <Avatar name={o.customer_name} size="sm" />
                          <span className="font-medium">{o.customer_name}</span>
                        </span>
                      </td>
                      <td className="py-3 tabular-nums font-semibold">{formatINR(o.amount)}</td>
                      <td className="py-3"><RiskBadge risk={o.risk_level} /></td>
                      <td className="py-3"><ProbabilityBar value={o.recovery_probability} /></td>
                      <td className="py-3"><ActionBadge action={o.recommended_action} /></td>
                      <td className="py-3 text-right">
                        <Link href={`/cases/${o.case_id}`} className="text-xs font-medium text-primary hover:underline">
                          Open
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function EmailStat({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div>
      <p className="eyebrow">{label}</p>
      <p className={`mt-1.5 font-display text-[22px] font-semibold tabular-nums ${tone || ""}`}>{value}</p>
    </div>
  );
}

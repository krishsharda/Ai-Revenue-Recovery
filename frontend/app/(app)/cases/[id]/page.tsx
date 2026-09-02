import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  BrainCircuit,
  CheckCircle2,
  CreditCard,
  Sparkles,
  UserRound,
} from "lucide-react";
import { Topbar } from "@/components/layout/topbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiErrorState } from "@/components/shared/states";
import {
  ActionBadge,
  ExecutionModeBadge,
  RiskBadge,
  StatusBadge,
} from "@/components/shared/badges";
import { Timeline } from "@/components/cases/timeline";
import { ExecuteButton } from "@/components/cases/execute-button";
import { AnalyzeButton } from "@/components/cases/analyze-button";
import { ActionRef } from "@/components/cases/action-ref";
import { StrategyComparison } from "@/components/cases/strategy-comparison";
import { Communications } from "@/components/cases/communications";
import { Avatar } from "@/components/shared/avatar";
import { RadialGauge } from "@/components/shared/radial-gauge";
import { api } from "@/lib/api";
import { formatINR, formatPct, titleCase } from "@/lib/format";
import type { RecoveryCaseDetail } from "@/lib/types";

export const dynamic = "force-dynamic";

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-border/50 py-2 last:border-0">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-right">{children}</span>
    </div>
  );
}

export default async function CaseDetailPage({ params }: { params: { id: string } }) {
  const id = Number(params.id);
  let c: RecoveryCaseDetail;
  try {
    c = await api.case(id);
  } catch (e) {
    if ((e as Error).message.includes("404")) notFound();
    return (
      <>
        <Topbar title={`Case #${id}`} />
        <div className="p-5">
          <ApiErrorState error={(e as Error).message} />
        </div>
      </>
    );
  }

  const terminal = ["RECOVERED", "FAILED", "CLOSED", "DO_NOTHING", "ABANDONED"].includes(c.status);
  const latest = c.decisions[c.decisions.length - 1];
  const successRate =
    c.customer.total_transactions > 0
      ? c.customer.successful_transactions / c.customer.total_transactions
      : 0;
  const explain = c.explainability.length
    ? c.explainability
    : latest?.reason
    ? [latest.reason]
    : [];

  return (
    <>
      <Topbar title={`${c.customer.name}`} subtitle={`Recovery case #${c.id} · ${titleCase(c.loss_type)}`} />
      <div className="space-y-5 p-5">
        <Link
          href="/cases"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to cases
        </Link>

        {/* Header */}
        <Card className="overflow-hidden bg-gradient-to-br from-card to-primary/5">
          <CardContent className="flex flex-col gap-6 p-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-5">
              <Avatar name={c.customer.name} size="lg" />
              <div className="flex flex-wrap items-center gap-x-8 gap-y-3">
                <div>
                  <p className="eyebrow">Amount at risk</p>
                  <p className="mt-1.5 font-display text-[38px] font-semibold leading-none tracking-tightest tabular-nums">
                    {formatINR(c.transaction.amount)}
                  </p>
                  <div className="mt-2 flex gap-2">
                    <RiskBadge risk={c.risk_level} />
                    <StatusBadge status={c.status} />
                  </div>
                </div>
                <div>
                  <p className="eyebrow">Expected recovery</p>
                  <p className="mt-1.5 font-display text-2xl font-semibold tabular-nums">
                    {formatINR(c.expected_recovery_value)}
                  </p>
                  <div className="mt-2"><ActionBadge action={c.recommended_action} /></div>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <RadialGauge value={c.recovery_probability} size={116} sublabel="recovery" />
              <div className="flex flex-col gap-2">
                <ExecuteButton caseId={c.id} terminal={terminal} />
                <AnalyzeButton caseId={c.id} />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Real vs simulated banner */}
        <div
          className={`flex items-center gap-3 rounded-xl border px-4 py-2.5 text-sm ${
            c.transaction.is_synthetic
              ? "border-warning/30 bg-warning/5 text-warning"
              : "border-success/30 bg-success/5 text-success"
          }`}
        >
          <span className="h-2 w-2 rounded-full bg-current" />
          {c.transaction.is_synthetic
            ? "Synthetic demo transaction — recovery actions run as clearly-labelled simulations."
            : "Real Razorpay Test event — recovery actions create real Razorpay test artifacts."}
        </div>

        {/* Expected-recovery-by-strategy comparison (the core decision surface) */}
        {c.intervention_options?.length > 0 && (
          <Card className="p-5">
            <StrategyComparison options={c.intervention_options} reason={latest?.reason} />
          </Card>
        )}

        {/* Three panels */}
        <div className="grid gap-4 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-4 w-4 text-info" /> Transaction
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <Row label="Amount">{formatINR(c.transaction.amount)} {c.transaction.currency}</Row>
              <Row label="Payment method">{titleCase(c.transaction.payment_method)}</Row>
              <Row label="Failure reason">{titleCase(c.transaction.failure_reason)}</Row>
              <Row label="Loss type">{titleCase(c.transaction.loss_type)}</Row>
              <Row label="Razorpay payment ID">
                <span className="font-mono text-xs">{c.transaction.razorpay_payment_id || "—"}</span>
              </Row>
              <Row label="Razorpay order ID">
                <span className="font-mono text-xs">{c.transaction.razorpay_order_id || "—"}</span>
              </Row>
              <Row label="Source">
                {c.transaction.is_synthetic ? (
                  <span className="text-warning">Synthetic / Demo</span>
                ) : (
                  <span className="text-success">Real Razorpay Test Event</span>
                )}
              </Row>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserRound className="h-4 w-4 text-primary" /> Customer Behaviour
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <Row label="Previous payments">{c.customer.successful_transactions}</Row>
              <Row label="Previous failures">{c.customer.failed_transactions}</Row>
              <Row label="Success rate">{formatPct(successRate)}</Row>
              <Row label="Historical recovery rate">{formatPct(c.customer.historical_recovery_rate)}</Row>
              <Row label="Customer value">
                <span className="capitalize">{c.customer.customer_value}</span>
              </Row>
              <Row label="Avg payment">{formatINR(c.customer.average_payment_amount)}</Row>
              <Row label="Opted out of messaging">{c.customer.opted_out ? "Yes" : "No"}</Row>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BrainCircuit className="h-4 w-4 text-primary" /> AI Analysis
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <Row label="Risk level"><RiskBadge risk={c.risk_level} /></Row>
              <Row label="Recovery probability">{formatPct(c.recovery_probability)}</Row>
              <Row label="Root cause">{c.root_cause ? titleCase(c.root_cause) : "—"}</Row>
              <Row label="Recommended action"><ActionBadge action={c.recommended_action} /></Row>
              <Row label="Channel">{titleCase(c.recommended_channel)}</Row>
              <Row label="Confidence">{latest ? formatPct(latest.confidence) : "—"}</Row>
              <Row label="Decided by">
                {c.decided_by === "llm" ? (
                  <span className="text-accent">AI · LLM</span>
                ) : c.decided_by === "heuristic_fallback" ? (
                  <span className="text-warning" title={c.fallback_reason || ""}>
                    Heuristic · fallback
                  </span>
                ) : (
                  <span>Heuristic engine</span>
                )}
              </Row>
              {c.decided_by === "heuristic_fallback" && c.fallback_reason && (
                <Row label="Fallback reason">
                  <span className="font-mono text-[11px] text-warning">{c.fallback_reason}</span>
                </Row>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Explainability */}
        <Card className="bg-gradient-to-br from-card to-primary/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" /> Why did the AI choose this?
            </CardTitle>
            {latest?.reason && <p className="text-xs text-muted-foreground">{latest.reason}</p>}
          </CardHeader>
          <CardContent className="pt-0">
            <ul className="grid gap-2 sm:grid-cols-2">
              {explain.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                  <span>{s}</span>
                </li>
              ))}
            </ul>
            {c.recommended_action && (
              <div className="mt-4 flex items-center gap-2 rounded-xl border border-primary/20 bg-primary/5 px-4 py-3">
                <span className="eyebrow">Therefore</span>
                <ActionBadge action={c.recommended_action} />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Email communications (real Resend records) */}
        {(c.communications?.length > 0 || c.recommended_action === "EMAIL") && (
          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle>Email Communications</CardTitle>
              <span className="eyebrow">Resend · delivery ≠ recovery</span>
            </CardHeader>
            <CardContent>
              <Communications items={c.communications} />
            </CardContent>
          </Card>
        )}

        {/* Timeline + actions */}
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Recovery Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <Timeline events={c.events} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Actions Taken</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {c.actions.length === 0 && (
                <p className="text-sm text-muted-foreground">No recovery action executed yet.</p>
              )}
              {c.actions.map((a) => (
                <div key={a.id} className="rounded-xl border border-border/70 bg-muted/20 p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <ActionBadge action={a.action_type} />
                      <span className="text-xs text-muted-foreground">attempt {a.attempt_number}</span>
                    </div>
                    <ExecutionModeBadge mode={a.execution_mode} />
                  </div>
                  {a.result && <p className="mt-2 text-xs text-muted-foreground">{a.result}</p>}
                  {a.external_reference && <ActionRef reference={a.external_reference} />}
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}

"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { CheckCircle2, Loader2, PlayCircle, RefreshCw, XCircle } from "lucide-react";
import { api } from "@/lib/api";
import type { ExecuteResult } from "@/lib/types";

export function ExecuteButton({ caseId, terminal }: { caseId: number; terminal: boolean }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ExecuteResult["result"] | null>(null);

  // Same reason as AnalyzeButton: `router.refresh()` doesn't return a promise,
  // so without a transition the button reported success while the timeline and
  // status badge on the page were still showing the pre-execution state.
  const [refreshing, startTransition] = useTransition();
  const busy = loading || refreshing;

  async function run(force = false) {
    setLoading(true);
    setResult(null);
    try {
      const res = await api.executeCase(caseId, { simulate: true, force });
      setResult(res.result);
      startTransition(() => router.refresh());
    } catch (e) {
      setResult({ status: "error", reason: (e as Error).message });
    } finally {
      setLoading(false);
    }
  }

  const recovered = result?.outcome === "RECOVERED";
  const noAction = result?.status === "do_nothing";

  return (
    <div className="flex flex-col items-end gap-2">
      <button
        onClick={() => run(terminal)}
        disabled={busy}
        className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/20 transition-all hover:bg-primary/90 disabled:opacity-60"
      >
        {busy ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : terminal ? (
          <RefreshCw className="h-4 w-4" />
        ) : (
          <PlayCircle className="h-4 w-4" />
        )}
        {loading
          ? "Executing…"
          : refreshing
          ? "Updating…"
          : terminal
          ? "Re-run Recovery"
          : "Execute Recovery Action"}
      </button>

      {result?.status === "error" && (
        <div className="w-full max-w-[280px] rounded-xl border border-danger/30 bg-danger/[0.06] p-3">
          <p className="eyebrow text-danger">Execution Failed</p>
          <p className="mt-1 break-words text-[11.5px] leading-snug text-danger/90">
            {result.reason || "The action could not be completed."}
          </p>
        </div>
      )}

      {result && result.status !== "error" && (() => {
        const real = result.execution_mode === "REAL_RAZORPAY_TEST";
        const heading = noAction
          ? "AI stood down — Do Nothing"
          : real
          ? "Real Razorpay Test Event"
          : "Simulated Recovery Action";
        return (
          <div className="w-full max-w-[280px] rounded-xl border border-border bg-card p-3 sheen">
            <p className="eyebrow">Execution Result</p>
            <div className="mt-1 flex items-center gap-2">
              <span
                className={`inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 font-mono text-[9.5px] font-semibold uppercase tracking-[0.08em] ${
                  real ? "bg-success text-white" : "bg-warning text-white"
                }`}
              >
                {real ? "Razorpay Test" : "Simulated"}
              </span>
              <span className="text-[13px] font-semibold">{heading}</span>
            </div>
            {result.detail && (
              <p className="mt-1.5 text-[11.5px] leading-snug text-muted-foreground">{result.detail}</p>
            )}
            {result.outcome && (
              <div
                className={`mt-2 inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[11px] font-medium ${
                  recovered
                    ? "border-success/30 bg-success/10 text-success"
                    : "border-danger/30 bg-danger/10 text-danger"
                }`}
              >
                {recovered ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                {recovered ? "Recovered" : "Not recovered"}
              </div>
            )}
            <p className="mt-2 font-mono text-[9.5px] uppercase tracking-[0.1em] text-muted-foreground/70">
              No real customer was charged · Razorpay Test Mode
            </p>
          </div>
        );
      })()}
    </div>
  );
}

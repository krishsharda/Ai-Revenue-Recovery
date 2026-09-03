"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { AlertCircle, BrainCircuit, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { titleCase } from "@/lib/format";

export function AnalyzeButton({ caseId }: { caseId: number }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [by, setBy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // `router.refresh()` is fire-and-forget, so releasing the button in a
  // `finally` used to mark the action done while the page still showed stale
  // data. Running the refresh inside a transition keeps `isPending` true until
  // the new server render actually commits.
  const [refreshing, startTransition] = useTransition();
  const busy = loading || refreshing;

  async function run() {
    setLoading(true);
    setBy(null);
    setError(null);
    try {
      const detail = await api.analyzeCase(caseId);
      const latest = detail.decisions[detail.decisions.length - 1];
      setBy(latest?.decided_by ?? null);
      startTransition(() => router.refresh());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        onClick={run}
        disabled={busy}
        className="inline-flex items-center gap-2 rounded-xl border border-border bg-muted/40 px-4 py-2.5 text-sm font-semibold transition-colors hover:bg-muted disabled:opacity-60"
      >
        {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <BrainCircuit className="h-4 w-4 text-primary" />}
        {loading ? "Analyzing…" : refreshing ? "Updating…" : "Analyze with AI"}
      </button>
      {by && !error && (
        <span className="text-[11px] text-muted-foreground">
          Decided by <span className="font-semibold text-foreground">{titleCase(by)}</span>
        </span>
      )}
      {error && (
        <span className="inline-flex max-w-[260px] items-start gap-1 text-right text-[11px] text-danger">
          <AlertCircle className="mt-px h-3 w-3 shrink-0" />
          {error}
        </span>
      )}
    </div>
  );
}

"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { BrainCircuit, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { titleCase } from "@/lib/format";

export function AnalyzeButton({ caseId }: { caseId: number }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [by, setBy] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setBy(null);
    try {
      const detail = await api.analyzeCase(caseId);
      const latest = detail.decisions[detail.decisions.length - 1];
      setBy(latest?.decided_by ?? null);
      router.refresh();
    } catch {
      setBy("error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        onClick={run}
        disabled={loading}
        className="inline-flex items-center gap-2 rounded-xl border border-border bg-muted/40 px-4 py-2.5 text-sm font-semibold transition-colors hover:bg-muted disabled:opacity-60"
      >
        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <BrainCircuit className="h-4 w-4 text-primary" />}
        {loading ? "Analyzing…" : "Analyze with AI"}
      </button>
      {by && by !== "error" && (
        <span className="text-[11px] text-muted-foreground">
          Decided by <span className="font-semibold text-foreground">{titleCase(by)}</span>
        </span>
      )}
    </div>
  );
}

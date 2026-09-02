"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, RefreshCw, ShieldCheck } from "lucide-react";
import { Topbar } from "@/components/layout/topbar";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ApiErrorState, EmptyState } from "@/components/shared/states";
import { api } from "@/lib/api";
import { formatTime, titleCase } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { AuditLogOut } from "@/lib/types";

function resultStyle(result: string | null): string {
  if (!result) return "bg-muted text-muted-foreground border-border";
  const r = result.toUpperCase();
  if (["APPROVED", "RECOVERED", "SUCCESS", "CAPTURED", "SUCCEEDED"].includes(r))
    return "bg-success/15 text-success border-success/30";
  if (["BLOCKED", "INVALID_SIGNATURE", "ERROR", "REJECTED", "FAILED"].includes(r))
    return "bg-danger/15 text-danger border-danger/30";
  if (["DOWNGRADED", "DO_NOTHING"].includes(r))
    return "bg-warning/15 text-warning border-warning/30";
  return "bg-info/15 text-info border-info/30";
}

export default function AuditPage() {
  const [items, setItems] = useState<AuditLogOut[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [event, setEvent] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.auditLogs({ limit: 200, event: event || undefined });
      setItems(res.items);
      setTotal(res.total);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [event]);

  useEffect(() => {
    load();
  }, [load]);

  const events = Array.from(new Set(items.map((i) => i.event)));

  return (
    <>
      <Topbar title="Audit Trail" subtitle="Every decision, guardrail check, and action — for trust and compliance" />
      <div className="space-y-4 p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <ShieldCheck className="h-4 w-4 text-success" />
            <span>
              <span className="font-semibold text-foreground">{total.toLocaleString()}</span> audit records
            </span>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={event}
              onChange={(e) => setEvent(e.target.value)}
              className="h-9 rounded-xl border border-border bg-muted/30 px-3 text-sm outline-none focus:border-primary/40"
            >
              <option value="">All events</option>
              {events.map((e) => (
                <option key={e} value={e} className="bg-card">
                  {e}
                </option>
              ))}
            </select>
            <button
              onClick={load}
              className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-muted/30 px-3 py-2 text-sm font-medium hover:bg-muted"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              Refresh
            </button>
          </div>
        </div>

        {error ? (
          <ApiErrorState error={error} />
        ) : items.length === 0 && !loading ? (
          <EmptyState title="No audit records" />
        ) : (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-muted-foreground">
                    <th className="px-5 py-3 font-medium">Time</th>
                    <th className="px-3 py-3 font-medium">Event</th>
                    <th className="px-3 py-3 font-medium">Actor</th>
                    <th className="px-3 py-3 font-medium">Action</th>
                    <th className="px-3 py-3 font-medium">Result</th>
                    <th className="px-3 py-3 font-medium">Case</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((a) => (
                    <tr key={a.id} className="border-b border-border/50 last:border-0 hover:bg-muted/20">
                      <td className="whitespace-nowrap px-5 py-2.5 font-mono text-xs text-muted-foreground">
                        {formatTime(a.created_at)}
                      </td>
                      <td className="px-3 py-2.5 font-medium">{a.event}</td>
                      <td className="px-3 py-2.5 text-muted-foreground">{a.actor}</td>
                      <td className="px-3 py-2.5 text-xs">{a.action ? titleCase(a.action) : "—"}</td>
                      <td className="px-3 py-2.5">
                        {a.result ? (
                          <Badge className={cn("normal-case", resultStyle(a.result))}>
                            {titleCase(a.result)}
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-3 py-2.5 text-xs text-muted-foreground">
                        {a.recovery_case_id ? (
                          <a href={`/cases/${a.recovery_case_id}`} className="text-primary hover:underline">
                            #{a.recovery_case_id}
                          </a>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </>
  );
}

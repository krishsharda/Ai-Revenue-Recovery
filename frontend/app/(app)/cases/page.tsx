import Link from "next/link";
import { Suspense } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Topbar } from "@/components/layout/topbar";
import { Card } from "@/components/ui/card";
import { FilterBar } from "@/components/cases/filter-bar";
import { ActionBadge, ProbabilityBar, RiskBadge, StatusBadge } from "@/components/shared/badges";
import { Avatar } from "@/components/shared/avatar";
import { ApiErrorState, EmptyState } from "@/components/shared/states";
import { api } from "@/lib/api";
import { formatINR, titleCase } from "@/lib/format";
import type { PaginatedCases } from "@/lib/types";

export const dynamic = "force-dynamic";

// Rendering all 100 cases at once produced a ~600 KB HTML document (markup plus
// the RSC payload that mirrors it), which the browser had to parse and hydrate
// on every visit. A page of 25 keeps the document about a quarter of that size
// and the table interactive far sooner.
const PAGE_SIZE = 25;

function pageHref(searchParams: { [k: string]: string | undefined }, page: number): string {
  const qs = new URLSearchParams();
  for (const key of ["status", "risk_level", "loss_type", "search"]) {
    const value = searchParams[key];
    if (value) qs.set(key, value);
  }
  if (page > 1) qs.set("page", String(page));
  const q = qs.toString();
  return q ? `/cases?${q}` : "/cases";
}

export default async function CasesPage({
  searchParams,
}: {
  searchParams: { [k: string]: string | undefined };
}) {
  const page = Math.max(1, Number.parseInt(searchParams.page ?? "1", 10) || 1);

  let data: PaginatedCases | null = null;
  let error: string | null = null;
  try {
    data = await api.cases({
      status: searchParams.status,
      risk_level: searchParams.risk_level,
      loss_type: searchParams.loss_type,
      search: searchParams.search,
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
    });
  } catch (e) {
    error = (e as Error).message;
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;
  const rangeStart = data && data.items.length ? (page - 1) * PAGE_SIZE + 1 : 0;
  const rangeEnd = data ? (page - 1) * PAGE_SIZE + data.items.length : 0;

  return (
    <>
      <Topbar title="Recovery Cases" subtitle="Every at-risk transaction and its AI-decided next action" />
      <div className="space-y-4 p-5">
        <Suspense>
          <FilterBar />
        </Suspense>

        {error ? (
          <ApiErrorState error={error} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState title="No cases match" hint="Try clearing filters or running a simulation with persist enabled." />
        ) : (
          <Card className="overflow-hidden">
            <div className="flex items-center justify-between border-b border-border px-5 py-3 text-xs text-muted-foreground">
              <span>
                Showing{" "}
                <span className="font-semibold text-foreground">
                  {rangeStart}–{rangeEnd}
                </span>{" "}
                of {data.total} cases
              </span>
              <span>
                Page <span className="font-semibold text-foreground">{page}</span> of {totalPages}
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-muted-foreground">
                    <th className="px-5 py-3 font-medium">Customer</th>
                    <th className="px-3 py-3 font-medium">Amount</th>
                    <th className="px-3 py-3 font-medium">Failure</th>
                    <th className="px-3 py-3 font-medium">Risk</th>
                    <th className="px-3 py-3 font-medium">Recovery Probability</th>
                    <th className="px-3 py-3 font-medium">AI Recommendation</th>
                    <th className="px-3 py-3 font-medium">Status</th>
                    <th className="px-3 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((c) => {
                    const accent =
                      c.risk_level === "CRITICAL" ? "border-l-danger"
                        : c.risk_level === "HIGH" ? "border-l-warning"
                        : c.risk_level === "MEDIUM" ? "border-l-info"
                        : "border-l-border";
                    return (
                    <tr key={c.id} className={`group border-b border-l-2 border-border/50 ${accent} last:border-b-0 hover:bg-muted/30`}>
                      <td className="px-5 py-3">
                        <Link href={`/cases/${c.id}`} className="flex items-center gap-3">
                          <Avatar name={c.customer_name} size="sm" />
                          <span>
                            <span className="block font-medium">{c.customer_name}</span>
                            <span className="block text-xs capitalize text-muted-foreground">
                              {c.customer_value} value · {titleCase(c.loss_type)}
                            </span>
                          </span>
                        </Link>
                      </td>
                      <td className="px-3 py-3 tabular-nums font-semibold">{formatINR(c.amount)}</td>
                      <td className="px-3 py-3 text-xs text-muted-foreground">
                        {titleCase(c.failure_reason)}
                      </td>
                      <td className="px-3 py-3"><RiskBadge risk={c.risk_level} /></td>
                      <td className="px-3 py-3"><ProbabilityBar value={c.recovery_probability} /></td>
                      <td className="px-3 py-3"><ActionBadge action={c.recommended_action} /></td>
                      <td className="px-3 py-3"><StatusBadge status={c.status} /></td>
                      <td className="px-3 py-3 text-right">
                        <Link
                          href={`/cases/${c.id}`}
                          className="inline-flex text-muted-foreground group-hover:text-primary"
                        >
                          <ChevronRight className="h-4 w-4" />
                        </Link>
                      </td>
                    </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-between gap-3 border-t border-border px-5 py-3">
                <PageLink
                  href={pageHref(searchParams, page - 1)}
                  disabled={page <= 1}
                  label="Previous"
                  icon="prev"
                />
                <span className="text-xs text-muted-foreground">
                  {rangeStart}–{rangeEnd} of {data.total}
                </span>
                <PageLink
                  href={pageHref(searchParams, page + 1)}
                  disabled={page >= totalPages}
                  label="Next"
                  icon="next"
                />
              </div>
            )}
          </Card>
        )}
      </div>
    </>
  );
}

function PageLink({
  href,
  disabled,
  label,
  icon,
}: {
  href: string;
  disabled: boolean;
  label: string;
  icon: "prev" | "next";
}) {
  const Icon = icon === "prev" ? ChevronLeft : ChevronRight;
  const content = (
    <>
      {icon === "prev" && <Icon className="h-3.5 w-3.5" />}
      {label}
      {icon === "next" && <Icon className="h-3.5 w-3.5" />}
    </>
  );
  const base =
    "inline-flex items-center gap-1.5 rounded-[10px] border border-border px-3 py-1.5 text-[12.5px] font-medium";

  if (disabled) {
    return (
      <span aria-disabled className={`${base} cursor-not-allowed text-muted-foreground/50`}>
        {content}
      </span>
    );
  }
  return (
    <Link href={href} className={`${base} transition-colors hover:bg-muted`}>
      {content}
    </Link>
  );
}

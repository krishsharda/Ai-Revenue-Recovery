"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Search } from "lucide-react";
import { useCallback } from "react";

const SELECTS: { key: string; label: string; options: [string, string][] }[] = [
  {
    key: "status",
    label: "Status",
    options: [
      ["", "All statuses"],
      ["RECOMMENDED", "Recommended"],
      ["IN_RECOVERY", "In Recovery"],
      ["RECOVERED", "Recovered"],
      ["FAILED", "Failed"],
      ["DO_NOTHING", "Do Nothing"],
      ["CLOSED", "Closed"],
    ],
  },
  {
    key: "risk_level",
    label: "Risk",
    options: [
      ["", "All risk"],
      ["CRITICAL", "Critical"],
      ["HIGH", "High"],
      ["MEDIUM", "Medium"],
      ["LOW", "Low"],
    ],
  },
  {
    key: "loss_type",
    label: "Type",
    options: [
      ["", "All types"],
      ["PAYMENT_FAILURE", "Failed Payment"],
      ["CHECKOUT_ABANDONMENT", "Abandonment"],
      ["SUBSCRIPTION_FAILURE", "Subscription"],
      ["OVERDUE_INVOICE", "Overdue Invoice"],
    ],
  },
];

export function FilterBar() {
  const router = useRouter();
  const params = useSearchParams();

  const update = useCallback(
    (key: string, value: string) => {
      const next = new URLSearchParams(params.toString());
      if (value) next.set(key, value);
      else next.delete(key);
      router.push(`/cases?${next.toString()}`);
    },
    [params, router]
  );

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="relative flex-1 min-w-[200px]">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          defaultValue={params.get("search") || ""}
          onKeyDown={(e) => {
            if (e.key === "Enter") update("search", (e.target as HTMLInputElement).value);
          }}
          placeholder="Search customer…"
          className="h-10 w-full rounded-xl border border-border bg-muted/30 pl-9 pr-3 text-sm outline-none placeholder:text-muted-foreground focus:border-primary/40"
        />
      </div>
      {SELECTS.map((s) => (
        <select
          key={s.key}
          value={params.get(s.key) || ""}
          onChange={(e) => update(s.key, e.target.value)}
          className="h-10 rounded-xl border border-border bg-muted/30 px-3 text-sm outline-none focus:border-primary/40"
        >
          {s.options.map(([v, l]) => (
            <option key={v} value={v} className="bg-card">
              {l}
            </option>
          ))}
        </select>
      ))}
    </div>
  );
}

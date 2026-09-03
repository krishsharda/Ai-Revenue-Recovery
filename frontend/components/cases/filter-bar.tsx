"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, Search, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState, useTransition } from "react";

const SELECTS: { key: FilterKey; label: string; options: [string, string][] }[] = [
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

type FilterKey = "status" | "risk_level" | "loss_type" | "search";
type Filters = Record<FilterKey, string>;

const EMPTY: Filters = { status: "", risk_level: "", loss_type: "", search: "" };
const SEARCH_DEBOUNCE_MS = 350;

function read(params: URLSearchParams): Filters {
  return {
    status: params.get("status") || "",
    risk_level: params.get("risk_level") || "",
    loss_type: params.get("loss_type") || "",
    search: params.get("search") || "",
  };
}

function toQuery(f: Filters): string {
  const next = new URLSearchParams();
  (Object.keys(EMPTY) as FilterKey[]).forEach((k) => {
    if (f[k]) next.set(k, f[k]);
  });
  return next.toString();
}

export function FilterBar() {
  const router = useRouter();
  const params = useSearchParams();
  const qs = params.toString();

  // `draft` is what the controls render. Binding them straight to the URL made
  // every dropdown look frozen: the page is `force-dynamic`, so the URL only
  // updates once the server round-trip lands, and until then the select
  // snapped back to its old value. Local state paints the choice on the same
  // frame as the click; the transition below carries the data fetch.
  const [draft, setDraft] = useState<Filters>(() => read(params));
  const [pending, startTransition] = useTransition();

  // Re-sync when the URL changes from anywhere else (back/forward, a link).
  useEffect(() => {
    setDraft(read(new URLSearchParams(qs)));
  }, [qs]);

  const navigate = useCallback(
    (next: Filters) => {
      const query = toQuery(next);
      startTransition(() => {
        router.replace(query ? `/cases?${query}` : "/cases", { scroll: false });
      });
    },
    [router]
  );

  // Note: `next` is computed outside the state updater. Updaters must stay
  // pure — StrictMode invokes them twice, which would fire two navigations.
  const apply = useCallback(
    (key: FilterKey, value: string) => {
      const next = { ...draft, [key]: value };
      setDraft(next);
      navigate(next);
    },
    [draft, navigate]
  );

  // Search applies as you type rather than only on Enter, debounced so a word
  // costs one request instead of one per keystroke.
  const timer = useRef<ReturnType<typeof setTimeout>>();
  const onSearch = useCallback(
    (value: string) => {
      const next = { ...draft, search: value };
      setDraft(next);
      clearTimeout(timer.current);
      timer.current = setTimeout(() => navigate(next), SEARCH_DEBOUNCE_MS);
    },
    [draft, navigate]
  );

  useEffect(() => () => clearTimeout(timer.current), []);

  const dirty = (Object.keys(EMPTY) as FilterKey[]).some((k) => draft[k]);

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="relative min-w-[200px] flex-1">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={draft.search}
          onChange={(e) => onSearch(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              clearTimeout(timer.current);
              navigate(draft);
            }
          }}
          placeholder="Search customer…"
          name="search"
          id="cases-search"
          aria-label="Search cases by customer"
          className="h-10 w-full rounded-xl border border-border bg-muted/30 pl-9 pr-9 text-sm outline-none placeholder:text-muted-foreground focus:border-primary/40"
        />
        {pending && (
          <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-muted-foreground" />
        )}
      </div>

      {SELECTS.map((s) => (
        <select
          key={s.key}
          name={s.key}
          id={`cases-filter-${s.key}`}
          value={draft[s.key]}
          onChange={(e) => apply(s.key, e.target.value)}
          aria-label={s.label}
          className="h-10 rounded-xl border border-border bg-muted/30 px-3 text-sm outline-none focus:border-primary/40"
        >
          {s.options.map(([v, l]) => (
            <option key={v} value={v} className="bg-card">
              {l}
            </option>
          ))}
        </select>
      ))}

      {dirty && (
        <button
          type="button"
          onClick={() => {
            clearTimeout(timer.current);
            setDraft(EMPTY);
            navigate(EMPTY);
          }}
          className="inline-flex h-10 items-center gap-1.5 rounded-xl border border-border px-3 text-[13px] text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <X className="h-3.5 w-3.5" /> Clear
        </button>
      )}
    </div>
  );
}

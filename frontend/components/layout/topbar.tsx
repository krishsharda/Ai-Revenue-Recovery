"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Brain, Database, FlaskConical, Zap } from "lucide-react";
import { api } from "@/lib/api";
import type { AppConfig } from "@/lib/types";
import { cn } from "@/lib/utils";

function Pill({ on, onLabel, offLabel, icon: Icon }: { on: boolean; onLabel: string; offLabel: string; icon: typeof Zap }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.12em]",
        on ? "border-success/25 bg-success/10 text-success" : "border-border bg-muted/60 text-muted-foreground"
      )}
      title={on ? onLabel : offLabel}
    >
      <Icon className="h-3 w-3" />
      {on ? onLabel : offLabel}
    </span>
  );
}

export function Topbar({ title, subtitle }: { title: string; subtitle?: string }) {
  const [cfg, setCfg] = useState<AppConfig | null>(null);
  useEffect(() => {
    api.configCached().then(setCfg).catch(() => setCfg(null));
  }, []);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-border bg-background px-5 sm:px-6">
      <div className="min-w-0">
        {subtitle && <p className="eyebrow truncate">{subtitle}</p>}
        <h1 className="mt-0.5 truncate font-display text-[19px] font-semibold tracking-tight">{title}</h1>
      </div>

      <div className="flex items-center gap-2">
        <span className="hidden items-center gap-1.5 rounded-full border border-warning/25 bg-warning/10 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.12em] text-warning md:inline-flex">
          <span className="h-1.5 w-1.5 rounded-full bg-warning animate-pulse-soft" />
          Razorpay Test
        </span>
        {cfg && (
          <div className="hidden items-center gap-1.5 2xl:flex">
            <Pill on={cfg.features.llm_configured} onLabel={cfg.features.llm_provider || "LLM"} offLabel="Heuristic" icon={Brain} />
            <Pill on={cfg.features.razorpay_configured} onLabel="Razorpay" offLabel="Sim" icon={Zap} />
            <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted/60 px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
              <Database className="h-3 w-3" />
              {cfg.features.database_engine}
            </span>
          </div>
        )}
        <Link
          href="/simulation"
          className="inline-flex items-center gap-1.5 rounded-[10px] bg-primary px-3.5 py-2 text-[12.5px] font-semibold text-primary-foreground transition-all hover:brightness-95"
        >
          <FlaskConical className="h-3.5 w-3.5" />
          Simulate
        </Link>
      </div>
    </header>
  );
}

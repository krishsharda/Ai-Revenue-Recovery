"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  FlaskConical,
  LayoutDashboard,
  LogOut,
  Radar,
  ScrollText,
  Settings,
  Table2,
} from "lucide-react";
import { BrandMark } from "@/components/brand/brand-mark";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/command-center", label: "Command Center", icon: Radar },
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/cases", label: "Recovery Cases", icon: Table2 },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/simulation", label: "Simulation", icon: FlaskConical },
  { href: "/audit", label: "Audit Trail", icon: ScrollText },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="sticky top-0 hidden h-screen w-[252px] shrink-0 flex-col border-r border-border bg-surface lg:flex">
      <div className="flex h-16 items-center gap-3 border-b border-border px-5">
        <Link href="/" className="flex items-center gap-3">
          <BrandMark className="h-9 w-9" />
          <div className="leading-none">
            <p className="font-display text-[14px] font-semibold tracking-tight">Revenue Recovery</p>
            <p className="mt-1 font-mono text-[9px] uppercase tracking-[0.26em] text-muted-foreground">
              AI Platform
            </p>
          </div>
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-5">
        <p className="eyebrow px-3 pb-2">Workspace</p>
        <div className="space-y-0.5">
          {NAV.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group relative flex items-center gap-3 rounded-[10px] px-3 py-2.5 text-[13.5px] font-medium transition-colors",
                  active
                    ? "bg-muted text-foreground"
                    : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                )}
              >
                {active && (
                  <span className="absolute left-0 top-1/2 h-5 w-[2px] -translate-y-1/2 rounded-full bg-accent shadow-[0_0_8px_hsl(var(--accent))]" />
                )}
                <Icon className={cn("h-[17px] w-[17px] transition-colors", active ? "text-accent" : "text-muted-foreground group-hover:text-foreground")} />
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>

      <div className="border-t border-border p-4">
        <div className="rounded-xl border border-border bg-muted/50 p-3.5 sheen">
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-foreground/80">
            AI decides · Rules control
          </p>
          <p className="mt-1.5 text-[11.5px] leading-relaxed text-muted-foreground">
            Every recommendation clears the guardrail engine before a rupee moves.
          </p>
        </div>
        <Link
          href="/"
          className="mt-3 flex items-center gap-2 px-2 text-[12px] text-muted-foreground transition-colors hover:text-foreground"
        >
          <LogOut className="h-3.5 w-3.5" /> Exit to landing
        </Link>
      </div>
    </aside>
  );
}

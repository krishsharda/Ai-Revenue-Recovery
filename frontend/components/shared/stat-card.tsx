import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string;
  sublabel?: string | null;
  icon?: LucideIcon;
  accent?: "primary" | "success" | "warning" | "danger" | "info";
}

const iconTone: Record<string, string> = {
  primary: "text-foreground",
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
  info: "text-info",
};

const barTone: Record<string, string> = {
  primary: "bg-accent",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
  info: "bg-info",
};

export function StatCard({ label, value, sublabel, icon: Icon, accent = "primary" }: StatCardProps) {
  return (
    <Card className="group overflow-hidden p-5 transition-colors hover:border-foreground/20">
      <span className={cn("absolute left-0 top-5 h-8 w-[2px] rounded-full opacity-70", barTone[accent])} />
      <div className="flex items-start justify-between">
        <p className="eyebrow">{label}</p>
        {Icon && (
          <div className="grid h-8 w-8 place-items-center rounded-lg border border-border bg-muted/50">
            <Icon className={cn("h-4 w-4", iconTone[accent])} />
          </div>
        )}
      </div>
      <p className="mt-4 font-display text-[34px] font-semibold leading-none tracking-tightest tabular-nums">
        {value}
      </p>
      {sublabel && <p className="mt-2 text-[11.5px] text-muted-foreground">{sublabel}</p>}
    </Card>
  );
}

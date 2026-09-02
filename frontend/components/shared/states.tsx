import { AlertTriangle, Inbox } from "lucide-react";
import { Card } from "@/components/ui/card";

export function ApiErrorState({ error }: { error?: string }) {
  return (
    <Card className="border-danger/25 bg-danger/[0.04] p-8 text-center">
      <div className="mx-auto grid h-12 w-12 place-items-center rounded-xl border border-danger/20 bg-danger/10 text-danger">
        <AlertTriangle className="h-6 w-6" />
      </div>
      <h3 className="mt-4 font-display text-lg font-semibold">Can&apos;t reach the API</h3>
      <p className="mx-auto mt-1.5 max-w-md text-sm text-muted-foreground">
        The backend isn&apos;t responding. From{" "}
        <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">backend/</code> run{" "}
        <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">uvicorn app.main:app --port 8000</code>.
      </p>
      {error && <p className="mt-3 font-mono text-[11px] text-danger/80">{error}</p>}
    </Card>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="grid place-items-center rounded-2xl border border-dashed border-border p-12 text-center">
      <div className="grid h-12 w-12 place-items-center rounded-xl border border-border bg-muted/50 text-muted-foreground">
        <Inbox className="h-6 w-6" />
      </div>
      <p className="mt-3 font-display font-medium">{title}</p>
      {hint && <p className="mt-1 text-sm text-muted-foreground">{hint}</p>}
    </div>
  );
}

export function SectionHeader({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="mb-4 flex items-baseline justify-between gap-4">
      <h2 className="font-display text-[15px] font-semibold tracking-tight">{title}</h2>
      {hint && <span className="eyebrow shrink-0">{hint}</span>}
    </div>
  );
}

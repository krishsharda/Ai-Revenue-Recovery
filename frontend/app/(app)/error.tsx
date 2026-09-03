"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Card } from "@/components/ui/card";

/**
 * Segment error boundary. Without one, a throw in any server page unmounts the
 * whole app shell and the user is left on a blank screen with no way back —
 * the sidebar disappears along with the page. This keeps the shell intact and
 * offers a retry that re-runs just the failed segment.
 */
export default function AppError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error("Route segment failed:", error);
  }, [error]);

  return (
    <div className="grid flex-1 place-items-center p-6">
      <Card className="max-w-md border-danger/25 bg-danger/[0.04] p-8 text-center">
        <div className="mx-auto grid h-12 w-12 place-items-center rounded-xl border border-danger/20 bg-danger/10 text-danger">
          <AlertTriangle className="h-6 w-6" />
        </div>
        <h2 className="mt-4 font-display text-lg font-semibold">Something went wrong</h2>
        <p className="mt-1.5 text-sm text-muted-foreground">
          This page failed to load. The rest of the app is still usable.
        </p>
        {error.message && (
          <p className="mt-3 break-words font-mono text-[11px] text-danger/80">{error.message}</p>
        )}
        <button
          onClick={reset}
          className="mt-5 inline-flex items-center gap-2 rounded-[10px] bg-primary px-4 py-2.5 text-[13px] font-semibold text-primary-foreground transition-all hover:brightness-95"
        >
          <RefreshCw className="h-4 w-4" /> Try again
        </button>
      </Card>
    </div>
  );
}

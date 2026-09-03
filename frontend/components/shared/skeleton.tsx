import { cn } from "@/lib/utils";

/**
 * Placeholder block used by the route-level `loading.tsx` files.
 *
 * Every data page in the app is `force-dynamic`, so a navigation can't paint
 * until the server has finished talking to the API. Without a Suspense
 * fallback the browser simply sits on the old page while that happens and the
 * nav links read as broken. These skeletons give the router something to show
 * immediately, so a click always produces a visible response.
 */
export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("animate-pulse rounded-md bg-muted", className)} {...props} />;
}

/** Matches the height and chrome of the real `Topbar` so the header doesn't jump. */
export function TopbarSkeleton() {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-border bg-background px-5 sm:px-6">
      <div className="min-w-0 space-y-1.5">
        <Skeleton className="h-2.5 w-28" />
        <Skeleton className="h-4 w-44" />
      </div>
      <Skeleton className="h-8 w-32 rounded-[10px]" />
    </header>
  );
}

export function CardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("rounded-2xl border border-border bg-card p-5", className)}>
      <Skeleton className="h-2.5 w-24" />
      <Skeleton className="mt-3 h-7 w-32" />
      <Skeleton className="mt-3 h-2.5 w-20" />
    </div>
  );
}

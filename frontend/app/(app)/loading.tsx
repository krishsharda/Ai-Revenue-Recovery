import { CardSkeleton, Skeleton, TopbarSkeleton } from "@/components/shared/skeleton";

/**
 * Group-level fallback: covers every route under `(app)` that doesn't ship a
 * more specific one. Its presence is what makes sidebar navigation feel
 * instant — the router can commit the new route immediately and stream the
 * real content in behind it.
 */
export default function AppLoading() {
  return (
    <>
      <TopbarSkeleton />
      <div className="space-y-6 p-5">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="rounded-2xl border border-border bg-card p-5">
              <Skeleton className="h-4 w-40" />
              <Skeleton className="mt-5 h-[180px] w-full rounded-xl" />
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

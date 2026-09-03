import { Skeleton, TopbarSkeleton } from "@/components/shared/skeleton";

export default function CaseDetailLoading() {
  return (
    <>
      <TopbarSkeleton />
      <div className="space-y-6 p-5">
        <div className="rounded-2xl border border-border bg-card p-6">
          <div className="flex items-center gap-4">
            <Skeleton className="h-14 w-14 shrink-0 rounded-full" />
            <div className="space-y-2">
              <Skeleton className="h-5 w-48" />
              <Skeleton className="h-3 w-64" />
            </div>
          </div>
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-16 rounded-xl" />
            ))}
          </div>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="rounded-2xl border border-border bg-card p-5">
              <Skeleton className="h-4 w-36" />
              <Skeleton className="mt-4 h-[200px] w-full rounded-xl" />
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

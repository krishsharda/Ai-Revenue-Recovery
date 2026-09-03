import { Skeleton, TopbarSkeleton } from "@/components/shared/skeleton";

export default function CasesLoading() {
  return (
    <>
      <TopbarSkeleton />
      <div className="space-y-4 p-5">
        <div className="flex flex-wrap items-center gap-2">
          <Skeleton className="h-10 min-w-[200px] flex-1 rounded-xl" />
          <Skeleton className="h-10 w-[132px] rounded-xl" />
          <Skeleton className="h-10 w-[112px] rounded-xl" />
          <Skeleton className="h-10 w-[124px] rounded-xl" />
        </div>
        <div className="overflow-hidden rounded-2xl border border-border bg-card">
          <div className="border-b border-border px-5 py-3">
            <Skeleton className="h-3 w-40" />
          </div>
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 border-b border-border/50 px-5 py-3.5 last:border-b-0">
              <Skeleton className="h-8 w-8 shrink-0 rounded-full" />
              <div className="min-w-0 flex-1 space-y-1.5">
                <Skeleton className="h-3.5 w-36" />
                <Skeleton className="h-2.5 w-28" />
              </div>
              <Skeleton className="hidden h-3.5 w-20 sm:block" />
              <Skeleton className="hidden h-5 w-16 rounded-md md:block" />
              <Skeleton className="hidden h-3 w-[112px] lg:block" />
              <Skeleton className="hidden h-5 w-24 rounded-md lg:block" />
              <Skeleton className="h-5 w-20 rounded-md" />
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

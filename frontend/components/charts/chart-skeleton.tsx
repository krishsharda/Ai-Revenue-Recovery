/**
 * Fills the chart's container while recharts loads. Sized to `h-full` so the
 * card keeps its height and the chart swaps in without shifting the layout.
 */
export function ChartSkeleton() {
  return (
    <div className="grid h-full w-full place-items-center rounded-xl bg-muted/40">
      <span className="sr-only">Loading chart…</span>
      <div className="flex h-1/2 w-2/3 items-end justify-center gap-2" aria-hidden>
        {[0.55, 0.85, 0.4, 0.7, 0.5].map((h, i) => (
          <div
            key={i}
            className="w-full animate-pulse rounded-sm bg-muted"
            style={{ height: `${h * 100}%`, animationDelay: `${i * 90}ms` }}
          />
        ))}
      </div>
    </div>
  );
}

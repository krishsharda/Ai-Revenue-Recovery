import { cn } from "@/lib/utils";

/**
 * Custom monogram — a return-arc (revenue winning its way back) crossed with a
 * rising tick. Intentional, not a stock icon.
 */
export function BrandMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "relative grid shrink-0 place-items-center overflow-hidden rounded-[10px] border border-white/12 bg-[linear-gradient(150deg,#12161f,#080b12)] sheen",
        className
      )}
    >
      <span className="pointer-events-none absolute -right-3 -top-3 h-8 w-8 rounded-full bg-accent/25 blur-lg" />
      <svg viewBox="0 0 24 24" className="relative h-[58%] w-[58%]" fill="none">
        {/* return arc */}
        <path
          d="M20 12a8 8 0 1 1-2.3-5.6"
          stroke="#f2f4f8"
          strokeWidth="2"
          strokeLinecap="round"
        />
        {/* arrowhead */}
        <path
          d="M20 3.6v3.4h-3.4"
          stroke="#f2f4f8"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* rising tick */}
        <path
          d="M8.6 14.2l2.4-2.6 2 1.7 2.6-3.1"
          stroke="hsl(205 96% 62%)"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}

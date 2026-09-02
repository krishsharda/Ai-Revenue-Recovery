import { cn } from "@/lib/utils";

interface RadialGaugeProps {
  value: number; // 0..1
  size?: number;
  stroke?: number;
  label?: string;
  sublabel?: string;
  color?: string; // css color; defaults by value
  className?: string;
}

export function RadialGauge({
  value,
  size = 140,
  stroke = 12,
  label,
  sublabel,
  color,
  className,
}: RadialGaugeProps) {
  const v = Math.max(0, Math.min(1, value));
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const dash = c * v;
  const auto = v >= 0.7 ? "hsl(158 70% 45%)" : v >= 0.4 ? "hsl(38 95% 56%)" : "hsl(352 82% 62%)";
  const stroke_color = color || auto;

  return (
    <div className={cn("relative grid place-items-center", className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="hsl(214 26% 90%)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={stroke_color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${c - dash}`}
          style={{ transition: "stroke-dasharray 0.7s cubic-bezier(0.16,1,0.3,1)", filter: "drop-shadow(0 0 5px " + stroke_color + "55)" }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">
        <div>
          <p className="font-display text-[26px] font-semibold leading-none tabular-nums">
            {label ?? `${Math.round(v * 100)}%`}
          </p>
          {sublabel && <p className="mt-1.5 font-mono text-[9.5px] uppercase tracking-[0.18em] text-muted-foreground">{sublabel}</p>}
        </div>
      </div>
    </div>
  );
}

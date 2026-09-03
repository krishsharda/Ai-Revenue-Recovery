"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { ActionCount } from "@/lib/types";
import { titleCase } from "@/lib/format";
import { CHART, TOOLTIP_STYLE } from "./palette";

const RISK_COLOR: Record<string, string> = {
  CRITICAL: CHART.danger,
  HIGH: CHART.warning,
  MEDIUM: CHART.info,
  LOW: CHART.muted,
};

export function RiskDonutChart({ data }: { data: ActionCount[] }) {
  const chartData = data.map((d) => ({ name: titleCase(d.action_type), key: d.action_type, value: d.count }));
  const total = chartData.reduce((s, d) => s + d.value, 0);

  if (total === 0) {
    return <div className="grid h-full place-items-center text-sm text-muted-foreground">No data</div>;
  }

  return (
    <div className="relative h-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            innerRadius="62%"
            outerRadius="92%"
            paddingAngle={2}
            stroke="none"
          >
            {chartData.map((d) => (
              <Cell key={d.key} fill={RISK_COLOR[d.key] || CHART.muted} />
            ))}
          </Pie>
          <Tooltip contentStyle={TOOLTIP_STYLE} />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 grid place-items-center">
        <div className="text-center">
          <p className="font-display text-2xl font-semibold tabular-nums">{total}</p>
          <p className="font-mono text-[9.5px] uppercase tracking-[0.18em] text-muted-foreground">Cases</p>
        </div>
      </div>
    </div>
  );
}

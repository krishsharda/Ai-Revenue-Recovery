"use client";

import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { InterventionPerformance } from "@/lib/types";
import { titleCase } from "@/lib/format";
import { ACTION_COLORS, CHART, TOOLTIP_STYLE } from "./palette";

export function InterventionBar({ data }: { data: InterventionPerformance[] }) {
  const chartData = data
    .filter((d) => d.success_rate !== null)
    .map((d) => ({
      name: titleCase(d.action_type),
      key: d.action_type,
      rate: Math.round((d.success_rate || 0) * 100),
      attempts: d.attempts,
    }));

  if (chartData.length === 0) {
    return <div className="grid h-full place-items-center text-sm text-muted-foreground">No data</div>;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 40, top: 4, bottom: 4 }}>
        <XAxis type="number" domain={[0, 100]} hide />
        <YAxis type="category" dataKey="name" width={150} tick={{ fill: CHART.axis, fontSize: 12 }}
          tickLine={false} axisLine={false} />
        <Tooltip
          cursor={{ fill: "hsl(220 16% 20% / 0.35)" }}
          formatter={(v: number, _n, p: any) => [`${v}%  (n=${p.payload.attempts})`, "success"]}
          contentStyle={TOOLTIP_STYLE}
        />
        <Bar dataKey="rate" radius={[0, 6, 6, 0]} barSize={18}>
          {chartData.map((d) => (
            <Cell key={d.key} fill={ACTION_COLORS[d.key] || CHART.primary} />
          ))}
          <LabelList dataKey="rate" position="right" formatter={(v: number) => `${v}%`}
            style={{ fill: CHART.axis, fontSize: 11, fontWeight: 600 }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

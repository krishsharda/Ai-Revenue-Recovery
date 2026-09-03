"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ActionCount } from "@/lib/types";
import { titleCase } from "@/lib/format";
import { ACTION_COLORS, CHART, TOOLTIP_STYLE } from "./palette";

export function ActionDistributionChart({ data }: { data: ActionCount[] }) {
  const chartData = data.map((d) => ({
    name: titleCase(d.action_type),
    key: d.action_type,
    count: d.count,
  }));

  if (chartData.length === 0) {
    return <div className="grid h-full place-items-center text-sm text-muted-foreground">No data</div>;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="name"
          width={140}
          tick={{ fill: CHART.axis, fontSize: 12 }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip cursor={{ fill: "hsl(220 16% 20% / 0.35)" }} contentStyle={TOOLTIP_STYLE} />
        <Bar dataKey="count" radius={[0, 6, 6, 0]} barSize={18}>
          {chartData.map((d) => (
            <Cell key={d.key} fill={ACTION_COLORS[d.key] || CHART.primary} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

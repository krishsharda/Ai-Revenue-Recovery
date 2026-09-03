"use client";

import dynamic from "next/dynamic";
import { ChartSkeleton } from "./chart-skeleton";

// recharts accounts for roughly half of the ~200 kB first-load JS on the three
// routes that draw charts, and it has to be parsed before the page can hydrate.
// Loading it on demand lets those routes become interactive on the shared
// bundle instead, with a same-height placeholder holding the layout until the
// chart arrives.
export const RiskDonut = dynamic(
  () => import("./risk-donut.chart").then((m) => m.RiskDonutChart),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

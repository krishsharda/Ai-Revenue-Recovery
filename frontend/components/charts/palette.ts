// Shared chart palette — Nocturne (theme-consistent hsl strings for Recharts).
export const CHART = {
  accent: "hsl(217 91% 56%)",
  primary: "hsl(217 91% 56%)",
  info: "hsl(200 85% 48%)",
  success: "hsl(152 58% 40%)",
  warning: "hsl(30 90% 46%)",
  danger: "hsl(0 72% 54%)",
  violet: "hsl(250 74% 60%)",
  muted: "hsl(215 16% 55%)",
  grid: "hsl(214 24% 91%)",
  axis: "hsl(215 16% 47%)",
};

export const TOOLTIP_STYLE = {
  background: "hsl(0 0% 100%)",
  border: "1px solid hsl(214 24% 90%)",
  borderRadius: 12,
  color: "hsl(222 47% 11%)",
  fontSize: 12,
  fontFamily: "var(--font-mono)",
  boxShadow: "0 10px 30px rgb(15 23 42 / 0.12)",
};

export const SERIES = [
  CHART.accent,
  CHART.success,
  CHART.warning,
  CHART.violet,
  CHART.danger,
  CHART.info,
  "hsl(30 90% 62%)",
  CHART.muted,
];

export const ACTION_COLORS: Record<string, string> = {
  RETRY_PAYMENT: CHART.info,
  SCHEDULE_RETRY: "hsl(200 70% 48%)",
  PAYMENT_LINK: CHART.accent,
  ALTERNATE_PAYMENT_METHOD: CHART.success,
  EMAIL: CHART.warning,
  WHATSAPP: "hsl(158 60% 58%)",
  HUMAN_ESCALATION: "hsl(353 78% 60%)",
  DO_NOTHING: CHART.muted,
};

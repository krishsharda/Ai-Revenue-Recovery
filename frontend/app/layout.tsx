import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Revenue Recovery",
  description:
    "Every rupee that slipped away has a way back. AI detects, diagnoses, decides and recovers failed payments — bounded by deterministic guardrails.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-background font-sans antialiased">{children}</body>
    </html>
  );
}

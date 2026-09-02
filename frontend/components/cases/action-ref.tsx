"use client";

import { ExternalLink } from "lucide-react";

export function ActionRef({ reference }: { reference: string }) {
  const isHttp = reference.startsWith("http");

  if (isHttp) {
    return (
      <a
        href={reference}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-2 inline-flex items-center gap-1.5 rounded-lg border border-primary/30 bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary transition-colors hover:bg-primary/20"
      >
        <ExternalLink className="h-3 w-3" /> Open Razorpay test payment link
      </a>
    );
  }

  return <p className="mt-1 font-mono text-[11px] text-primary">{reference}</p>;
}

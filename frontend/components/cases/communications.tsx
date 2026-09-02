import { Mail, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { formatTime, titleCase } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { CommunicationOut } from "@/lib/types";

const STATUS: Record<string, string> = {
  SENT: "bg-success/12 text-success border-success/25",
  FAILED: "bg-danger/12 text-danger border-danger/25",
  BLOCKED: "bg-warning/12 text-warning border-warning/25",
  PENDING: "bg-info/12 text-info border-info/25",
};

export function Communications({ items }: { items: CommunicationOut[] }) {
  if (!items?.length) {
    return (
      <p className="text-sm text-muted-foreground">
        No email communications yet. When the AI selects EMAIL and guardrails pass, a real email is
        sent via Resend and recorded here.
      </p>
    );
  }
  return (
    <div className="space-y-3">
      {items.map((c) => (
        <div key={c.id} className="rounded-xl border border-border bg-muted/30 p-3.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-muted-foreground" />
              <span className="text-[13px] font-medium">{titleCase(c.channel)} · {titleCase(c.provider)}</span>
            </div>
            <Badge className={cn("whitespace-nowrap", STATUS[c.status] || STATUS.PENDING)}>{c.status}</Badge>
          </div>

          <dl className="mt-2.5 grid grid-cols-2 gap-x-4 gap-y-1.5 text-[12px]">
            <Field label="Recipient" value={c.recipient} mono />
            <Field label="Subject" value={c.subject} />
            <Field label="Provider ID" value={c.provider_message_id} mono />
            <Field label="Sent at" value={c.sent_at ? formatTime(c.sent_at) : null} />
          </dl>

          {c.payment_link && (
            <a href={c.payment_link} target="_blank" rel="noopener noreferrer"
              className="mt-2.5 inline-flex items-center gap-1.5 rounded-lg border border-primary/30 bg-primary/10 px-2.5 py-1 text-[11px] font-medium text-primary hover:bg-primary/20">
              <ExternalLink className="h-3 w-3" /> Razorpay test payment link
            </a>
          )}
          {c.failure_reason && (
            <p className="mt-2 font-mono text-[11px] text-danger">{c.failure_reason}</p>
          )}
        </div>
      ))}
    </div>
  );
}

function Field({ label, value, mono }: { label: string; value: string | null | undefined; mono?: boolean }) {
  return (
    <div className="min-w-0">
      <dt className="font-mono text-[9.5px] uppercase tracking-[0.12em] text-muted-foreground">{label}</dt>
      <dd className={cn("truncate", mono && "font-mono text-[11px]")}>{value || "—"}</dd>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, KeyRound, Loader2, Mail, Send, XCircle, Zap, BrainCircuit } from "lucide-react";
import { Topbar } from "@/components/layout/topbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, getAdminToken, setAdminToken } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { AppSettings, TestEmailResult } from "@/lib/types";

export default function SettingsPage() {
  const [cfg, setCfg] = useState<AppSettings | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [to, setTo] = useState("");
  const [sending, setSending] = useState(false);
  const [testResult, setTestResult] = useState<TestEmailResult | null>(null);
  const [token, setToken] = useState("");

  useEffect(() => {
    api.settings().then(setCfg).catch((e) => setErr((e as Error).message));
    setToken(getAdminToken());
  }, []);

  const email = cfg?.email;
  const connected = !!email?.connected;

  async function sendTest() {
    setSending(true);
    setTestResult(null);
    try {
      setTestResult(await api.sendTestEmail(to.trim()));
    } catch (e) {
      setTestResult({ ok: false, status: "BLOCKED", error: (e as Error).message });
    } finally {
      setSending(false);
    }
  }

  return (
    <>
      <Topbar title="Communication Settings" subtitle="Email · Razorpay · AI providers" />
      <div className="max-w-3xl space-y-5 p-5 sm:p-6">
        {/* Email */}
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-primary" /> Email
            </CardTitle>
            <StatusDot on={connected} onLabel="Connected" offLabel="Not Configured" />
          </CardHeader>
          <CardContent className="space-y-4">
            {connected ? (
              <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm sm:grid-cols-3">
                <Row label="Provider" value={email.provider} />
                <Row label="Environment" value={email.environment} />
                <Row label="Sender" value={email.sender} />
              </dl>
            ) : (
              <div className="rounded-xl border border-warning/30 bg-warning/[0.06] p-4 text-sm">
                <p className="font-medium">Real email recovery is disabled.</p>
                <p className="mt-1 text-muted-foreground">
                  Add <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">RESEND_API_KEY</code> and{" "}
                  <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">EMAIL_FROM</code> to your{" "}
                  <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">.env</code>, then restart the backend.
                  The API key is never displayed here.
                </p>
              </div>
            )}

            {/* Send Test Email */}
            <div className="border-t border-border pt-4">
              <p className="eyebrow mb-2">Send Test Email</p>
              <div className="flex flex-col gap-2 sm:flex-row">
                <input
                  type="email"
                  value={to}
                  onChange={(e) => setTo(e.target.value)}
                  placeholder="you@example.com"
                  className="h-10 flex-1 rounded-xl border border-border bg-card px-3 text-sm outline-none focus:border-primary/40"
                />
                <button
                  onClick={sendTest}
                  disabled={sending || !connected || !to}
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-primary px-4 text-[13px] font-semibold text-primary-foreground transition-all hover:brightness-95 disabled:opacity-50"
                >
                  {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  Send Test Email
                </button>
              </div>
              {!connected && (
                <p className="mt-2 text-[12px] text-muted-foreground">Configure Resend to enable test sends.</p>
              )}
              {testResult && (
                <div
                  className={cn(
                    "mt-3 flex items-center gap-2 rounded-lg border px-3 py-2 text-[13px]",
                    testResult.ok
                      ? "border-success/30 bg-success/10 text-success"
                      : "border-danger/30 bg-danger/10 text-danger"
                  )}
                >
                  {testResult.ok ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                  {testResult.ok
                    ? `Sent to ${testResult.recipient} · id ${testResult.provider_message_id}`
                    : `Failed: ${testResult.error || testResult.status}`}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Razorpay + LLM (read-only) */}
        <div className="grid gap-5 sm:grid-cols-2">
          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-warning" /> Razorpay
              </CardTitle>
              <StatusDot on={!!cfg?.razorpay?.connected} onLabel="Test Mode" offLabel="Simulated" />
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {cfg?.razorpay?.connected
                  ? "Live Razorpay Test keys — real test orders & payment links."
                  : "No keys — recovery actions are clearly-labelled simulations."}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <BrainCircuit className="h-4 w-4 text-accent" /> AI Decision Engine
              </CardTitle>
              <StatusDot on={!!cfg?.llm?.connected} onLabel={cfg?.llm?.provider || "LLM"} offLabel="Heuristic" />
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {cfg?.llm?.connected ? `${cfg.llm.provider} · ${cfg.llm.model}` : "Deterministic heuristic engine."}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Admin access */}
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <KeyRound className="h-4 w-4 text-muted-foreground" /> Admin Access
            </CardTitle>
            <StatusDot on={!!token} onLabel="Token Set" offLabel="Not Set" />
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Actions that destroy data or send real email require the{" "}
              <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">ADMIN_TOKEN</code>{" "}
              configured on the server. It is held for this browser session only and is never
              stored in the app bundle. Local development without a token set needs nothing here.
            </p>
            <div className="flex flex-col gap-2 sm:flex-row">
              <input
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                autoComplete="off"
                placeholder="Paste ADMIN_TOKEN"
                className="h-10 flex-1 rounded-xl border border-border bg-card px-3 font-mono text-sm outline-none focus:border-primary/40"
              />
              <button
                onClick={() => setAdminToken(token.trim())}
                className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-[13px] font-semibold transition-colors hover:bg-muted"
              >
                Save for session
              </button>
            </div>
          </CardContent>
        </Card>

        {err && <p className="text-sm text-danger">{err}</p>}
      </div>
    </>
  );
}

function StatusDot({ on, onLabel, offLabel }: { on: boolean; onLabel: string; offLabel: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.12em]",
        on ? "border-success/25 bg-success/10 text-success" : "border-border bg-muted/60 text-muted-foreground"
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", on ? "bg-success" : "bg-muted-foreground")} />
      {on ? onLabel : offLabel}
    </span>
  );
}

function Row({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div>
      <dt className="eyebrow">{label}</dt>
      <dd className="mt-0.5 truncate text-[13px] font-medium">{value || "—"}</dd>
    </div>
  );
}

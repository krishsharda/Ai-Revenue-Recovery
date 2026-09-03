import Link from "next/link";
import { ArrowRight, FlaskConical } from "lucide-react";
import MetroHero from "@/components/ui/scroll-locked-video-hero";
import { BrandMark } from "@/components/brand/brand-mark";

export default function LandingPage() {
  return (
    <main className="relative bg-[#05070d]">
      {/* Brand bar — always clickable over the locked hero */}
      <header className="fixed inset-x-0 top-0 z-50 flex items-center justify-between px-5 py-4 sm:px-8 sm:py-6">
        <Link href="/" className="flex items-center gap-3">
          <BrandMark className="h-9 w-9" />
          <div className="leading-none">
            <p className="font-display text-[15px] font-semibold tracking-tight text-[#f2f4f8]">
              Revenue Recovery
            </p>
            <p className="mt-1 font-mono text-[9.5px] uppercase tracking-[0.28em] text-[#f2f4f8]/45">
              AI Revenue Platform
            </p>
          </div>
        </Link>

        <div className="flex items-center gap-2 sm:gap-3">
          <span className="hidden items-center gap-2 rounded-full border border-white/12 bg-white/[0.03] px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.2em] text-[#f2f4f8]/60 backdrop-blur-md sm:inline-flex">
            <span className="h-1.5 w-1.5 rounded-full bg-warning animate-pulse-soft" />
            Razorpay Test Mode
          </span>
          <Link
            href="/simulation"
            className="hidden items-center gap-2 rounded-full border border-white/15 px-4 py-2 text-[13px] font-medium text-[#f2f4f8]/80 transition-colors hover:border-white/30 hover:text-[#f2f4f8] sm:inline-flex"
          >
            <FlaskConical className="h-3.5 w-3.5" /> Run simulation
          </Link>
          <Link
            href="/command-center"
            className="group inline-flex items-center gap-2 rounded-full bg-[#f2f4f8] px-5 py-2 text-[13px] font-semibold text-[#05070d] transition-colors hover:bg-white"
          >
            Open dashboard
            <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>
      </header>

      {/* Scroll-locked video hero, themed for revenue recovery.
          Self-hosted from /public so it loads reliably on every refresh. */}
      <MetroHero
        videoSrc="/hero.mp4"
        title="MAKE EVERY FAILED PAYMENT COUNT"
        tagline="Spot the signal, choose the right next move, and turn lost revenue into a second chance."
        scrollHint="SCROLL"
        signature={false}
      />

      {/* Bottom meta */}
      <div className="pointer-events-none fixed inset-x-0 bottom-5 z-40 hidden items-center justify-between px-8 sm:flex">
        <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-[#f2f4f8]/40">
          Detect · Diagnose · Decide · Recover
        </p>
        <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-[#f2f4f8]/40">
          AI decides · Rules control · System executes
        </p>
      </div>
    </main>
  );
}

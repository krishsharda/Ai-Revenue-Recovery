import { Sidebar } from "@/components/layout/sidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-aurora relative flex min-h-screen">
      <div className="grain-overlay" aria-hidden />
      <Sidebar />
      <main className="relative z-10 flex min-w-0 flex-1 flex-col">{children}</main>
    </div>
  );
}

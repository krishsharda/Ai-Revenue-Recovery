import { cn } from "@/lib/utils";

const GRADIENTS = [
  "from-indigo-500 to-sky-400",
  "from-emerald-500 to-teal-400",
  "from-fuchsia-500 to-pink-400",
  "from-amber-500 to-orange-400",
  "from-cyan-500 to-blue-400",
  "from-violet-500 to-indigo-400",
  "from-rose-500 to-red-400",
];

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function hash(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

export function Avatar({ name, size = "md", className }: { name: string; size?: "sm" | "md" | "lg"; className?: string }) {
  const g = GRADIENTS[hash(name) % GRADIENTS.length];
  const sizeCls = { sm: "h-8 w-8 text-[11px]", md: "h-10 w-10 text-xs", lg: "h-14 w-14 text-base" }[size];
  return (
    <div
      className={cn(
        "grid shrink-0 place-items-center rounded-full bg-gradient-to-br font-bold text-white ring-2 ring-background",
        g,
        sizeCls,
        className
      )}
    >
      {initials(name)}
    </div>
  );
}

import * as React from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "accent" | "success" | "danger";
type Size = "sm" | "md" | "lg";

const variants: Record<Variant, string> = {
  // Ivory fill, ink text — the editorial signature action.
  primary: "bg-primary text-primary-foreground hover:brightness-95 active:brightness-90",
  // Clean outline on white.
  secondary:
    "border border-border bg-card text-foreground hover:bg-muted",
  ghost: "bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted",
  accent: "bg-accent text-accent-foreground hover:brightness-105",
  success: "bg-success text-white hover:brightness-105",
  danger: "bg-danger text-white hover:brightness-105",
};

const sizes: Record<Size, string> = {
  sm: "h-8 px-3 text-[12px]",
  md: "h-10 px-4 text-[13px]",
  lg: "h-11 px-6 text-sm",
};

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex select-none items-center justify-center gap-2 rounded-[10px] font-medium tracking-tight transition-all duration-150",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        "disabled:pointer-events-none disabled:opacity-50",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  )
);
Button.displayName = "Button";

import { type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const badgeVariants = {
  default: "bg-brand-500/10 text-brand-400 border-brand-500/20",
  secondary: "bg-[hsl(var(--secondary))] text-[hsl(var(--secondary-foreground))] border-[hsl(var(--border))]",
  destructive: "bg-red-500/15 text-red-400 border-red-500/20",
  outline: "border border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))] bg-transparent",
  success: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
} as const;

export interface BadgeProps extends HTMLAttributes<HTMLDivElement> {
  variant?: keyof typeof badgeVariants;
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-all duration-200",
        badgeVariants[variant],
        className
      )}
      {...props}
    />
  );
}

export { Badge };

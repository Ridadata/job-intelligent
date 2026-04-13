import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const variants = {
  default: "bg-brand-500 text-slate-950 hover:bg-brand-400 shadow-sm shadow-brand-500/20 hover:shadow-brand-500/30",
  destructive: "bg-red-500 text-white hover:bg-red-600 shadow-sm",
  outline: "border border-[hsl(var(--border))] bg-transparent hover:bg-[hsl(var(--accent)/0.1)] hover:border-brand-500/50 text-[hsl(var(--foreground))]",
  secondary: "bg-[hsl(var(--secondary))] text-[hsl(var(--secondary-foreground))] hover:bg-[hsl(var(--secondary)/0.8)]",
  ghost: "hover:bg-[hsl(var(--surface-2))] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]",
  link: "text-brand-500 underline-offset-4 hover:underline",
  gradient: "bg-gradient-to-r from-brand-500 to-blue-500 text-white shadow-lg shadow-brand-500/25 hover:shadow-brand-500/40 hover:brightness-110",
} as const;

const sizes = {
  default: "h-10 px-5 py-2",
  sm: "h-8 rounded-lg px-3 text-xs",
  lg: "h-12 rounded-xl px-8 text-base",
  icon: "h-10 w-10",
} as const;

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    return (
      <button
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[hsl(var(--background))] disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]",
          variants[variant],
          sizes[size],
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };

import { cn } from "@/lib/utils";

interface MatchScoreProps {
  score: number;
  className?: string;
}

export function MatchScore({ score, className }: MatchScoreProps) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 80
      ? "text-emerald-400 border-emerald-500/20 bg-emerald-500/10"
      : pct >= 60
        ? "text-amber-400 border-amber-500/20 bg-amber-500/10"
        : "text-red-400 border-red-500/20 bg-red-500/10";

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-bold tabular-nums",
        color,
        className
      )}
    >
      {pct}% match
    </span>
  );
}

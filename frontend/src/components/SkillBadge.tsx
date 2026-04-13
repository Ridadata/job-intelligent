import { cn } from "@/lib/utils";

interface SkillBadgeProps {
  skill: string;
  matched?: boolean;
}

export function SkillBadge({ skill, matched }: SkillBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-lg px-2.5 py-1 text-xs font-medium transition-colors",
        matched
          ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20"
          : "bg-brand-500/10 text-brand-400 border border-brand-500/20"
      )}
    >
      {skill}
    </span>
  );
}

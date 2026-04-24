import { Link } from "react-router-dom";
import { MapPin, Building2, Calendar, Bookmark, BookmarkCheck } from "lucide-react";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/Badge";
import { SkillBadge } from "@/components/SkillBadge";
import { ROUTES } from "@/config/routes";
import { MAX_SKILLS_DISPLAY } from "@/config/constants";
import type { Job } from "@/types";
import { formatDistanceToNow } from "date-fns";

interface JobCardProps {
  job: Job;
  onSave?: (id: string) => void;
  onUnsave?: (id: string) => void;
  isSaved?: boolean;
  matchedSkills?: string[];
  matchScore?: number;
}

export function JobCard({ job, onSave, onUnsave, isSaved = false, matchedSkills, matchScore }: JobCardProps) {
  const visibleSkills = job.required_skills.slice(0, MAX_SKILLS_DISPLAY);
  const extraCount = job.required_skills.length - MAX_SKILLS_DISPLAY;

  return (
    <motion.div
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
      className="group relative rounded-2xl bg-white dark:bg-[hsl(var(--surface-1))] border border-gray-100 dark:border-white/[0.06] shadow-sm p-5 transition-all duration-300 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          {/* Company avatar + title */}
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-500/10 text-sm font-bold text-brand-500">
              {job.company?.charAt(0)?.toUpperCase() ?? "J"}
            </div>
            <div className="min-w-0">
              <Link
                to={ROUTES.JOB_DETAIL(job.id)}
                className="text-base font-semibold hover:text-brand-400 transition-colors line-clamp-1"
              >
                {job.title}
              </Link>
              <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-[hsl(var(--muted-foreground))]">
                {job.company && (
                  <span className="flex items-center gap-1">
                    <Building2 className="h-3.5 w-3.5" />
                    {job.company}
                  </span>
                )}
                {job.location && (
                  <span className="flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5" />
                    {job.location}
                  </span>
                )}
                {job.published_at && (
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    {formatDistanceToNow(new Date(job.published_at), { addSuffix: true })}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {matchScore != null && (
            <span className="rounded-full bg-brand-500/10 border border-brand-500/20 px-2.5 py-0.5 text-xs font-bold text-brand-400 tabular-nums">
              {Math.round(matchScore * 100)}%
            </span>
          )}
          {(onSave || onUnsave) && (
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={() => (isSaved ? onUnsave?.(job.id) : onSave?.(job.id))}
              className={`flex h-9 w-9 items-center justify-center rounded-xl border transition-all duration-200 ${
                isSaved
                  ? "border-brand-500/30 bg-brand-500/10 text-brand-400"
                  : "border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))] hover:border-brand-500/30 hover:text-brand-400"
              }`}
              aria-label={isSaved ? "Unsave job" : "Save job"}
            >
              {isSaved ? <BookmarkCheck className="h-4 w-4" /> : <Bookmark className="h-4 w-4" />}
            </motion.button>
          )}
        </div>
      </div>

      {/* Skills pills */}
      <div className="mt-4 flex flex-wrap items-center gap-2">
        {job.contract_type && (
          <Badge variant="outline">{job.contract_type}</Badge>
        )}
        {visibleSkills.length > 0 &&
          visibleSkills.map((skill) => (
            <SkillBadge
              key={skill}
              skill={skill}
              matched={matchedSkills?.includes(skill)}
            />
          ))}
        {extraCount > 0 && (
          <Badge variant="secondary">+{extraCount}</Badge>
        )}
      </div>

      {job.salary_min != null && job.salary_max != null && (
        <p className="mt-3 text-sm font-medium text-[hsl(var(--muted-foreground))]">
          💰 {job.salary_min.toLocaleString()}–{job.salary_max.toLocaleString()} €
        </p>
      )}
    </motion.div>
  );
}

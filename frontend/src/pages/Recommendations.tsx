import { Link } from "react-router-dom";
import { Sparkles, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { SkillBadge } from "@/components/SkillBadge";
import { MatchScore } from "@/components/MatchScore";
import { EmptyState } from "@/components/EmptyState";
import { useRecommendations } from "@/hooks/useRecommendations";
import { useAuthStore } from "@/store/auth.store";
import { ROUTES } from "@/config/routes";
import type { Recommendation } from "@/types";

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.06, duration: 0.35 },
  }),
};

export default function Recommendations() {
  const user = useAuthStore((s) => s.user);

  const { data, isLoading, isError } = useRecommendations(
    user ? { candidate_id: user.id, top_n: 20 } : null
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500/10 text-brand-500">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Recommendations</h1>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            AI-powered job matches based on your profile
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32 w-full rounded-2xl" />
          ))}
        </div>
      ) : isError ? (
        <EmptyState title="Failed to load" description="Please try again later." />
      ) : data?.data && data.data.length > 0 ? (
        <>
          {data.meta?.cached && (
            <p className="text-xs text-[hsl(var(--muted-foreground))]">
              ✦ Results cached · computed in {data.latency_ms}ms
            </p>
          )}
          <div className="space-y-3">
            {data.data.map((rec, idx) => (
              <motion.div key={rec.job_id} custom={idx} initial="hidden" animate="visible" variants={fadeUp}>
                <RecommendationCard rec={rec} />
              </motion.div>
            ))}
          </div>
        </>
      ) : (
        <EmptyState
          icon={<Sparkles className="h-10 w-10" />}
          title="No recommendations yet"
          description="Complete your profile and add skills to receive personalized AI matches"
          action={<Link to={ROUTES.PROFILE}><Button variant="gradient">Go to profile</Button></Link>}
        />
      )}
    </motion.div>
  );
}

function RecommendationCard({ rec }: { rec: Recommendation }) {
  const breakdown = rec.score_breakdown;

  return (
    <motion.div
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
      className="group relative rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 transition-all duration-300 hover:border-brand-500/30 hover:shadow-card-hover"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2.5">
            <Link
              to={ROUTES.JOB_DETAIL(rec.job_id)}
              className="text-base font-semibold hover:text-brand-400 transition-colors line-clamp-1"
            >
              {rec.title}
            </Link>
            <MatchScore score={rec.similarity_score} />
          </div>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            {rec.company} · {rec.location}
            {rec.contract_type && <> · {rec.contract_type}</>}
          </p>
        </div>
        <Link to={ROUTES.JOB_DETAIL(rec.job_id)}>
          <button className="flex h-9 w-9 items-center justify-center rounded-xl border border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))] transition-all duration-200 hover:border-brand-500/30 hover:text-brand-400">
            <ArrowRight className="h-4 w-4" />
          </button>
        </Link>
      </div>

      {/* Explanation text */}
      {rec.explanation_text && (
        <p className="mt-3 text-xs text-[hsl(var(--muted-foreground))] italic">
          {rec.explanation_text}
        </p>
      )}

      {/* Score breakdown */}
      {breakdown && Object.keys(breakdown).length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {Object.entries(breakdown).map(([key, value]) => (
            <span
              key={key}
              className="inline-flex items-center gap-1 rounded-full bg-[hsl(var(--muted))]/10 px-2 py-0.5 text-[10px] font-medium text-[hsl(var(--muted-foreground))]"
            >
              {key.replace(/_/g, " ")}:
              <span className={value >= 0.7 ? "text-emerald-500" : value >= 0.4 ? "text-amber-500" : "text-red-400"}>
                {Math.round(value * 100)}%
              </span>
            </span>
          ))}
        </div>
      )}

      {/* Skills */}
      <div className="mt-3 space-y-2">
        {rec.matched_skills.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">Matched:</span>
            {rec.matched_skills.map((s) => (
              <SkillBadge key={s} skill={s} matched />
            ))}
          </div>
        )}
        {rec.missing_skills.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-medium text-[hsl(var(--muted-foreground))]">Missing:</span>
            {rec.missing_skills.map((s) => (
              <SkillBadge key={s} skill={s} />
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

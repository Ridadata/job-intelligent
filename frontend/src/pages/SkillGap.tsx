import { Link } from "react-router-dom";
import { TrendingUp, Target, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import { Skeleton } from "@/components/ui/Skeleton";
import { SkillBadge } from "@/components/SkillBadge";
import { EmptyState } from "@/components/EmptyState";
import { Button } from "@/components/ui/Button";
import { useSkillGap } from "@/hooks/useSkillGap";
import { useAuthStore } from "@/store/auth.store";
import { ROUTES } from "@/config/routes";

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.06, duration: 0.35 },
  }),
};

export default function SkillGap() {
  const user = useAuthStore((s) => s.user);
  const { data, isLoading, isError } = useSkillGap(user?.id ?? null);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">Skill Gap Analysis</h1>
        <p className="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
          Discover the most in-demand skills you should learn next
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 w-full rounded-2xl" />
          ))}
        </div>
      ) : isError ? (
        <EmptyState title="Failed to load" description="Please try again later." />
      ) : data && data.top_missing_skills.length > 0 ? (
        <div className="space-y-6">
          {/* Your skills */}
          <div className="rounded-2xl bg-white dark:bg-[hsl(var(--surface-1))] border border-gray-100 dark:border-white/[0.06] shadow-sm p-5">
            <h2 className="mb-3 text-sm font-semibold text-gray-500 dark:text-gray-400">
              Your Current Skills
            </h2>
            <div className="flex flex-wrap gap-1.5">
              {data.candidate_skills.map((s) => (
                <SkillBadge key={s} skill={s} matched />
              ))}
            </div>
          </div>

          {/* Missing skills ranked */}
          <div className="rounded-2xl bg-white dark:bg-[hsl(var(--surface-1))] border border-gray-100 dark:border-white/[0.06] shadow-sm p-5">
            <div className="mb-4 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-brand-500" />
              <h2 className="text-sm font-semibold">Top Skills to Learn</h2>
            </div>
            <div className="space-y-3">
              {data.top_missing_skills.map((skill, idx) => {
                const freq = data.skill_frequency[skill] || 0;
                const potential = data.improvement_potential[skill] || 0;
                const barWidth = Math.min(potential * 100, 100);

                return (
                  <motion.div
                    key={skill}
                    custom={idx}
                    initial="hidden"
                    animate="visible"
                    variants={fadeUp}
                    className="group"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-50 dark:bg-brand-500/10 text-xs font-bold text-brand-500">
                          {idx + 1}
                        </span>
                        <span className="text-sm font-medium capitalize">{skill}</span>
                      </div>
                      <span className="text-xs text-[hsl(var(--muted-foreground))]">
                        Required in {freq} job{freq !== 1 ? "s" : ""}
                      </span>
                    </div>
                    <div className="mt-1.5 ml-8 h-1.5 rounded-full bg-[hsl(var(--muted))]/20">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${barWidth}%` }}
                        transition={{ duration: 0.6, delay: idx * 0.05 }}
                        className="h-full rounded-full bg-brand-400"
                      />
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>

          {/* CTA */}
          <div className="flex items-center gap-3 rounded-2xl border border-brand-500/20 bg-brand-500/5 p-5">
            <div className="flex-1">
              <p className="text-sm font-semibold">Improve your match score</p>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">
                Adding these skills to your profile will unlock more recommendations.
              </p>
            </div>
            <Link to={ROUTES.PROFILE}>
              <Button variant="gradient" size="sm">
                Update Profile <ArrowRight className="ml-1 h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>

          {data.latency_ms && (
            <p className="text-xs text-[hsl(var(--muted-foreground))]">
              ✦ Analysis computed in {data.latency_ms}ms
            </p>
          )}
        </div>
      ) : (
        <EmptyState
          icon={<Target className="h-10 w-10" />}
          title="No skill gap data"
          description="Complete your profile and add skills to see your skill gap analysis."
          action={
            <Link to={ROUTES.PROFILE}>
              <Button variant="gradient">Go to profile</Button>
            </Link>
          }
        />
      )}
    </motion.div>
  );
}

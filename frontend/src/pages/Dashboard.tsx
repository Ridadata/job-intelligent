import { Link } from "react-router-dom";
import {
  Briefcase,
  BarChart3,
  Upload,
  Search,
  Target,
  ChevronUp,
  ChevronDown,
  Plus,
} from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { JobCard } from "@/components/JobCard";
import { EmptyState } from "@/components/EmptyState";
import { useAuthStore } from "@/store/auth.store";
import { useJobs } from "@/hooks/useJobs";
import { useRecommendations } from "@/hooks/useRecommendations";
import { useSavedJobs } from "@/hooks/useSavedJobs";
import { ROUTES } from "@/config/routes";

/* ── Subtle fade-in ─────────────────────────────────────── */
const fadeIn = {
  hidden: { opacity: 0, y: 8 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.06, duration: 0.35, ease: "easeOut" as const },
  }),
};

/* ── Shared card style (clean, no glass) ─────────────────── */
const cardBase =
  "rounded-2xl bg-white dark:bg-[hsl(var(--surface-1))] border border-gray-100 dark:border-white/[0.06] shadow-sm";

export default function Dashboard() {
  const user = useAuthStore((s) => s.user);
  const firstName = user?.email?.split("@")[0] ?? "there";

  const recentJobs = useJobs({ page: 1, per_page: 6 });
  const recs = useRecommendations(
    user ? { candidate_id: user.id, top_n: 4 } : null
  );
  const savedJobs = useSavedJobs(1, 1);

  const topMatch = recs.data?.data?.[0];
  const totalJobs = recentJobs.data?.total ?? 0;
  const totalRecs = recs.data?.total ?? 0;
  const totalSaved = savedJobs.data?.total ?? 0;
  const matchScore = topMatch ? Math.round(topMatch.similarity_score * 100) : 0;

  return (
    <div className="space-y-7 pb-10">
      {/* ── Header ───────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
            Dashboard
          </h1>
          <p className="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
            Welcome back, {firstName}
          </p>
        </div>
        <Link to={ROUTES.JOBS}>
          <Button className="gap-2 rounded-xl bg-brand-500 px-5 py-2.5 text-sm font-semibold text-white shadow-none hover:bg-brand-600 transition-colors">
            <Plus className="h-4 w-4" />
            Explore Jobs
          </Button>
        </Link>
      </motion.div>

      {/* ── KPI Row ──────────────────────────────────────── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {([
          {
            label: "TOTAL JOBS",
            value: totalJobs ? totalJobs.toLocaleString() : "—",
            change: null,
            up: true,
          },
          {
            label: "RECOMMENDATIONS",
            value: totalRecs ? totalRecs.toString() : "0",
            change: totalRecs > 0 ? `+${totalRecs}` : null,
            up: true,
          },
          {
            label: "TOP MATCH",
            value: matchScore ? `${matchScore}%` : "—",
            change: matchScore >= 50 ? `+${matchScore - 40}%` : null,
            up: matchScore >= 50,
          },
          {
            label: "SAVED JOBS",
            value: totalSaved ? totalSaved.toString() : "0",
            change: null,
            up: true,
          },
        ] as const).map((kpi, i) => (
          <motion.div key={kpi.label} custom={i} initial="hidden" animate="visible" variants={fadeIn}>
            <div className={`${cardBase} p-5`}>
              <p className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500">
                {kpi.label}
              </p>
              <div className="mt-2 flex items-end gap-2">
                <span className="text-[1.75rem] font-bold leading-none tabular-nums text-gray-900 dark:text-white">
                  {kpi.value}
                </span>
                {kpi.change && (
                  <span className={`mb-0.5 flex items-center gap-0.5 text-xs font-semibold ${kpi.up ? "text-brand-500" : "text-red-400"}`}>
                    {kpi.up ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                    {kpi.change}
                  </span>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* ── Location Stats Strip ─────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25, duration: 0.35 }}
        className={`${cardBase} flex items-center divide-x divide-gray-100 dark:divide-white/[0.06] overflow-x-auto`}
      >
        {[
          { region: "France", count: 312, up: true },
          { region: "Morocco", count: 187, up: true },
          { region: "Remote", count: 245, up: true },
          { region: "Europe", count: 156, up: false },
          { region: "USA", count: 98, up: true },
          { region: "Africa", count: 64, up: false },
        ].map((loc) => (
          <div key={loc.region} className="flex-1 min-w-[100px] px-5 py-4 text-center">
            <p className="text-xs text-gray-400 dark:text-gray-500">{loc.region}</p>
            <div className="mt-1 flex items-center justify-center gap-1.5">
              <span className="text-lg font-bold tabular-nums text-gray-900 dark:text-white">{loc.count}</span>
              {loc.up ? (
                <ChevronUp className="h-3.5 w-3.5 text-brand-500" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5 text-red-400" />
              )}
            </div>
          </div>
        ))}
      </motion.div>

      {/* ── Two-Column: Recommendations + Skill Comparison ── */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Top Recommendations (like Team Members list) */}
        <motion.section
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35, duration: 0.35 }}
        >
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-base font-bold text-gray-900 dark:text-white">Top Recommendations</h2>
            <Link
              to={ROUTES.RECOMMENDATIONS}
              className="text-xs font-medium text-brand-500 hover:text-brand-600 transition-colors"
            >
              View All
            </Link>
          </div>

          <div className={`${cardBase} divide-y divide-gray-50 dark:divide-white/[0.04] overflow-hidden`}>
            {recs.isLoading ? (
              <div className="space-y-0">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="px-5 py-4">
                    <Skeleton className="h-5 w-3/4 rounded-lg" />
                    <Skeleton className="mt-2 h-3 w-1/2 rounded-lg" />
                  </div>
                ))}
              </div>
            ) : recs.data?.data && recs.data.data.length > 0 ? (
              recs.data.data.map((rec) => (
                <Link
                  key={rec.job_id}
                  to={ROUTES.JOB_DETAIL(rec.job_id)}
                  className="flex items-center gap-4 px-5 py-3.5 transition-colors hover:bg-gray-50 dark:hover:bg-white/[0.02]"
                >
                  {/* Icon avatar */}
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gray-100 dark:bg-white/[0.06]">
                    <Briefcase className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                  </div>
                  {/* Info */}
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {rec.title}
                    </p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 truncate">
                      {rec.company}{rec.location ? ` · ${rec.location}` : ""}
                    </p>
                  </div>
                  {/* Badge */}
                  <span className="shrink-0 rounded-full bg-brand-50 dark:bg-brand-500/10 px-3 py-1 text-xs font-semibold text-brand-600 dark:text-brand-400">
                    {Math.round(rec.similarity_score * 100)}% match
                  </span>
                </Link>
              ))
            ) : (
              <div className="px-5 py-8">
                <EmptyState
                  title="No recommendations yet"
                  description="Complete your profile to get matched"
                  action={
                    <Link to={ROUTES.PROFILE}>
                      <Button size="sm" className="rounded-lg bg-brand-500 text-white hover:bg-brand-600">
                        Complete Profile
                      </Button>
                    </Link>
                  }
                />
              </div>
            )}
          </div>
        </motion.section>

        {/* Skill Comparison (horizontal bars) */}
        <motion.section
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.35 }}
        >
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-base font-bold text-gray-900 dark:text-white">Skill Comparison</h2>
            <Link
              to={ROUTES.JOBS}
              className="text-xs font-medium text-brand-500 hover:text-brand-600 transition-colors"
            >
              View All
            </Link>
          </div>

          <div className={`${cardBase} p-5 space-y-5`}>
            {[
              { skill: "Python", pct: 85, color: "bg-brand-400" },
              { skill: "SQL", pct: 78, color: "bg-brand-400" },
              { skill: "Cloud (AWS/GCP)", pct: 65, color: "bg-brand-400" },
              { skill: "Spark / Big Data", pct: 52, color: "bg-brand-400" },
              { skill: "Machine Learning", pct: 44, color: "bg-brand-400" },
            ].map((item) => (
              <div key={item.skill} className="space-y-1.5">
                <div className="flex items-center gap-3">
                  <BarChart3 className="h-3.5 w-3.5 text-gray-400" />
                  <span className="flex-1 text-sm text-gray-700 dark:text-gray-300">{item.skill}</span>
                  <span className="text-sm font-semibold tabular-nums text-gray-900 dark:text-white">{item.pct}%</span>
                </div>
                <div className="ml-[26px] h-2 w-full rounded-full bg-gray-100 dark:bg-white/[0.06]">
                  <motion.div
                    className={`h-full rounded-full ${item.color}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${item.pct}%` }}
                    transition={{ duration: 0.7, delay: 0.5, ease: "easeOut" }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.section>
      </div>

      {/* ── Quick Actions Row ────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45, duration: 0.35 }}
        className="grid gap-4 sm:grid-cols-3"
      >
        {([
          { icon: Upload, label: "Upload CV", desc: "Let AI parse your skills", to: ROUTES.PROFILE, accent: "text-brand-600 bg-brand-50 dark:bg-brand-500/10" },
          { icon: Search, label: "Search Jobs", desc: "Browse all opportunities", to: ROUTES.JOBS, accent: "text-brand-500 bg-brand-100 dark:bg-brand-500/10" },
          { icon: Target, label: "Skill Gap", desc: "Find skills to learn next", to: ROUTES.SKILL_GAP, accent: "text-brand-700 bg-brand-50 dark:bg-brand-500/10" },
        ] as const).map((action) => (
          <Link key={action.label} to={action.to}>
            <div className={`${cardBase} group flex items-center gap-4 p-4 transition-all duration-150 hover:shadow-md cursor-pointer`}>
              <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${action.accent}`}>
                <action.icon className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-gray-900 dark:text-white">{action.label}</p>
                <p className="text-xs text-gray-400 dark:text-gray-500">{action.desc}</p>
              </div>
            </div>
          </Link>
        ))}
      </motion.div>

      {/* ── Recent Jobs ──────────────────────────────────── */}
      <motion.section
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.35 }}
      >
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-bold text-gray-900 dark:text-white">Recent Jobs</h2>
          <Link
            to={ROUTES.JOBS}
            className="text-xs font-medium text-brand-500 hover:text-brand-600 transition-colors"
          >
            Browse All
          </Link>
        </div>

        {recentJobs.isLoading ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-24 w-full rounded-2xl" />
            ))}
          </div>
        ) : recentJobs.data?.items && recentJobs.data.items.length > 0 ? (
          <div className="space-y-2.5">
            {recentJobs.data.items.map((job, idx) => (
              <motion.div
                key={job.id}
                custom={idx}
                initial="hidden"
                animate="visible"
                variants={fadeIn}
              >
                <JobCard job={job} />
              </motion.div>
            ))}
          </div>
        ) : (
          <div className={`${cardBase} p-8`}>
            <EmptyState
              title="No jobs yet"
              description="Jobs will appear here once the data pipeline runs"
            />
          </div>
        )}
      </motion.section>
    </div>
  );
}

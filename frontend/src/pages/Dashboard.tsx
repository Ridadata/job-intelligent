import { Link } from "react-router-dom";
import {
  Briefcase,
  Star,
  Bookmark,
  TrendingUp,
  ArrowRight,
  Brain,
  BarChart3,
  Sparkles,
  Upload,
  Search,
  Target,
  Zap,
} from "lucide-react";
import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { JobCard } from "@/components/JobCard";
import { EmptyState } from "@/components/EmptyState";
import { useAuthStore } from "@/store/auth.store";
import { useJobs } from "@/hooks/useJobs";
import { useRecommendations } from "@/hooks/useRecommendations";
import { useSavedJobs } from "@/hooks/useSavedJobs";
import { ROUTES } from "@/config/routes";

/* ── Animation variants ─────────────────────────────────── */
const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.07, duration: 0.45, ease: [0.25, 0.46, 0.45, 0.94] as [number, number, number, number] },
  }),
};

const stagger = {
  visible: { transition: { staggerChildren: 0.06 } },
};

/* ── Quick Action Card ───────────────────────────────────── */
function QuickAction({
  icon: Icon,
  label,
  description,
  to,
  gradient,
}: {
  icon: React.ElementType;
  label: string;
  description: string;
  to: string;
  gradient: string;
}) {
  return (
    <Link to={to} className="group block">
      <div className="glass-card flex items-center gap-4 p-4 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg cursor-pointer">
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-white"
          style={{ background: gradient }}
        >
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-[hsl(var(--foreground))]">{label}</p>
          <p className="text-xs text-[hsl(var(--muted-foreground))] truncate">{description}</p>
        </div>
        <ArrowRight className="h-4 w-4 text-[hsl(var(--muted-foreground))] opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
      </div>
    </Link>
  );
}

/* ── Main Dashboard ──────────────────────────────────────── */
export default function Dashboard() {
  const user = useAuthStore((s) => s.user);
  const firstName = user?.email?.split("@")[0] ?? "there";

  const recentJobs = useJobs({ page: 1, per_page: 5 });
  const recs = useRecommendations(
    user ? { candidate_id: user.id, top_n: 3 } : null
  );
  const savedJobs = useSavedJobs(1, 1);

  const topMatch = recs.data?.data?.[0];
  const matchedSkillCount = topMatch?.matched_skills?.length ?? 0;
  const totalJobs = recentJobs.data?.total ?? 0;
  const totalRecs = recs.data?.total ?? 0;
  const totalSaved = savedJobs.data?.total ?? 0;
  const matchScore = topMatch ? Math.round(topMatch.similarity_score * 100) : 0;

  return (
    <div className="space-y-8 pb-8">
      {/* ── Greeting Header ──────────────────────────────── */}
      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="flex flex-col gap-6 pt-2 sm:flex-row sm:items-end sm:justify-between"
      >
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-brand-500/20 bg-brand-500/5 px-3 py-1">
            <Sparkles className="h-3.5 w-3.5 text-brand-500" />
            <span className="text-xs font-medium text-brand-600 dark:text-brand-400">AI-Powered Platform</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-[hsl(var(--foreground))] sm:text-3xl">
            Welcome back, <span className="text-brand-500">{firstName}</span>
          </h1>
          <p className="mt-1.5 text-sm leading-relaxed text-[hsl(var(--muted-foreground))] max-w-lg">
            Your career intelligence dashboard — track opportunities, review matches, and discover your next role.
          </p>
        </div>
        <div className="flex gap-2.5 shrink-0">
          <Link to={ROUTES.JOBS}>
            <Button variant="gradient" className="gap-2">
              <Search className="h-4 w-4" />
              Explore Jobs
            </Button>
          </Link>
          <Link to={ROUTES.RECOMMENDATIONS}>
            <Button variant="outline" className="gap-2">
              View Matches
            </Button>
          </Link>
        </div>
      </motion.section>

      {/* ── KPI Cards ────────────────────────────────────── */}
      <motion.div
        className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
        initial="hidden"
        animate="visible"
        variants={stagger}
      >
        {([
          {
            icon: Briefcase,
            label: "Total Jobs",
            value: totalJobs ? totalJobs.toLocaleString() : "—",
            change: "Live from pipeline",
            gradient: "linear-gradient(135deg, #06B6D4, #0891B2)",
          },
          {
            icon: Star,
            label: "Recommendations",
            value: totalRecs ? totalRecs.toString() : "0",
            change: "AI-matched for you",
            gradient: "linear-gradient(135deg, #8B5CF6, #7C3AED)",
          },
          {
            icon: TrendingUp,
            label: "Top Match",
            value: matchScore ? `${matchScore}%` : "—",
            change: matchScore >= 80 ? "Excellent fit" : matchScore >= 50 ? "Good potential" : "Complete profile",
            gradient: "linear-gradient(135deg, #10B981, #059669)",
          },
          {
            icon: Bookmark,
            label: "Saved Jobs",
            value: totalSaved ? totalSaved.toString() : "0",
            change: "Bookmarked opportunities",
            gradient: "linear-gradient(135deg, #F59E0B, #D97706)",
          },
        ] as const).map((kpi, i) => (
          <motion.div key={kpi.label} custom={i} variants={fadeUp}>
            <div className="glass-card group relative overflow-hidden p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg">
              <div
                className="absolute inset-x-0 top-0 h-0.5 opacity-60"
                style={{ background: kpi.gradient }}
              />
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-[hsl(var(--muted-foreground))]">
                    {kpi.label}
                  </p>
                  <p className="mt-2 text-3xl font-bold tabular-nums tracking-tight text-[hsl(var(--foreground))]">
                    {kpi.value}
                  </p>
                  <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">{kpi.change}</p>
                </div>
                <div
                  className="flex h-11 w-11 items-center justify-center rounded-xl text-white"
                  style={{ background: kpi.gradient }}
                >
                  <kpi.icon className="h-5 w-5" />
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* ── AI Insights + Quick Actions Row ───────────────── */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* AI Insights — wider */}
        <motion.div
          className="lg:col-span-3"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.45 }}
        >
          <div className="glass-card gradient-border h-full overflow-hidden p-6">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-blue-600 text-white shadow-glow">
                <Brain className="h-6 w-6" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-base font-bold text-[hsl(var(--foreground))]">AI Insights</h3>
                  <span className="rounded-full bg-brand-500/10 border border-brand-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-brand-600 dark:text-brand-400">
                    Live
                  </span>
                </div>
                {topMatch ? (
                  <div className="space-y-3">
                    <p className="text-sm leading-relaxed text-[hsl(var(--muted-foreground))]">
                      Your profile matches{" "}
                      <span className="font-semibold text-brand-500">{Math.round(topMatch.similarity_score * 100)}%</span>{" "}
                      with top data roles.
                      {matchedSkillCount > 0 && (
                        <>{" "}You have <span className="font-semibold text-emerald-500">{matchedSkillCount} matching skills</span>.</>
                      )}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <Link to={ROUTES.RECOMMENDATIONS}>
                        <Button variant="gradient" size="sm" className="gap-1.5 text-xs">
                          View Recommendations <ArrowRight className="h-3 w-3" />
                        </Button>
                      </Link>
                      <Link to={ROUTES.SKILL_GAP}>
                        <Button variant="outline" size="sm" className="gap-1.5 text-xs">
                          <Target className="h-3 w-3" /> Skill Gap Analysis
                        </Button>
                      </Link>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <p className="text-sm leading-relaxed text-[hsl(var(--muted-foreground))]">
                      Complete your profile to unlock AI-powered career insights, job matching, and personalized recommendations.
                    </p>
                    <Link to={ROUTES.PROFILE}>
                      <Button variant="gradient" size="sm" className="gap-1.5 text-xs">
                        Complete Profile <ArrowRight className="h-3 w-3" />
                      </Button>
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Quick Actions — narrower */}
        <motion.div
          className="lg:col-span-2 space-y-3"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.45 }}
        >
          <h3 className="text-sm font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">
            Quick Actions
          </h3>
          <QuickAction
            icon={Upload}
            label="Upload CV"
            description="Let AI parse your skills"
            to={ROUTES.PROFILE}
            gradient="linear-gradient(135deg, #8B5CF6, #7C3AED)"
          />
          <QuickAction
            icon={Search}
            label="Search Jobs"
            description="Browse all opportunities"
            to={ROUTES.JOBS}
            gradient="linear-gradient(135deg, #06B6D4, #0891B2)"
          />
          <QuickAction
            icon={Target}
            label="Skill Gap"
            description="Find skills to learn next"
            to={ROUTES.SKILL_GAP}
            gradient="linear-gradient(135deg, #10B981, #059669)"
          />
        </motion.div>
      </div>

      {/* ── Two-Column: Recommendations + Market ─────────── */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Top Recommendations */}
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.45 }}
        >
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-bold text-[hsl(var(--foreground))]">Top Recommendations</h2>
            <Link to={ROUTES.RECOMMENDATIONS}>
              <Button variant="ghost" size="sm" className="gap-1.5 text-xs">
                View all <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>

          {recs.isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-[72px] w-full rounded-2xl" />
              ))}
            </div>
          ) : recs.data?.data && recs.data.data.length > 0 ? (
            <div className="space-y-3">
              {recs.data.data.map((rec, idx) => (
                <motion.div
                  key={rec.job_id}
                  custom={idx}
                  initial="hidden"
                  animate="visible"
                  variants={fadeUp}
                >
                  <Card className="group transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md">
                    <CardContent className="flex items-center justify-between p-4">
                      <div className="min-w-0 flex-1">
                        <Link
                          to={ROUTES.JOB_DETAIL(rec.job_id)}
                          className="text-sm font-semibold text-[hsl(var(--foreground))] hover:text-brand-500 transition-colors line-clamp-1"
                        >
                          {rec.title}
                        </Link>
                        <p className="mt-0.5 text-xs text-[hsl(var(--muted-foreground))]">
                          {rec.company} · {rec.location}
                        </p>
                      </div>
                      <div className="flex items-center gap-2.5">
                        <span className="inline-flex items-center rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 text-xs font-bold tabular-nums text-emerald-600 dark:text-emerald-400">
                          {Math.round(rec.similarity_score * 100)}%
                        </span>
                        <ArrowRight className="h-4 w-4 text-[hsl(var(--muted-foreground))] opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No recommendations yet"
              description="Complete your profile to get AI-powered job matches"
              action={
                <Link to={ROUTES.PROFILE}>
                  <Button variant="gradient" size="sm">Complete Profile</Button>
                </Link>
              }
            />
          )}
        </motion.section>

        {/* Market Overview */}
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55, duration: 0.45 }}
        >
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-bold text-[hsl(var(--foreground))]">Market Overview</h2>
            <Link to={ROUTES.JOBS}>
              <Button variant="ghost" size="sm" className="gap-1.5 text-xs">
                Explore <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>

          <Card className="overflow-hidden">
            <CardContent className="p-5">
              <div className="flex items-start gap-4 mb-5">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white">
                  <BarChart3 className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[hsl(var(--foreground))]">Data Job Market</h3>
                  <p className="mt-0.5 text-xs text-[hsl(var(--muted-foreground))]">
                    {totalJobs
                      ? `${totalJobs.toLocaleString()} jobs tracked across all sources`
                      : "Loading market data..."}
                  </p>
                </div>
              </div>

              {/* Trending skills with visual bars */}
              <div className="space-y-3">
                <p className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">
                  Trending Skills
                </p>
                {[
                  { skill: "Python", pct: 85, color: "bg-brand-500" },
                  { skill: "SQL", pct: 78, color: "bg-blue-500" },
                  { skill: "Spark", pct: 52, color: "bg-violet-500" },
                  { skill: "Cloud (AWS/GCP)", pct: 65, color: "bg-emerald-500" },
                ].map((item) => (
                  <div key={item.skill} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-[hsl(var(--foreground))]">{item.skill}</span>
                      <span className="text-xs tabular-nums text-[hsl(var(--muted-foreground))]">{item.pct}%</span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-[hsl(var(--surface-2))]">
                      <motion.div
                        className={`h-full rounded-full ${item.color}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${item.pct}%` }}
                        transition={{ duration: 0.8, delay: 0.6, ease: "easeOut" }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Platform stats row */}
              <div className="mt-5 grid grid-cols-3 gap-3 border-t border-[hsl(var(--border))] pt-4">
                {[
                  { label: "Sources", value: "6+", icon: Zap },
                  { label: "Updated", value: "6h", icon: TrendingUp },
                  { label: "Match Rate", value: "94%", icon: Sparkles },
                ].map((stat) => (
                  <div key={stat.label} className="text-center">
                    <stat.icon className="mx-auto mb-1 h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
                    <p className="text-sm font-bold tabular-nums text-[hsl(var(--foreground))]">{stat.value}</p>
                    <p className="text-[10px] text-[hsl(var(--muted-foreground))]">{stat.label}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.section>
      </div>

      {/* ── Recent Jobs ──────────────────────────────────── */}
      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.45 }}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-[hsl(var(--foreground))]">Recent Jobs</h2>
          <Link to={ROUTES.JOBS}>
            <Button variant="ghost" size="sm" className="gap-1.5 text-xs">
              Browse all <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>

        {recentJobs.isLoading ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-28 w-full rounded-2xl" />
            ))}
          </div>
        ) : recentJobs.data?.items && recentJobs.data.items.length > 0 ? (
          <div className="space-y-3">
            {recentJobs.data.items.map((job, idx) => (
              <motion.div
                key={job.id}
                custom={idx}
                initial="hidden"
                animate="visible"
                variants={fadeUp}
              >
                <JobCard job={job} />
              </motion.div>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No jobs yet"
            description="Jobs will appear here once the data pipeline runs"
          />
        )}
      </motion.section>
    </div>
  );
}

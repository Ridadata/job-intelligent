import { Link } from "react-router-dom";
import { Briefcase, Star, Bookmark, TrendingUp, ArrowRight, Brain, BarChart3 } from "lucide-react";
import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { JobCard } from "@/components/JobCard";
import { EmptyState } from "@/components/EmptyState";
import { useAuthStore } from "@/store/auth.store";
import { useJobs } from "@/hooks/useJobs";
import { useRecommendations } from "@/hooks/useRecommendations";
import { useCountUp } from "@/hooks/useCountUp";
import { ROUTES } from "@/config/routes";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.4, ease: "easeOut" as const },
  }),
};

function AnimatedStat({ end, suffix, label, duration = 1200 }: { end: number; suffix: string; label: string; duration?: number }) {
  const value = useCountUp(end, duration);
  const display = suffix === "×" ? value.toFixed(1) : suffix === "k+" ? `${Math.round(value)}` : `${Math.round(value)}`;
  return (
    <div className="glass-card px-4 py-5 text-center">
      <p className="font-display font-extrabold" style={{ fontSize: "1.8rem", letterSpacing: "-0.04em", color: "var(--text-primary)" }}>
        {display}{suffix}
      </p>
      <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{label}</p>
    </div>
  );
}

export default function Dashboard() {
  const user = useAuthStore((s) => s.user);

  const recentJobs = useJobs({ page: 1, per_page: 5 });
  const recs = useRecommendations(
    user ? { candidate_id: user.id, top_n: 3 } : null
  );

  const topMatch = recs.data?.data?.[0];
  const matchedSkillCount = topMatch?.explanation?.matched_skills?.length ?? 0;

  return (
    <div className="space-y-8">
      {/* Hero section */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center"
        style={{ padding: "3rem 1.5rem 2rem" }}
      >
        {/* Animated badge */}
        <div className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full px-3.5 py-1.5"
          style={{
            background: "rgba(6,182,212,0.08)",
            border: "1px solid rgba(6,182,212,0.25)",
          }}
        >
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full rounded-full opacity-75 animate-pulse-dot" style={{ background: "var(--accent-cyan)" }} />
            <span className="relative inline-flex h-2 w-2 rounded-full" style={{ background: "var(--accent-cyan)" }} />
          </span>
          <span className="text-xs font-medium" style={{ color: "var(--accent-cyan)", fontSize: "0.8rem" }}>AI-Powered Recruitment Platform</span>
        </div>

        {/* Headline */}
        <h1 className="font-display font-extrabold mx-auto overflow-visible pb-2" style={{
          fontSize: "clamp(2.2rem, 5vw, 3.5rem)",
          letterSpacing: "-0.04em",
          lineHeight: 1.3,
          color: "var(--text-primary)",
        }}>
          Match Data Talent with<br />
          <span className="text-gradient inline-block">Precision Intelligence</span>
        </h1>

        {/* Subtitle */}
        <p className="mx-auto mt-5 font-medium tracking-wide" style={{
          fontSize: "1.05rem",
          color: "var(--text-muted)",
          maxWidth: 560,
          lineHeight: 1.65,
        }}>
          {user?.email
            ? `Welcome back, ${user.email.split("@")[0]}. Your personalized AI job intelligence is ready — tracking recommendations, opportunities, and career insights.`
            : "Job Intelligent centralizes data-related job opportunities and matches them to your profile using AI — with match scores, skill graphs, and predictive insights built in."
          }
        </p>

        {/* CTA buttons */}
        <div className="flex items-center justify-center gap-3 mt-7">
          <Link to={ROUTES.JOBS}>
            <button
              className="inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-white transition-all duration-200 hover:-translate-y-0.5"
              style={{
                background: "linear-gradient(135deg, #06B6D4, #0EA5E9)",
                boxShadow: "0 4px 16px rgba(6,182,212,0.35)",
              }}
            >
              Explore Jobs <ArrowRight className="h-4 w-4" />
            </button>
          </Link>
          <Link to={ROUTES.RECOMMENDATIONS}>
            <button
              className="inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold transition-all duration-200 hover:-translate-y-0.5"
              style={{
                background: "var(--btn-subtle-bg)",
                border: "1px solid var(--border-glow)",
                color: "var(--text-primary)",
              }}
            >
              View Matches
            </button>
          </Link>
        </div>

        {/* Stat strip — count-up animation */}
        <div className="mx-auto mt-10 grid max-w-xl grid-cols-3 gap-3">
          <AnimatedStat end={94} suffix="%" label="Match Accuracy" duration={1400} />
          <AnimatedStat end={2.8} suffix="×" label="Faster Hires" duration={1200} />
          <AnimatedStat end={10} suffix="k+" label="Data Jobs Listed" duration={1000} />
        </div>
      </motion.section>

      {/* KPI row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { icon: <Briefcase className="h-5 w-5" />, label: "Total Jobs", value: recentJobs.data?.total ?? "—", color: "rgba(6,182,212,0.1)", textColor: "var(--accent-blue)" },
          { icon: <Star className="h-5 w-5" />, label: "Recommendations", value: recs.data?.total ?? "—", color: "rgba(14,165,233,0.1)", textColor: "var(--accent-violet)" },
          { icon: <TrendingUp className="h-5 w-5" />, label: "Top Match", value: topMatch ? `${Math.round(topMatch.similarity_score * 100)}%` : "—", color: "rgba(16,185,129,0.1)", textColor: "var(--accent-emerald)" },
          { icon: <Bookmark className="h-5 w-5" />, label: "Saved Jobs", value: "—", color: "rgba(245,158,11,0.1)", textColor: "var(--accent-amber)" },
        ].map((kpi, i) => (
          <motion.div
            key={kpi.label}
            custom={i}
            initial="hidden"
            animate="visible"
            variants={fadeUp}
          >
            <div
              className="glass-card group p-5 flex items-center gap-4 hover:-translate-y-1 transition-transform duration-200"
              style={{ boxShadow: "var(--shadow-card)" }}
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl" style={{ background: kpi.color, color: kpi.textColor }}>
                {kpi.icon}
              </div>
              <div>
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>{kpi.label}</p>
                <p className="text-2xl font-display font-extrabold tracking-tight" style={{ color: "var(--text-primary)" }}>{kpi.value}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* AI Insights widget */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35, duration: 0.4 }}
      >
        <div className="glass-card gradient-border overflow-hidden p-6" style={{ boxShadow: "var(--shadow-card)" }}>
          <div className="flex items-start gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl" style={{ background: "rgba(6,182,212,0.1)" }}>
              <Brain className="h-5 w-5" style={{ color: "var(--accent-blue)" }} />
            </div>
            <div>
              <h3 className="text-base font-display font-bold mb-1" style={{ color: "var(--text-primary)" }}>AI Insights</h3>
              {topMatch ? (
                <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
                  Your skills match <span className="font-medium" style={{ color: "var(--accent-blue)" }}>{Math.round(topMatch.similarity_score * 100)}%</span> of
                  top data jobs. {matchedSkillCount > 0 && (
                    <>You have <span className="font-medium" style={{ color: "var(--accent-emerald)" }}>{matchedSkillCount}</span> matching skills. </>
                  )}
                  <Link to={ROUTES.RECOMMENDATIONS} className="hover:underline" style={{ color: "var(--accent-blue)" }}>
                    View recommendations →
                  </Link>
                </p>
              ) : (
                <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
                  Complete your profile to unlock AI-powered insights about your skill alignment with the market.{" "}
                  <Link to={ROUTES.PROFILE} className="hover:underline" style={{ color: "var(--accent-blue)" }}>
                    Complete profile →
                  </Link>
                </p>
              )}
            </div>
          </div>
        </div>
      </motion.div>

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Top recommendations */}
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45, duration: 0.4 }}
        >
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-display font-bold" style={{ color: "var(--text-primary)" }}>Top Recommendations</h2>
            <Link to={ROUTES.RECOMMENDATIONS}>
              <Button variant="ghost" size="sm" className="gap-1.5">
                View all <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>

          {recs.isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-20 w-full rounded-2xl" />
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
                  <Card className="group">
                    <CardContent className="flex items-center justify-between p-4">
                      <div className="min-w-0 flex-1">
                        <Link to={ROUTES.JOB_DETAIL(rec.job_id)} className="font-medium hover:text-brand-400 transition-colors line-clamp-1">
                          {rec.title}
                        </Link>
                        <p className="text-sm text-[hsl(var(--muted-foreground))]">{rec.company} · {rec.location}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="rounded-full bg-emerald-500/15 border border-emerald-500/20 px-3 py-1 text-sm font-bold text-emerald-600 dark:text-emerald-400">
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
              description="Complete your profile to receive personalized AI-powered job matches"
              action={<Link to={ROUTES.PROFILE}><Button variant="gradient">Complete profile</Button></Link>}
            />
          )}
        </motion.section>

        {/* Market trends */}
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55, duration: 0.4 }}
        >
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-display font-bold" style={{ color: "var(--text-primary)" }}>Market Trends</h2>
            <Link to={ROUTES.JOBS}>
              <Button variant="ghost" size="sm" className="gap-1.5">
                Explore <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-start gap-4 mb-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-500/10">
                  <BarChart3 className="h-5 w-5 text-blue-400" />
                </div>
                <div>
                  <h3 className="text-base font-semibold mb-1">Data Job Market</h3>
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">
                    {recentJobs.data?.total
                      ? `${recentJobs.data.total} jobs currently tracked across all sources.`
                      : "Loading market data..."}
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {["Python", "SQL", "Spark", "Cloud"].map((skill) => (
                  <div key={skill} className="rounded-xl bg-[hsl(var(--surface-1))] p-3 text-center">
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">Trending</p>
                    <p className="text-sm font-semibold text-brand-400">{skill}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.section>
      </div>

      {/* Recent jobs */}
      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.4 }}
      >
        <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-display font-bold" style={{ color: "var(--text-primary)" }}>Recent Jobs</h2>
          <Link to={ROUTES.JOBS}>
            <Button variant="ghost" size="sm" className="gap-1.5">
              Browse all <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>

        {recentJobs.isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-24 w-full rounded-2xl" />
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
          <EmptyState title="No jobs yet" description="Jobs will appear here once the pipeline runs" />
        )}
      </motion.section>
    </div>
  );
}

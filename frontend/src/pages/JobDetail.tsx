import { useParams, Link } from "react-router-dom";
import { ArrowLeft, MapPin, Building2, Calendar, ExternalLink, Bookmark } from "lucide-react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { SkillBadge } from "@/components/SkillBadge";
import { EmptyState } from "@/components/EmptyState";
import { useJob, useSaveJob } from "@/hooks/useJobs";
import { ROUTES } from "@/config/routes";
import { formatDistanceToNow } from "date-fns";

export default function JobDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: job, isLoading, isError } = useJob(id ?? "");
  const saveJob = useSaveJob();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    );
  }

  if (isError || !job) {
    return (
      <EmptyState title="Job not found" description="This job may have been removed or the link is invalid." />
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6 max-w-4xl"
    >
      <Link
        to={ROUTES.JOBS}
        className="inline-flex items-center gap-1.5 text-sm text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors"
      >
        <ArrowLeft className="h-4 w-4" /> Back to search
      </Link>

      {/* Header card */}
      <div className="rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-6 lg:p-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-brand-500/10 text-xl font-bold text-brand-500">
              {job.company?.charAt(0)?.toUpperCase() ?? "J"}
            </div>
            <div>
              <h1 className="text-2xl font-bold">{job.title}</h1>
              <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-[hsl(var(--muted-foreground))]">
                {job.company && (
                  <span className="flex items-center gap-1.5"><Building2 className="h-4 w-4" />{job.company}</span>
                )}
                {job.location && (
                  <span className="flex items-center gap-1.5"><MapPin className="h-4 w-4" />{job.location}</span>
                )}
                {job.published_at && (
                  <span className="flex items-center gap-1.5">
                    <Calendar className="h-4 w-4" />
                    {formatDistanceToNow(new Date(job.published_at), { addSuffix: true })}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <Button variant="outline" onClick={() => saveJob.mutate(job.id)}>
              <Bookmark className="mr-2 h-4 w-4" /> Save
            </Button>
            {job.url && (
              <a href={job.url} target="_blank" rel="noopener noreferrer">
                <Button variant="gradient">
                  <ExternalLink className="mr-2 h-4 w-4" /> Apply
                </Button>
              </a>
            )}
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          {job.contract_type && <Badge variant="outline">{job.contract_type}</Badge>}
          {job.taxonomy_category && <Badge variant="secondary">{job.taxonomy_category}</Badge>}
          {job.salary_min != null && job.salary_max != null && (
            <Badge variant="default">
              {job.salary_min.toLocaleString()}–{job.salary_max.toLocaleString()} €
            </Badge>
          )}
        </div>
      </div>

      {job.required_skills.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Required Skills</CardTitle></CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {job.required_skills.map((skill) => (
              <SkillBadge key={skill} skill={skill} />
            ))}
          </CardContent>
        </Card>
      )}

      {job.description && (
        <Card>
          <CardHeader><CardTitle>Description</CardTitle></CardHeader>
          <CardContent>
            <div className="prose dark:prose-invert max-w-none whitespace-pre-wrap text-sm leading-relaxed text-[hsl(var(--muted-foreground))]">
              {job.description}
            </div>
          </CardContent>
        </Card>
      )}
    </motion.div>
  );
}

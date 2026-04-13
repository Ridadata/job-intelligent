import { useState } from "react";
import { Bookmark } from "lucide-react";
import { motion } from "framer-motion";
import { JobCard } from "@/components/JobCard";
import { Pagination } from "@/components/Pagination";
import { PageSkeleton } from "@/components/PageSkeleton";
import { EmptyState } from "@/components/EmptyState";
import { Button } from "@/components/ui/Button";
import { useSavedJobs } from "@/hooks/useSavedJobs";
import { useUnsaveJob } from "@/hooks/useJobs";
import { DEFAULT_PAGE_SIZE } from "@/config/constants";
import { ROUTES } from "@/config/routes";
import { Link } from "react-router-dom";

export default function SavedJobs() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError } = useSavedJobs(page, DEFAULT_PAGE_SIZE);
  const unsave = useUnsaveJob();

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400">
          <Bookmark className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Saved Jobs</h1>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            {data?.total ?? 0} jobs saved for later
          </p>
        </div>
      </div>

      {isLoading ? (
        <PageSkeleton />
      ) : isError ? (
        <EmptyState title="Failed to load saved jobs" description="Please try again later." />
      ) : data?.items && data.items.length > 0 ? (
        <>
          <div className="space-y-3">
            {data.items.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                isSaved
                onUnsave={(id) => unsave.mutate(id)}
              />
            ))}
          </div>
          <Pagination
            page={page}
            totalPages={data.pages}
            onPageChange={setPage}
            className="justify-center"
          />
        </>
      ) : (
        <EmptyState
          icon={<Bookmark className="h-10 w-10" />}
          title="No saved jobs"
          description="Browse jobs and save the ones that interest you"
          action={
            <Link to={ROUTES.JOBS}>
              <Button variant="gradient">Browse jobs</Button>
            </Link>
          }
        />
      )}
    </motion.div>
  );
}

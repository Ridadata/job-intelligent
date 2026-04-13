import { useState } from "react";
import { motion } from "framer-motion";
import { SearchBar } from "@/components/SearchBar";
import { FilterPanel } from "@/components/FilterPanel";
import { JobCard } from "@/components/JobCard";
import { Pagination } from "@/components/Pagination";
import { PageSkeleton } from "@/components/PageSkeleton";
import { EmptyState } from "@/components/EmptyState";
import { useJobs, useSaveJob, useUnsaveJob } from "@/hooks/useJobs";
import { useDebounce } from "@/hooks/useDebounce";
import { useFiltersStore } from "@/store/filters.store";
import { DEFAULT_PAGE_SIZE } from "@/config/constants";
import { Search, Briefcase } from "lucide-react";

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.06 } },
};
const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

export default function JobSearch() {
  const [page, setPage] = useState(1);
  const { query, location, contractType, skills, salaryMin, salaryMax, setFilter } =
    useFiltersStore();

  const debouncedQuery = useDebounce(query, 300);

  const { data, isLoading, isError } = useJobs({
    query: debouncedQuery || undefined,
    location: location || undefined,
    contract_type: contractType || undefined,
    skills: skills.length > 0 ? skills : undefined,
    salary_min: salaryMin ?? undefined,
    salary_max: salaryMax ?? undefined,
    page,
    per_page: DEFAULT_PAGE_SIZE,
  });

  const saveJob = useSaveJob();
  const unsaveJob = useUnsaveJob();

  if (isError) {
    return (
      <EmptyState
        icon={<Search className="h-10 w-10" />}
        title="Failed to load jobs"
        description="Please try again later."
      />
    );
  }

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
          <Briefcase className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Job Search</h1>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            Explore {data?.total ?? "—"} data-related opportunities
          </p>
        </div>
      </div>

      <SearchBar
        value={query}
        onChange={(v) => { setFilter("query", v); setPage(1); }}
        placeholder="Search by title, skill, or company..."
      />

      <FilterPanel />

      {isLoading ? (
        <PageSkeleton />
      ) : data?.items && data.items.length > 0 ? (
        <>
          <motion.div
            variants={stagger}
            initial="hidden"
            animate="visible"
            className="space-y-3"
          >
            {data.items.map((job) => (
              <motion.div key={job.id} variants={fadeUp}>
                <JobCard
                  job={job}
                  onSave={(id) => saveJob.mutate(id)}
                  onUnsave={(id) => unsaveJob.mutate(id)}
                />
              </motion.div>
            ))}
          </motion.div>
          <Pagination
            page={page}
            totalPages={data.pages}
            onPageChange={setPage}
            className="justify-center"
          />
        </>
      ) : (
        <EmptyState
          icon={<Search className="h-10 w-10" />}
          title="No jobs found"
          description="Try adjusting your search or filters"
        />
      )}
    </motion.div>
  );
}

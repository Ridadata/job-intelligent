import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { jobsService } from "@/services/jobs.service";
import { notify } from "@/lib/toast";
import type { JobFilters } from "@/types";

export function useJobs(filters: JobFilters) {
  return useQuery({
    queryKey: ["jobs", filters],
    queryFn: () => jobsService.searchJobs(filters),
  });
}

export function useJob(id: string) {
  return useQuery({
    queryKey: ["job", id],
    queryFn: () => jobsService.getJob(id),
    enabled: !!id,
  });
}

export function useSaveJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => jobsService.saveJob(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["saved-jobs"] });
      notify.success("Job saved", "Added to your saved jobs");
    },
    onError: (err: Error) => notify.error("Failed to save", err.message),
  });
}

export function useUnsaveJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => jobsService.unsaveJob(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["saved-jobs"] });
      notify.success("Job removed", "Removed from your saved jobs");
    },
    onError: (err: Error) => notify.error("Failed to remove", err.message),
  });
}

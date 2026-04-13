import { useQuery } from "@tanstack/react-query";
import { jobsService } from "@/services/jobs.service";

export function useSavedJobs(page = 1, perPage = 20) {
  return useQuery({
    queryKey: ["saved-jobs", page, perPage],
    queryFn: () => jobsService.getSavedJobs(page, perPage),
  });
}

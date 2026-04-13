import { apiClient } from "./api-client";
import { ENDPOINTS } from "@/config/api";
import type { Job, PaginatedResponse, JobFilters } from "@/types";

export const jobsService = {
  async searchJobs(filters: JobFilters = {}): Promise<PaginatedResponse<Job>> {
    const params: Record<string, string> = {};
    if (filters.query) params.q = filters.query;
    if (filters.location) params.location = filters.location;
    if (filters.contract_type) params.contract_type = filters.contract_type;
    if (filters.salary_min) params.salary_min = String(filters.salary_min);
    if (filters.salary_max) params.salary_max = String(filters.salary_max);
    if (filters.skills?.length) params.skills = filters.skills.join(",");
    params.page = String(filters.page || 1);
    params.per_page = String(filters.per_page || 20);
    return apiClient.get<PaginatedResponse<Job>>(ENDPOINTS.JOBS.LIST, params);
  },

  async getJob(id: string): Promise<Job> {
    return apiClient.get<Job>(ENDPOINTS.JOBS.DETAIL(id));
  },

  async saveJob(id: string): Promise<void> {
    return apiClient.post(ENDPOINTS.JOBS.SAVE(id));
  },

  async unsaveJob(id: string): Promise<void> {
    return apiClient.delete(ENDPOINTS.JOBS.SAVE(id));
  },

  async getSavedJobs(page = 1, perPage = 20): Promise<PaginatedResponse<Job>> {
    return apiClient.get<PaginatedResponse<Job>>(ENDPOINTS.CANDIDATES.SAVED_JOBS, {
      page: String(page),
      per_page: String(perPage),
    });
  },
};

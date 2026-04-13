export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "/api/v1";

export const ENDPOINTS = {
  AUTH: {
    LOGIN: "/auth/login",
    REGISTER: "/auth/register",
    ME: "/auth/me",
  },
  JOBS: {
    LIST: "/jobs",
    DETAIL: (id: string) => `/jobs/${id}`,
    SAVE: (id: string) => `/jobs/${id}/save`,
  },
  CANDIDATES: {
    PROFILE: "/candidates/profile",
    CV: "/candidates/cv",
    SAVED_JOBS: "/candidates/saved-jobs",
    SKILL_GAP: (id: string) => `/candidates/${id}/skill-gap`,
  },
  RECOMMENDATIONS: "/recommendations",
  SEARCH: "/search",
  ADMIN: {
    PIPELINE_RUNS: "/admin/pipeline-runs",
    USERS: "/admin/users",
    STATS: "/admin/stats",
  },
  HEALTH: "/health",
} as const;

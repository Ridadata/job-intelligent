export const ROUTES = {
  LOGIN: "/login",
  REGISTER: "/register",
  DASHBOARD: "/dashboard",
  JOBS: "/jobs",
  JOB_DETAIL: (id: string) => `/jobs/${id}`,
  RECOMMENDATIONS: "/recommendations",
  SKILL_GAP: "/skill-gap",
  PROFILE: "/profile",
  SAVED_JOBS: "/saved-jobs",
  ADMIN: "/admin",
  ADMIN_PIPELINE: "/admin/pipeline",
  ADMIN_USERS: "/admin/users",
} as const;

/** Job-related TypeScript types matching backend schemas. */

export interface Job {
  id: string;
  title: string;
  company: string | null;
  location: string | null;
  contract_type: string | null;
  salary_min: number | null;
  salary_max: number | null;
  required_skills: string[];
  description: string | null;
  published_at: string | null;
  taxonomy_category: string | null;
  url: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface UserProfile {
  id: string;
  email: string;
  role: "candidate" | "admin";
}

export interface CandidateProfile {
  id: string;
  user_id: string;
  name: string | null;
  title: string | null;
  skills: string[];
  experience_years: number | null;
  education_level: string | null;
  location: string | null;
  salary_expectation: number | null;
  preferred_contract_types: string[];
  profile_completeness: number;
  created_at: string;
  updated_at: string;
}

export interface Recommendation {
  job_id: string;
  title: string;
  company: string | null;
  location: string | null;
  contract_type: string | null;
  similarity_score: number;
  matched_skills: string[];
  missing_skills: string[];
  score_breakdown: Record<string, number>;
  explanation_text: string;
  tech_stack: string[];
}

export interface MatchExplanation {
  matched_skills: string[];
  missing_skills: string[];
  score_breakdown: Record<string, number>;
}

// Skill Gap types
export interface SkillGapResponse {
  candidate_skills: string[];
  top_missing_skills: string[];
  skill_frequency: Record<string, number>;
  improvement_potential: Record<string, number>;
  latency_ms: number;
}

// Semantic search types
export interface SemanticSearchResult {
  id: string;
  title: string;
  company: string | null;
  location: string | null;
  contract_type: string | null;
  similarity_score: number;
  tech_stack: string[];
}

export interface SemanticSearchResponse {
  items: SemanticSearchResult[];
  total: number;
  query: string;
  latency_ms: number;
}

// Auth types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// Recommendation request
export interface RecommendationRequest {
  candidate_id: string;
  top_n?: number;
  min_score?: number;
  filters?: {
    contract_type?: string;
    location?: string;
  };
}

export interface RecommendationResponse {
  data: Recommendation[];
  total: number;
  latency_ms: number;
  meta: {
    model: string;
    threshold: number;
    cached: boolean;
  };
}

// Admin types
export interface PipelineRun {
  id: string;
  stage: string;
  status: "running" | "success" | "failed";
  rows_in: number | null;
  rows_out: number | null;
  duration_ms: number | null;
  error_message: string | null;
  started_at: string;
  finished_at: string | null;
}

export interface SourceStats {
  source: string;
  total_offers: number;
  last_scraped_at: string | null;
}

// Job filters
export interface JobFilters {
  query?: string;
  location?: string;
  contract_type?: string;
  skills?: string[];
  salary_min?: number;
  salary_max?: number;
  page?: number;
  per_page?: number;
}

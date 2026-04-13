import { apiClient } from "./api-client";
import { ENDPOINTS } from "@/config/api";
import type { RecommendationRequest, RecommendationResponse, SkillGapResponse, SemanticSearchResponse } from "@/types";

export const recommendationsService = {
  async getRecommendations(request: RecommendationRequest): Promise<RecommendationResponse> {
    return apiClient.post<RecommendationResponse>(ENDPOINTS.RECOMMENDATIONS, request);
  },

  async getSkillGap(candidateId: string, topN: number = 10): Promise<SkillGapResponse> {
    return apiClient.get<SkillGapResponse>(
      ENDPOINTS.CANDIDATES.SKILL_GAP(candidateId),
      { top_n: String(topN) },
    );
  },

  async semanticSearch(
    query: string,
    options?: { top_n?: number; contract_type?: string; location?: string },
  ): Promise<SemanticSearchResponse> {
    const params: Record<string, string> = { q: query };
    if (options?.top_n) params.top_n = String(options.top_n);
    if (options?.contract_type) params.contract_type = options.contract_type;
    if (options?.location) params.location = options.location;
    return apiClient.get<SemanticSearchResponse>(ENDPOINTS.SEARCH, params);
  },
};

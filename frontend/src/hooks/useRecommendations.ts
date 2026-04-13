import { useQuery } from "@tanstack/react-query";
import { recommendationsService } from "@/services/recommendations.service";
import { RECOMMENDATION_STALE_TIME_MS } from "@/config/constants";
import type { RecommendationRequest } from "@/types";

export function useRecommendations(request: RecommendationRequest | null) {
  return useQuery({
    queryKey: ["recommendations", request?.candidate_id],
    queryFn: () => recommendationsService.getRecommendations(request!),
    enabled: !!request?.candidate_id,
    staleTime: RECOMMENDATION_STALE_TIME_MS,
  });
}

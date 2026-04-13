import { useQuery } from "@tanstack/react-query";
import { recommendationsService } from "@/services/recommendations.service";

export function useSemanticSearch(
  query: string,
  options?: { top_n?: number; contract_type?: string; location?: string },
) {
  return useQuery({
    queryKey: ["semantic-search", query, options],
    queryFn: () => recommendationsService.semanticSearch(query, options),
    enabled: query.length >= 2,
    staleTime: 2 * 60 * 1000,
  });
}

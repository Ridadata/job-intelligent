import { useQuery } from "@tanstack/react-query";
import { recommendationsService } from "@/services/recommendations.service";

export function useSkillGap(candidateId: string | null, topN: number = 10) {
  return useQuery({
    queryKey: ["skill-gap", candidateId, topN],
    queryFn: () => recommendationsService.getSkillGap(candidateId!, topN),
    enabled: !!candidateId,
    staleTime: 5 * 60 * 1000,
  });
}

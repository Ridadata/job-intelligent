import { QueryClient } from "@tanstack/react-query";
import { STALE_TIME_MS } from "@/config/constants";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: STALE_TIME_MS,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

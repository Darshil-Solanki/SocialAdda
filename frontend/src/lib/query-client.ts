import { QueryClient } from "@tanstack/react-query";

// Used by the browser (one per app) and by the server (one per request, so users never share cached data).
export function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false },
    },
  });
}

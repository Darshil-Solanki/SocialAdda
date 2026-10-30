import { cookies, headers } from "next/headers";
import type { QueryClient } from "@tanstack/react-query";

import { ACCESS_COOKIE, backendUrl } from "./session";

export class SessionRequired extends Error {}
export class NotFoundOnServer extends Error {}

// Access token for this render: the proxy passes a refreshed one in a header, otherwise the cookie is used.
async function serverAccess(): Promise<string | null> {
  const fromProxy = (await headers()).get("x-sa-access");
  if (fromProxy) return fromProxy;
  return (await cookies()).get(ACCESS_COOKIE)?.value ?? null;
}

// Trailing slash before the query string, as Django expects.
function withSlash(path: string): string {
  const [pathname, query] = path.split("?", 2);
  const slashed = pathname.endsWith("/") ? pathname : `${pathname}/`;
  return query === undefined ? slashed : `${slashed}?${query}`;
}

// GET against the backend from the server. Throws SessionRequired on 401 and NotFoundOnServer on 404.
export async function serverGet<T>(path: string, access?: string | null): Promise<T> {
  const token = access ?? (await serverAccess());
  if (!token) throw new SessionRequired("No session");
  const response = await fetch(`${backendUrl()}/api/v1${withSlash(path)}`, {
    headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
    cache: "no-store",
  });
  if (response.status === 401) throw new SessionRequired("Session expired");
  if (response.status === 404) throw new NotFoundOnServer(path);
  if (!response.ok) throw new Error(`Backend answered ${response.status} for ${path}`);
  return (await response.json()) as T;
}

// Mirrors useCursorList in lib/queries.ts, so the cached data matches what the client expects.
export async function prefetchCursor<T>(queryClient: QueryClient, queryKey: readonly unknown[], path: string) {
  await queryClient.prefetchInfiniteQuery({
    queryKey,
    queryFn: ({ pageParam }) => serverGet<{ next: string | null; previous: string | null; results: T[] }>(pageParam),
    initialPageParam: path,
    getNextPageParam: (last: { next: string | null }) => (last.next ? toApiPathFromAbsolute(last.next) : undefined),
    pages: 1,
  });
}

// Django's cursor links are absolute; keep only the part after /api/v1 (same rule as the client).
function toApiPathFromAbsolute(url: string): string {
  const parsed = new URL(url, "http://placeholder");
  return parsed.pathname.replace(/^\/api\/v1/, "") + parsed.search;
}

// Server-side session handling. Runs only in the Next.js server (route handlers, the proxy, server components).
// Tokens live in httpOnly cookies, so browser JavaScript never reads them.

export const REFRESH_COOKIE = "sa_refresh";
export const ACCESS_COOKIE = "sa_access";
const ACCESS_MAX_AGE_S = 5 * 60; // matches the access token lifetime in the backend (5 minutes)
const REFRESH_MAX_AGE_S = 7 * 24 * 60 * 60; // matches the refresh token lifetime in the backend

export type TokenPair = { access: string; refresh: string };

export function backendUrl(): string {
  return process.env.BACKEND_URL ?? "http://localhost:8000";
}

// Rotation blacklists the old refresh token in Django, so concurrent requests that carry the same old token
// must share one rotation. The result is also kept briefly, because the browser may still send the old cookie
// with requests that were already in flight.
const RECENT_TTL_MS = 30_000;
const recent = new Map<string, { at: number; pending: Promise<TokenPair | null> }>();

export function refreshTokens(refresh: string, fetchImpl: typeof fetch = fetch): Promise<TokenPair | null> {
  const now = Date.now();
  for (const [key, entry] of recent) {
    if (now - entry.at > RECENT_TTL_MS) recent.delete(key);
  }
  const existing = recent.get(refresh);
  if (existing) return existing.pending;

  // Network failures reject (the caller decides); a rejected token resolves to null (logged out).
  const pending = (async () => {
    const response = await fetchImpl(`${backendUrl()}/api/v1/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
      cache: "no-store",
    });
    if (!response.ok) return null;
    const data = (await response.json()) as { access: string; refresh?: string };
    return { access: data.access, refresh: data.refresh ?? refresh };
  })();
  recent.set(refresh, { at: now, pending });
  return pending;
}

// Drops the cached rotation for a token (used on logout).
export function forgetRefresh(refresh: string): void {
  recent.delete(refresh);
}

type CookieWriter = { set(name: string, value: string, options: CookieOptions): unknown };
type CookieOptions = {
  httpOnly: boolean;
  sameSite: "lax";
  secure: boolean;
  path: string;
  maxAge: number;
};

function options(maxAge: number): CookieOptions {
  return {
    httpOnly: true,
    sameSite: "lax",
    // Browsers accept Secure cookies on http://localhost, so this holds for local production builds too.
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge,
  };
}

export function setSessionCookies(writer: CookieWriter, tokens: TokenPair): void {
  writer.set(ACCESS_COOKIE, tokens.access, options(ACCESS_MAX_AGE_S));
  writer.set(REFRESH_COOKIE, tokens.refresh, options(REFRESH_MAX_AGE_S));
}

export function clearSessionCookies(writer: CookieWriter): void {
  writer.set(ACCESS_COOKIE, "", options(0));
  writer.set(REFRESH_COOKIE, "", options(0));
}

export type ResolvedSession = {
  access: string | null;
  // Set when the refresh token was used: the caller must store the new pair on its response.
  rotated: TokenPair | null;
  // True when there is no usable session at all (no cookies, or the refresh token was rejected).
  loggedOut: boolean;
  // True when a refresh cookie exists, whether or not it still works.
  hadRefresh: boolean;
};

// Returns the access token to use for a request, refreshing it when the access cookie is missing.
export async function resolveSession(read: (name: string) => string | undefined): Promise<ResolvedSession> {
  const access = read(ACCESS_COOKIE);
  if (access) return { access, rotated: null, loggedOut: false, hadRefresh: Boolean(read(REFRESH_COOKIE)) };

  const refresh = read(REFRESH_COOKIE);
  if (!refresh) return { access: null, rotated: null, loggedOut: true, hadRefresh: false };

  const pair = await refreshTokens(refresh);
  if (!pair) return { access: null, rotated: null, loggedOut: true, hadRefresh: true };
  return { access: pair.access, rotated: pair, loggedOut: false, hadRefresh: true };
}

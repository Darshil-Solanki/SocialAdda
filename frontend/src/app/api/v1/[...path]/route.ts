import { type NextRequest, NextResponse } from "next/server";

import { apiUrl, forwardedHeaders, jsonResponse, relay } from "@/lib/server/backend";
import { clearSessionCookies, resolveSession, setSessionCookies, type TokenPair } from "@/lib/server/session";
import { isSafePath } from "@/lib/server/paths";

// Session endpoints are handled by /api/session/* so that tokens never reach the browser through this proxy.
const SESSION_ONLY = new Set(["auth/token/", "auth/token/refresh/", "auth/register/", "auth/logout/"]);

// Each path segment must be a plain name (usernames, ids, endpoint names). Encoded slashes and dot segments could
// otherwise climb out of /api/v1 to other Django paths, such as /admin/ or the token endpoints.

async function handle(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (!isSafePath(path)) {
    return jsonResponse({ detail: "Not found." }, 404);
  }
  const subpath = path.join("/");
  const normalized = subpath.endsWith("/") ? subpath : `${subpath}/`;
  if (SESSION_ONLY.has(normalized)) return jsonResponse({ detail: "Not found." }, 404);

  const search = new URL(request.url).search;
  const body = request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer();

  const session = await resolveSession((name) => request.cookies.get(name)?.value);
  const send = (access: string | null) =>
    fetch(apiUrl(`${normalized}${search}`), {
      method: request.method,
      headers: forwardedHeaders(request, access),
      body,
      cache: "no-store",
      redirect: "manual",
    });

  let upstream = await send(session.access);
  let rotated: TokenPair | null = session.rotated;
  // The access token can expire a little before its cookie does; refresh once and retry.
  if (upstream.status === 401 && session.access && !session.rotated) {
    const refreshed = await resolveSession((name) => (name === "sa_access" ? undefined : request.cookies.get(name)?.value));
    if (refreshed.rotated) {
      rotated = refreshed.rotated;
      upstream = await send(refreshed.rotated.access);
    }
  }

  const response = await relay(upstream);
  const out = new NextResponse(response.body, { status: response.status, headers: response.headers });
  if (rotated) setSessionCookies(out.cookies, rotated);
  if (session.loggedOut && session.hadRefresh) clearSessionCookies(out.cookies);
  return out;
}

export const GET = handle;
export const POST = handle;
export const PATCH = handle;
export const PUT = handle;
export const DELETE = handle;

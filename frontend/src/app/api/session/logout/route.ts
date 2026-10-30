import { type NextRequest, NextResponse } from "next/server";

import { apiUrl, forwardedHeaders } from "@/lib/server/backend";
import { REFRESH_COOKIE, clearSessionCookies, forgetRefresh } from "@/lib/server/session";

// Revokes the refresh token in Django and clears the cookies, even when Django cannot be reached.
export async function POST(request: NextRequest) {
  const refresh = request.cookies.get(REFRESH_COOKIE)?.value;
  if (refresh) {
    forgetRefresh(refresh);
    try {
      // The browser's logout request has no body, so forwardedHeaders has no content type to copy. Without this
      // header the body goes out as text/plain and Django answers 415, leaving the refresh token valid.
      const headers = forwardedHeaders(request, null);
      headers.set("Content-Type", "application/json");
      await fetch(apiUrl("auth/logout/"), {
        method: "POST",
        headers,
        body: JSON.stringify({ refresh }),
        cache: "no-store",
      });
    } catch {
      // The refresh token still expires on its own; the cookies are cleared below either way.
    }
  }
  const response = new NextResponse(null, { status: 204 });
  clearSessionCookies(response.cookies);
  return response;
}

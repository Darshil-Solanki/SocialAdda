import { type NextRequest, NextResponse } from "next/server";

import { clearSessionCookies, resolveSession, setSessionCookies } from "@/lib/server/session";

// Gives the browser an access token for opening a WebSocket. The token is only held in memory by the page.
export async function GET(request: NextRequest) {
  const session = await resolveSession((name) => request.cookies.get(name)?.value);
  if (!session.access) {
    const response = NextResponse.json({ detail: "Sign in to continue." }, { status: 401 });
    if (session.loggedOut) clearSessionCookies(response.cookies);
    return response;
  }
  const response = NextResponse.json({ token: session.access });
  if (session.rotated) setSessionCookies(response.cookies, session.rotated);
  return response;
}

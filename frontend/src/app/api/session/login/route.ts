import { type NextRequest, NextResponse } from "next/server";

import { apiUrl, forwardedHeaders, relay } from "@/lib/server/backend";
import { setSessionCookies, type TokenPair } from "@/lib/server/session";

// Exchanges credentials for tokens, stores them in httpOnly cookies, and returns only the user.
export async function POST(request: NextRequest) {
  const credentials = await request.text();
  const tokenResponse = await fetch(apiUrl("auth/token/"), {
    method: "POST",
    headers: forwardedHeaders(request, null),
    body: credentials,
    cache: "no-store",
  });
  if (!tokenResponse.ok) return relay(tokenResponse);

  const tokens = (await tokenResponse.json()) as TokenPair;
  const meResponse = await fetch(apiUrl("me/"), {
    headers: forwardedHeaders(request, tokens.access),
    cache: "no-store",
  });
  if (!meResponse.ok) return relay(meResponse);

  const user = await meResponse.json();
  const response = NextResponse.json({ user });
  setSessionCookies(response.cookies, tokens);
  return response;
}

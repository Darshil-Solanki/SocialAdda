import { type NextRequest, NextResponse } from "next/server";

import { apiUrl, forwardedHeaders, relay } from "@/lib/server/backend";
import { setSessionCookies, type TokenPair } from "@/lib/server/session";

// Creates the account, stores the new tokens in httpOnly cookies, and returns only the user.
export async function POST(request: NextRequest) {
  const payload = await request.text();
  const upstream = await fetch(apiUrl("auth/register/"), {
    method: "POST",
    headers: forwardedHeaders(request, null),
    body: payload,
    cache: "no-store",
  });
  if (!upstream.ok) return relay(upstream);

  const data = (await upstream.json()) as TokenPair & { user: unknown };
  const response = NextResponse.json({ user: data.user }, { status: 201 });
  setSessionCookies(response.cookies, { access: data.access, refresh: data.refresh });
  return response;
}

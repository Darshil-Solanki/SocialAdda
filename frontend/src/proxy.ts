import { type NextRequest, NextResponse } from "next/server";

import { clearSessionCookies, resolveSession, setSessionCookies } from "@/lib/server/session";

// Every page render gets a fresh nonce, applied to scripts and styles that Next.js injects. In production no
// inline style attributes or unsafe-inline are allowed: the app avoids React's style prop. The dev server is the
// one exception: its error overlay and dev font <style> tags are injected by Next.js without a nonce, which is
// what the Next.js CSP guide says to allow in development only.
function contentSecurityPolicy(nonce: string): string {
  const isDev = process.env.NODE_ENV === "development";
  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDev ? " 'unsafe-eval'" : ""}`,
    isDev ? "style-src 'self' 'unsafe-inline'" : `style-src 'self' 'nonce-${nonce}'`,
    "img-src 'self' data: blob: http: https:",
    "font-src 'self' data:",
    "connect-src 'self' ws: wss: http: https:",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join("; ");
}

export async function proxy(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const csp = contentSecurityPolicy(nonce);

  const requestHeaders = new Headers(request.headers);
  // Internal headers must come only from this proxy, never from the browser.
  requestHeaders.delete("x-sa-access");
  requestHeaders.delete("x-nonce");
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", csp);

  let rotated = null;
  let loggedOut = false;
  let hadRefresh = false;
  try {
    const session = await resolveSession((name) => request.cookies.get(name)?.value);
    // Server components read this header to make their own API calls during this render.
    if (session.access) requestHeaders.set("x-sa-access", session.access);
    rotated = session.rotated;
    loggedOut = session.loggedOut;
    hadRefresh = session.hadRefresh;
  } catch {
    // Backend unreachable: render without a session. Pages that need data show their own error.
  }

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", csp);
  if (rotated) setSessionCookies(response.cookies, rotated);
  // A refresh cookie the backend no longer accepts is removed, so the browser stops retrying it.
  if (loggedOut && hadRefresh) clearSessionCookies(response.cookies);
  return response;
}

export const config = {
  // Everything except API routes, static files, optimized images, the favicon and uploaded media.
  matcher: ["/((?!api/|_next/static|_next/image|favicon.ico|media/).*)"],
};

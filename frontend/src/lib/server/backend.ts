import type { NextRequest } from "next/server";

import { backendUrl } from "./session";

// Headers that carry the caller's identity and format to Django. The client address is forwarded so that
// Django's per-client throttles see the real visitor, not the Next.js server.
export function forwardedHeaders(request: NextRequest, access: string | null): Headers {
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);
  headers.set("Accept", "application/json");
  // Put behind a proxy that sets X-Forwarded-For (or X-Real-IP); otherwise every visitor shares one address.
  const clientAddress = request.headers.get("x-forwarded-for") ?? request.headers.get("x-real-ip");
  if (clientAddress) headers.set("X-Forwarded-For", clientAddress);
  if (access) headers.set("Authorization", `Bearer ${access}`);
  return headers;
}

export function apiUrl(pathWithQuery: string): string {
  return `${backendUrl()}/api/v1/${pathWithQuery}`;
}

export function jsonResponse(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

// Copies a Django response, keeping its status and body.
export async function relay(upstream: Response): Promise<Response> {
  if (upstream.status === 204) return new Response(null, { status: 204 });
  const body = await upstream.arrayBuffer();
  const contentType = upstream.headers.get("content-type") ?? "application/json";
  return new Response(body, { status: upstream.status, headers: { "Content-Type": contentType } });
}

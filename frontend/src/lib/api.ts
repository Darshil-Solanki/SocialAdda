// Browser-side API client. Tokens are in httpOnly cookies that only the Next.js server reads, so this module
// never handles them. Requests go to same-origin routes: /api/v1/* (proxied to Django) and /api/session/*.

const API_BASE = "/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    public data: unknown,
  ) {
    super(errorMessage(data, status));
  }
}

function errorMessage(data: unknown, status: number): string {
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    if (typeof record.detail === "string") return record.detail;
    for (const value of Object.values(record)) {
      if (Array.isArray(value) && typeof value[0] === "string") return value[0];
      if (typeof value === "string") return value;
    }
  }
  if (status >= 500) return "The server ran into a problem. Please try again in a moment.";
  // A non-JSON body (for example an HTML error page) is never shown to the user as raw text.
  return `The request failed (${status}). Please try again.`;
}

// Used when the request never got an answer (offline, server down, DNS failure).
const UNREACHABLE = "Could not reach the server. Check your connection and try again.";

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
};

// Sends one request to a same-origin URL and returns the parsed JSON (or null for 204).
export async function request<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {};
  let body: BodyInit | undefined;
  if (options.body instanceof FormData) {
    body = options.body; // the browser sets the multipart boundary itself
  } else if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.body);
  }

  let response: Response;
  try {
    response = await fetch(url, { method: options.method ?? "GET", headers, body, credentials: "same-origin" });
  } catch {
    throw new ApiError(0, { detail: UNREACHABLE });
  }

  if (response.status === 204) return undefined as T;

  const text = await response.text();
  // Parse defensively: an error page from a proxy or a crashed server is HTML, not JSON.
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }
  if (!response.ok) throw new ApiError(response.status, data);
  if (data === null && text) throw new ApiError(response.status, null);
  return data as T;
}

// `path` is relative to /api/v1, for example "/posts/" or "/users/bob/".
export function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  return request<T>(`${API_BASE}${path}`, options);
}

// Signs in: the server stores the tokens in cookies and returns the user.
export async function loginSession(username: string, password: string): Promise<{ user: unknown }> {
  return request("/api/session/login/", { method: "POST", body: { username, password } });
}

export async function registerSession(input: Record<string, string>): Promise<{ user: unknown }> {
  return request("/api/session/register/", { method: "POST", body: input });
}

// Ends the session. Errors are ignored: the cookies are cleared by the server, and the page signs out either way.
export async function endSession(): Promise<void> {
  try {
    await request("/api/session/logout/", { method: "POST" });
  } catch {
    // Nothing else to do; the local UI state is cleared by the caller.
  }
}

// Short-lived access token for opening a WebSocket (the browser sends it in the URL, as the backend expects).
export async function socketToken(): Promise<string | null> {
  try {
    const data = await request<{ token: string }>("/api/session/socket/");
    return data.token;
  } catch {
    return null;
  }
}

// Cursor links from the API are absolute URLs; keep only the part after /api/v1.
export function toApiPath(url: string): string {
  const parsed = new URL(url, "http://placeholder");
  return parsed.pathname.replace(/^\/api\/v1/, "") + parsed.search;
}

// Message to show a user for any failed request.
export function describeError(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Something went wrong. Please try again.";
}

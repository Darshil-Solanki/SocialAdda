import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch, describeError, endSession, toApiPath } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiFetch", () => {
  it("calls the same-origin API route with the cookie credentials and no token in JavaScript", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch("/me/");

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/v1/me/");
    expect(init.credentials).toBe("same-origin");
    expect(init.headers.Authorization).toBeUndefined();
  });

  it("does not show a raw JSON parse error when the server returns an HTML error page", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<!DOCTYPE html><h1>Server Error</h1>", { status: 500 })));

    const message = await apiFetch("/posts/").catch((caught: unknown) => describeError(caught));

    expect(message).toBe("The server ran into a problem. Please try again in a moment.");
  });

  it("explains an unreachable server instead of the browser's network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    const message = await apiFetch("/posts/").catch((caught: unknown) => describeError(caught));

    expect(message).toBe("Could not reach the server. Check your connection and try again.");
  });

  it("uses the API's own message for a JSON error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Not found." }), { status: 404 })));

    const error = await apiFetch("/posts/9/").catch((caught: unknown) => caught);

    expect(error).toBeInstanceOf(ApiError);
    expect(describeError(error)).toBe("Not found.");
  });

  it("sends a FormData body without setting a JSON content type", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: 1 }), { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);
    const form = new FormData();
    form.append("content_text", "hi");

    await apiFetch("/posts/", { method: "POST", body: form });

    const [, init] = fetchMock.mock.calls[0];
    expect(init.body).toBe(form);
    expect(init.headers["Content-Type"]).toBeUndefined();
  });
});

describe("endSession", () => {
  it("asks the server to end the session and never throws", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));
    vi.stubGlobal("fetch", fetchMock);

    await expect(endSession()).resolves.toBeUndefined();
    expect(fetchMock.mock.calls[0][0]).toBe("/api/session/logout/");
  });
});

describe("toApiPath", () => {
  it("turns an absolute cursor link into a path relative to /api/v1", () => {
    expect(toApiPath("http://localhost:8000/api/v1/posts/?cursor=abc123")).toBe("/posts/?cursor=abc123");
  });
});
